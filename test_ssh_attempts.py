#!/usr/bin/env python3

import time
import random
import subprocess

def generate_failed_attempt(ip):
    """Generate a failed SSH attempt log entry"""
    log_entry = f"Failed password for root from {ip} port {random.randint(1000, 65535)} ssh2"
    subprocess.run(['logger', log_entry])

def main():
    # Test IPs
    test_ips = [
        "192.168.1.100",
        "10.0.0.50",
        "172.16.0.25"
    ]
    
    print("Starting SSH attack simulation...")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            # Randomly select an IP
            ip = random.choice(test_ips)
            # Generate failed attempt
            generate_failed_attempt(ip)
            print(f"Generated failed attempt from {ip}")
            # Wait random time between attempts
            time.sleep(random.uniform(0.5, 2))
    except KeyboardInterrupt:
        print("\nStopping simulation...")

if __name__ == "__main__":
    main() 