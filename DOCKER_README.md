# Docker Setup for SSH Brute-Force Monitor

This guide explains how to set up and test the SSH brute-force monitoring system using Docker.

## Prerequisites

- Docker installed
- Docker Compose installed
- Slack token (for notifications)

## Setup Instructions

1. **Create necessary directories**:
   ```bash
   mkdir logs
   ```

2. **Set up environment variables**:
   ```bash
   # Create .env file with your Slack configuration
   cp .env.example .env
   # Edit .env and add your Slack token
   ```

3. **Build and start the container**:
   ```bash
   docker-compose up --build
   ```

4. **In a separate terminal, run the test script**:
   ```bash
   # Make the test script executable
   chmod +x test_ssh_attempts.py
   # Run the test
   ./test_ssh_attempts.py
   ```

## Testing the System

1. **Monitor the logs**:
   ```bash
   # Watch the auth.log
   tail -f logs/auth.log
   ```

2. **Check iptables rules**:
   ```bash
   # Connect to the container
   docker exec -it ssh-monitor bash
   # Check iptables rules
   iptables -L -n
   ```

3. **Verify Slack notifications**:
   - Check your configured Slack channel for alerts

## Important Notes

- The container runs in privileged mode to allow iptables modifications
- SSH is exposed on port 2222 of the host machine
- Logs are persisted in the `logs` directory
- The container will automatically restart unless stopped

## Troubleshooting

1. **If the container fails to start**:
   ```bash
   # Check container logs
   docker-compose logs
   ```

2. **If iptables rules aren't being added**:
   ```bash
   # Check if the container has proper permissions
   docker exec -it ssh-monitor bash
   iptables -L -n
   ```

3. **If Slack notifications aren't working**:
   - Verify your Slack token in the .env file
   - Check if the bot is added to the channel
   - Monitor the container logs for any Slack API errors

## Cleanup

To stop and remove the container:
```bash
docker-compose down
``` 