#!/usr/bin/env python3

import os
import re
import time
import logging
import pyinotify
from datetime import datetime, timedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from collections import defaultdict
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/log_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
LOG_FILE = "/var/log/auth.log"
FAILED_LOGIN_THRESHOLD = int(os.getenv("FAILED_LOGIN_THRESHOLD", "3"))
TIME_WINDOW = int(os.getenv("TIME_WINDOW", "300"))  # 5 minutes in seconds
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "#ssh-monitoring")

logger.info(f"Starting with configuration:")
logger.info(f"FAILED_LOGIN_THRESHOLD: {FAILED_LOGIN_THRESHOLD}")
logger.info(f"TIME_WINDOW: {TIME_WINDOW}")
logger.info(f"SLACK_CHANNEL: {SLACK_CHANNEL}")
logger.info(f"SLACK_TOKEN configured: {'Yes' if SLACK_TOKEN else 'No'}")

# Initialize Slack client if token is available
if SLACK_TOKEN:
    try:
        slack_client = WebClient(token=SLACK_TOKEN)
        # Test the connection
        response = slack_client.auth_test()
        logger.info(f"Successfully connected to Slack as {response['user']}")
    except Exception as e:
        logger.error(f"Failed to initialize Slack client: {str(e)}")
        slack_client = None
else:
    logger.warning("No Slack token provided - notifications will be disabled")
    slack_client = None

# Track failed attempts
failed_attempts = defaultdict(list)
blocked_ips = set()

def send_slack_alert(message):
    """Send alert to Slack channel"""
    if not slack_client:
        logger.warning("Slack notifications disabled - no token provided")
        return
        
    try:
        logger.info(f"Attempting to send Slack message: {message}")
        response = slack_client.chat_postMessage(
            channel=SLACK_CHANNEL,
            text=message
        )
        if response['ok']:
            logger.info(f"Successfully sent Slack alert: {message}")
        else:
            logger.error(f"Failed to send Slack message: {response}")
    except SlackApiError as e:
        logger.error(f"Error sending Slack message: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error sending Slack message: {str(e)}")

def block_ip(ip):
    """Block IP using iptables"""
    if ip not in blocked_ips:
        try:
            logger.info(f"Attempting to block IP: {ip}")
            
            # Check if rule already exists
            check_cmd = f"iptables -C INPUT -s {ip} -j DROP 2>/dev/null"
            check_result = os.system(check_cmd)
            logger.info(f"Check command result: {check_result}")
            
            if check_result == 0:
                logger.info(f"IP {ip} is already blocked")
                blocked_ips.add(ip)
                return
            
            # Add the blocking rule
            block_cmd = f"iptables -A INPUT -s {ip} -j DROP"
            result = os.system(block_cmd)
            logger.info(f"Block command result: {result}")
            
            if result == 0:
                blocked_ips.add(ip)
                alert_message = f"🚨 *Security Alert* 🚨\n🚫 IP {ip} has been blocked due to {FAILED_LOGIN_THRESHOLD} failed SSH attempts within {TIME_WINDOW} seconds"
                send_slack_alert(alert_message)
                logger.info(f"Successfully blocked IP: {ip}")
            else:
                logger.error(f"Failed to block IP {ip}. Exit code: {result}")
                
        except Exception as e:
            logger.error(f"Error blocking IP {ip}: {str(e)}")

def process_log_line(line):
    """Process a single log line"""
    try:
        # Check for failed SSH attempts
        if "Failed password" in line and "ssh" in line:
            # Extract IP address
            ip_match = re.search(r'from (\d+\.\d+\.\d+\.\d+)', line)
            if ip_match:
                ip = ip_match.group(1)
                current_time = time.time()
                logger.info(f"Found failed attempt from IP: {ip}")

                # Add attempt to tracking
                failed_attempts[ip].append(current_time)

                # Clean up old attempts
                failed_attempts[ip] = [t for t in failed_attempts[ip]
                                     if current_time - t < TIME_WINDOW]

                logger.info(f"Current failed attempts for {ip}: {len(failed_attempts[ip])}")

                # Check if threshold reached
                if len(failed_attempts[ip]) >= FAILED_LOGIN_THRESHOLD:
                    logger.info(f"Threshold reached for IP: {ip}")
                    block_ip(ip)
    except Exception as e:
        logger.error(f"Error processing log line: {str(e)}")
        logger.error(f"Problematic line: {line.strip()}")

def process_existing_logs():
    """Process existing log entries"""
    logger.info("Processing existing log entries...")
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r') as f:
                for line in f:
                    process_log_line(line)
        except Exception as e:
            logger.error(f"Error processing existing logs: {str(e)}")
    logger.info("Finished processing existing log entries")

class LogEventHandler(pyinotify.ProcessEvent):
    def process_IN_MODIFY(self, event):
        """Process file modification events"""
        if event.pathname == LOG_FILE:
            logger.debug("Log file modified, processing new entries...")
            try:
                with open(LOG_FILE, 'r') as f:
                    f.seek(0, 2)  # Go to end of file
                    while True:
                        line = f.readline()
                        if not line:
                            break
                        process_log_line(line)
            except Exception as e:
                logger.error(f"Error processing modified log file: {str(e)}")

def main():
    logger.info("Starting SSH brute-force detection system...")
    
    try:
        # Process existing log entries
        process_existing_logs()

        # Initialize inotify
        wm = pyinotify.WatchManager()
        handler = LogEventHandler()
        notifier = pyinotify.Notifier(wm, handler)

        # Add watch for the log file
        wm.add_watch(LOG_FILE, pyinotify.IN_MODIFY)

        logger.info("Now monitoring for new SSH attempts...")

        # Start monitoring
        notifier.loop()
    except KeyboardInterrupt:
        logger.info("\nStopping monitoring...")
    except Exception as e:
        logger.error(f"Fatal error in main loop: {str(e)}")
        raise

if __name__ == "__main__":
    main() 