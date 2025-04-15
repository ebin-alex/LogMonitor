FROM ubuntu:22.04

# Install required packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    iptables \
    openssh-server \
    rsyslog \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Create directory for the application
WORKDIR /app

# Copy application files
COPY requirements.txt .
COPY log_monitor.py .
COPY .env .

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Create necessary directories and set permissions
RUN mkdir -p /var/run/sshd && \
    mkdir -p /var/log && \
    touch /var/log/auth.log && \
    chown root:root /var/log/auth.log && \
    chmod 644 /var/log/auth.log && \
    mkdir -p /var/log/supervisor && \
    chmod 777 /var/log/supervisor && \
    mkdir -p /var/spool/rsyslog && \
    chown -R syslog:syslog /var/spool/rsyslog

# Create a test user
RUN useradd -m -s /bin/bash testuser && \
    echo "testuser:password123" | chpasswd

# Configure SSH
RUN echo "SyslogFacility AUTH" >> /etc/ssh/sshd_config && \
    echo "LogLevel INFO" >> /etc/ssh/sshd_config && \
    echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config && \
    echo "PermitRootLogin no" >> /etc/ssh/sshd_config && \
    echo "UsePAM yes" >> /etc/ssh/sshd_config && \
    echo "X11Forwarding yes" >> /etc/ssh/sshd_config && \
    echo "PrintMotd no" >> /etc/ssh/sshd_config && \
    echo "AcceptEnv LANG LC_*" >> /etc/ssh/sshd_config

# Configure rsyslog
RUN echo '$ModLoad imuxsock\n\
$WorkDirectory /var/spool/rsyslog\n\
auth,authpriv.*    /var/log/auth.log\n\
*.info;mail.none;authpriv.none  /var/log/messages' > /etc/rsyslog.conf && \
    rm -f /etc/rsyslog.d/* && \
    mkdir -p /var/lib/rsyslog

# Configure supervisord
RUN echo '[supervisord]\n\
nodaemon=true\n\
logfile=/var/log/supervisor/supervisord.log\n\
\n\
[program:rsyslog]\n\
command=/usr/sbin/rsyslogd -n -f /etc/rsyslog.conf\n\
priority=1\n\
stdout_logfile=/var/log/supervisor/rsyslog-stdout.log\n\
stderr_logfile=/var/log/supervisor/rsyslog-stderr.log\n\
\n\
[program:sshd]\n\
command=/usr/sbin/sshd -D\n\
priority=2\n\
stdout_logfile=/var/log/supervisor/sshd-stdout.log\n\
stderr_logfile=/var/log/supervisor/sshd-stderr.log\n\
\n\
[program:log_monitor]\n\
command=python3 /app/log_monitor.py\n\
directory=/app\n\
user=root\n\
priority=3\n\
stdout_logfile=/var/log/supervisor/log_monitor-stdout.log\n\
stderr_logfile=/var/log/supervisor/log_monitor-stderr.log' > /etc/supervisor/conf.d/supervisord.conf

# Expose SSH port
EXPOSE 22

# Start supervisord
CMD ["/usr/bin/supervisord"] 