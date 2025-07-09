# 🚀 ChamaLink Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying ChamaLink to production environments. It covers everything from server setup to monitoring and maintenance.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Application Deployment](#application-deployment)
4. [SSL Configuration](#ssl-configuration)
5. [Monitoring Setup](#monitoring-setup)
6. [Backup Strategy](#backup-strategy)
7. [Maintenance Procedures](#maintenance-procedures)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- **Operating System**: Ubuntu 20.04 LTS or CentOS 8+
- **CPU**: 4 cores minimum (8 cores recommended for production)
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 100GB SSD minimum (500GB recommended)
- **Network**: 1Gbps connection with static IP
- **Domain**: Registered domain name with DNS access

### Required Accounts & Services
- [ ] GitHub account with repository access
- [ ] Domain registrar account (Namecheap, GoDaddy, etc.)
- [ ] Cloud provider account (AWS, DigitalOcean, Linode)
- [ ] Email service (Gmail, SendGrid, Mailgun)
- [ ] M-Pesa developer account (Safaricom)
- [ ] SSL certificate provider (Let's Encrypt recommended)

## Server Setup

### 1. Initial Server Configuration

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl wget git vim htop tree unzip

# Create application user
sudo useradd -m -s /bin/bash chamalink
sudo usermod -aG sudo chamalink

# Setup SSH access for application user
sudo -u chamalink mkdir -p /home/chamalink/.ssh
sudo -u chamalink chmod 700 /home/chamalink/.ssh

# Configure firewall
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw --force enable
```

### 2. Install Required Software

```bash
# Install Python 3.8+
sudo apt install -y python3.8 python3.8-venv python3.8-dev python3-pip

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib postgresql-client
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Install Redis
sudo apt install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Install Nginx
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx

# Install Certbot for SSL
sudo apt install -y certbot python3-certbot-nginx

# Install Node.js (for frontend build tools)
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt install -y nodejs
```

### 3. Database Setup

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE chamalink_prod;
CREATE USER chamalink WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE chamalink_prod TO chamalink;
ALTER USER chamalink CREATEDB;
\q

# Test database connection
sudo -u chamalink psql -h localhost -d chamalink_prod -U chamalink
```

### 4. Redis Configuration

```bash
# Edit Redis configuration
sudo vim /etc/redis/redis.conf

# Recommended settings:
# maxmemory 256mb
# maxmemory-policy allkeys-lru
# save 900 1
# save 300 10
# save 60 10000

# Restart Redis
sudo systemctl restart redis-server
```

## Application Deployment

### 1. Clone Repository

```bash
# Switch to application user
sudo -i -u chamalink

# Clone the repository
cd /home/chamalink
git clone https://github.com/RahasoftBwire/chamalink.git app
cd app

# Create and activate virtual environment
python3.8 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
vim .env
```

**Production .env file:**
```env
# Application Configuration
SECRET_KEY=your-super-secure-secret-key-min-32-chars
DATABASE_URL=postgresql://chamalink:your_secure_password@localhost/chamalink_prod
FLASK_ENV=production
FLASK_DEBUG=False

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=noreply@yourdomain.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=ChamaLink <noreply@yourdomain.com>

# M-Pesa Configuration
MPESA_CONSUMER_KEY=your-consumer-key
MPESA_CONSUMER_SECRET=your-consumer-secret
MPESA_SHORTCODE=your-shortcode
MPESA_PASSKEY=your-passkey
MPESA_ENVIRONMENT=production

# Security Settings
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
PERMANENT_SESSION_LIFETIME=1800

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Application Settings
UPLOAD_FOLDER=/home/chamalink/app/uploads
MAX_CONTENT_LENGTH=16777216
```

### 3. Database Migration

```bash
# Initialize database
export FLASK_APP=run.py
flask db upgrade

# Create initial admin user (optional)
python3 create_admin.py
```

### 4. Application Server Setup

**Create Gunicorn configuration file:**
```bash
vim /home/chamalink/app/gunicorn.conf.py
```

```python
# Gunicorn configuration file
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
user = "chamalink"
group = "chamalink"

# Logging
accesslog = "/home/chamalink/app/logs/access.log"
errorlog = "/home/chamalink/app/logs/error.log"
loglevel = "info"

# Process naming
proc_name = "chamalink"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
```

**Create log directory:**
```bash
mkdir -p /home/chamalink/app/logs
```

### 5. Systemd Service Configuration

```bash
# Exit from chamalink user
exit

# Create systemd service file
sudo vim /etc/systemd/system/chamalink.service
```

```ini
[Unit]
Description=ChamaLink Flask Application
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=chamalink
Group=chamalink
WorkingDirectory=/home/chamalink/app
Environment=PATH=/home/chamalink/app/venv/bin
EnvironmentFile=/home/chamalink/app/.env
ExecStart=/home/chamalink/app/venv/bin/gunicorn --config /home/chamalink/app/gunicorn.conf.py wsgi:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

**Enable and start the service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable chamalink
sudo systemctl start chamalink

# Check service status
sudo systemctl status chamalink
```

## SSL Configuration

### 1. Nginx Configuration

```bash
# Create Nginx site configuration
sudo vim /etc/nginx/sites-available/chamalink
```

```nginx
# HTTP server (redirects to HTTPS)
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration (will be updated by Certbot)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Main application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files
    location /static {
        alias /home/chamalink/app/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Media files
    location /uploads {
        alias /home/chamalink/app/uploads;
        expires 1y;
        add_header Cache-Control "public";
    }

    # Security
    location = /robots.txt {
        alias /home/chamalink/app/app/static/robots.txt;
        access_log off;
    }

    # Deny access to sensitive files
    location ~ /\. {
        deny all;
        access_log off;
    }

    location ~ \.py$ {
        deny all;
        access_log off;
    }
}
```

**Enable the site:**
```bash
sudo ln -s /etc/nginx/sites-available/chamalink /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 2. SSL Certificate Setup

```bash
# Obtain SSL certificate with Certbot
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test certificate renewal
sudo certbot renew --dry-run

# Setup automatic renewal
sudo crontab -e
# Add this line:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

## Monitoring Setup

### 1. Application Monitoring

**Create monitoring script:**
```bash
sudo vim /home/chamalink/monitor.sh
```

```bash
#!/bin/bash
# ChamaLink monitoring script

LOG_FILE="/var/log/chamalink-monitor.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Check application health
check_app() {
    local response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
    if [ "$response" != "200" ]; then
        echo "[$DATE] ERROR: Application health check failed (HTTP $response)" >> $LOG_FILE
        # Restart application
        sudo systemctl restart chamalink
        # Send alert email
        echo "ChamaLink application restarted at $DATE" | mail -s "ChamaLink Alert" admin@yourdomain.com
    fi
}

# Check database connectivity
check_database() {
    local result=$(sudo -u chamalink psql -h localhost -d chamalink_prod -U chamalink -c "SELECT 1;" 2>&1)
    if [[ $result != *"1"* ]]; then
        echo "[$DATE] ERROR: Database connection failed" >> $LOG_FILE
    fi
}

# Check disk space
check_disk() {
    local usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$usage" -gt 85 ]; then
        echo "[$DATE] WARNING: Disk usage at ${usage}%" >> $LOG_FILE
    fi
}

# Run checks
check_app
check_database
check_disk
```

**Make executable and setup cron job:**
```bash
sudo chmod +x /home/chamalink/monitor.sh
sudo crontab -e
# Add this line to run every 5 minutes:
# */5 * * * * /home/chamalink/monitor.sh
```

### 2. Log Rotation

```bash
# Create logrotate configuration
sudo vim /etc/logrotate.d/chamalink
```

```
/home/chamalink/app/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 chamalink chamalink
    postrotate
        systemctl reload chamalink
    endscript
}

/var/log/chamalink-monitor.log {
    weekly
    missingok
    rotate 4
    compress
    delaycompress
    notifempty
}
```

## Backup Strategy

### 1. Database Backup

**Create backup script:**
```bash
sudo vim /home/chamalink/backup.sh
```

```bash
#!/bin/bash
# ChamaLink backup script

BACKUP_DIR="/backups/chamalink"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="chamalink_prod"
DB_USER="chamalink"

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
echo "Starting database backup..."
pg_dump -h localhost -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Application files backup
echo "Starting application backup..."
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='logs' \
    /home/chamalink/app

# Cleanup old backups (keep last 30 days)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

# Upload to cloud storage (optional)
# aws s3 cp $BACKUP_DIR/db_backup_$DATE.sql.gz s3://your-backup-bucket/
# aws s3 cp $BACKUP_DIR/app_backup_$DATE.tar.gz s3://your-backup-bucket/

echo "Backup completed: $DATE"
```

**Setup automated backups:**
```bash
sudo chmod +x /home/chamalink/backup.sh
sudo crontab -e
# Add this line for daily backups at 2 AM:
# 0 2 * * * /home/chamalink/backup.sh
```

### 2. Restore Procedures

**Database restore:**
```bash
# Stop application
sudo systemctl stop chamalink

# Restore database
gunzip -c /backups/chamalink/db_backup_YYYYMMDD_HHMMSS.sql.gz | \
    psql -h localhost -U chamalink chamalink_prod

# Start application
sudo systemctl start chamalink
```

**Application restore:**
```bash
# Extract application backup
tar -xzf /backups/chamalink/app_backup_YYYYMMDD_HHMMSS.tar.gz -C /

# Restore permissions
sudo chown -R chamalink:chamalink /home/chamalink/app

# Restart services
sudo systemctl restart chamalink
```

## Maintenance Procedures

### 1. Regular Updates

**Monthly maintenance script:**
```bash
#!/bin/bash
# Monthly maintenance script

# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python packages
source /home/chamalink/app/venv/bin/activate
pip list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1 | xargs -n1 pip install -U

# Restart services
sudo systemctl restart chamalink
sudo systemctl restart nginx

# Clean up logs
sudo journalctl --vacuum-time=30d

# Run application maintenance
cd /home/chamalink/app
python3 maintenance.py

echo "Monthly maintenance completed: $(date)"
```

### 2. Database Maintenance

```sql
-- Weekly database maintenance queries
-- Run as postgres user

-- Analyze tables for query optimization
ANALYZE;

-- Vacuum to reclaim space
VACUUM;

-- Reindex to maintain performance
REINDEX DATABASE chamalink_prod;

-- Check for unused indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY n_distinct DESC;
```

### 3. Security Updates

**Weekly security checks:**
```bash
#!/bin/bash
# Security maintenance script

# Check for security updates
sudo apt list --upgradable | grep -i security

# Update SSL certificates
sudo certbot renew --quiet

# Check file permissions
find /home/chamalink/app -type f -name "*.py" ! -perm 644 -exec chmod 644 {} \;
find /home/chamalink/app -type d ! -perm 755 -exec chmod 755 {} \;

# Check for suspicious log entries
grep -i "error\|warning\|failed" /var/log/nginx/error.log | tail -20
grep -i "error\|exception" /home/chamalink/app/logs/error.log | tail -20

echo "Security check completed: $(date)"
```

## Troubleshooting

### Common Issues & Solutions

#### 1. Application Won't Start
```bash
# Check service status
sudo systemctl status chamalink

# Check logs
sudo journalctl -u chamalink -n 50

# Check application logs
tail -f /home/chamalink/app/logs/error.log

# Common fixes:
# - Check environment variables in .env file
# - Verify database connectivity
# - Check file permissions
# - Ensure all dependencies are installed
```

#### 2. Database Connection Issues
```bash
# Test database connection
sudo -u chamalink psql -h localhost -d chamalink_prod -U chamalink

# Check PostgreSQL status
sudo systemctl status postgresql

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-*-main.log

# Reset database password if needed
sudo -u postgres psql -c "ALTER USER chamalink PASSWORD 'new_password';"
```

#### 3. High Memory Usage
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -10

# Check application processes
ps aux | grep gunicorn

# Restart application if needed
sudo systemctl restart chamalink

# Consider increasing server memory or optimizing queries
```

#### 4. SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Test SSL configuration
openssl s_client -connect yourdomain.com:443

# Renew certificate manually
sudo certbot renew --force-renewal

# Check Nginx configuration
sudo nginx -t
```

#### 5. Performance Issues
```bash
# Check server load
top
htop

# Check disk I/O
iotop

# Check network connections
netstat -tulpn

# Analyze slow queries
sudo -u postgres psql chamalink_prod -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

### Emergency Procedures

#### Application Rollback
```bash
# Stop current application
sudo systemctl stop chamalink

# Restore from backup
tar -xzf /backups/chamalink/app_backup_YYYYMMDD_HHMMSS.tar.gz -C /

# Restore database if needed
gunzip -c /backups/chamalink/db_backup_YYYYMMDD_HHMMSS.sql.gz | \
    psql -h localhost -U chamalink chamalink_prod

# Restart services
sudo systemctl start chamalink
sudo systemctl restart nginx
```

#### Emergency Contacts
- **Primary Admin**: Bilford Bwire - bilfordbwire@gmail.com
- **Server Provider**: [Your hosting provider support]
- **Domain Registrar**: [Your domain provider support]
- **SSL Provider**: Let's Encrypt support forums

### Monitoring Dashboard URLs
- **Application Health**: https://yourdomain.com/health
- **Server Metrics**: Set up monitoring dashboard (Grafana, etc.)
- **Uptime Monitoring**: External service (Pingdom, UptimeRobot)

---

*This deployment guide should be updated regularly as the application evolves. Last updated: July 2025*
