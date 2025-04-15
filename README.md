# SSH Brute-Force Detection System

A real-time log monitoring system that detects and blocks SSH brute-force attempts, with Slack notifications.

## Features

- Real-time monitoring of `/var/log/auth.log`
- Detection of failed SSH login attempts
- Automatic IP blocking using iptables
- Slack notifications for security alerts
- Configurable thresholds and time windows
- Low-resource implementation using inotify

## Prerequisites

- Python 3.6 or higher
- iptables (for IP blocking)
- Slack workspace and bot token
- Root/sudo access (for iptables)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd log-monitor
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Copy the example environment file and configure it:
```bash
cp .env.example .env
```

4. Edit `.env` and add your Slack token and other configurations.

## Usage

1. Start the monitoring system:
```bash
sudo python3 log_monitor.py
```

The system will:
- Monitor auth.log for failed SSH attempts
- Track IP addresses with multiple failures within the configured time window
- Block IPs that exceed the failure threshold
- Send Slack notifications for blocked IPs

## Configuration

Edit the `.env` file to configure:
- `SLACK_TOKEN`: Your Slack bot token
- `SLACK_CHANNEL`: Channel for security alerts
- `FAILED_LOGIN_THRESHOLD`: Number of failed attempts before blocking
- `TIME_WINDOW`: Time window in seconds for counting attempts

## Security Considerations

- Run the script with appropriate permissions (sudo required for iptables)
- Keep your Slack token secure
- Regularly review blocked IPs
- Consider implementing additional security measures

## Troubleshooting

- Ensure the auth.log file exists and is readable
- Check iptables permissions
- Verify Slack token and channel settings
- Monitor system logs for any errors

## License

MIT License 