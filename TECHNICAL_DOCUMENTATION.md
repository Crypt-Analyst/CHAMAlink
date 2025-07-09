# 🔧 ChamaLink Technical Documentation

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Database Schema](#database-schema)
3. [API Documentation](#api-documentation)
4. [Security Implementation](#security-implementation)
5. [Performance Optimization](#performance-optimization)
6. [Deployment Guide](#deployment-guide)
7. [Monitoring & Maintenance](#monitoring--maintenance)

## System Architecture

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                        Load Balancer (Nginx)                    │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────────┐
│                     Application Layer                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────┐  │
│  │   Flask     │ │   Gunicorn  │ │   Redis     │ │  Celery  │  │
│  │   App 1     │ │   WSGI      │ │   Cache     │ │  Queue   │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └──────────┘  │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────────┐
│                      Data Layer                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────┐  │
│  │ PostgreSQL  │ │   File      │ │   Backup    │ │   Logs   │  │
│  │ Primary DB  │ │   Storage   │ │   Storage   │ │  Storage │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └──────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack Details

#### Backend Framework
- **Flask 3.1.1**: Lightweight Python web framework
- **SQLAlchemy 2.0**: ORM for database interactions
- **Flask-Migrate**: Database migration management
- **Flask-Login**: User session management
- **Flask-Mail**: Email functionality
- **Gunicorn**: WSGI HTTP Server for production

#### Database
- **PostgreSQL 14+**: Primary database for production
- **SQLite**: Development and testing database
- **Redis**: Caching and session storage
- **Backup Strategy**: Automated daily backups with 30-day retention

#### Frontend
- **HTML5/CSS3**: Modern web standards
- **Bootstrap 5.3**: Responsive UI framework
- **JavaScript ES6+**: Client-side functionality
- **jQuery 3.6**: DOM manipulation and AJAX
- **Chart.js**: Data visualization

#### External Services
- **M-Pesa API**: Payment processing
- **SMTP (Gmail)**: Email services
- **SMS Gateway**: SMS notifications
- **CloudFlare**: CDN and DDoS protection

## Database Schema

### Core Tables

#### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    phone_number VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    is_super_admin BOOLEAN DEFAULT FALSE,
    date_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    two_factor_secret VARCHAR(32)
);
```

#### Chamas Table
```sql
CREATE TABLE chamas (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    admin_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    meeting_day VARCHAR(20),
    meeting_time TIME,
    contribution_amount DECIMAL(10,2),
    contribution_frequency VARCHAR(20),
    registration_fee DECIMAL(10,2) DEFAULT 0,
    location VARCHAR(100),
    rules TEXT,
    objectives TEXT
);
```

#### Transactions Table
```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    chama_id INTEGER REFERENCES chamas(id),
    user_id INTEGER REFERENCES users(id),
    amount DECIMAL(10,2) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    mpesa_receipt_number VARCHAR(50),
    reference_number VARCHAR(100)
);
```

### Relationship Diagram
```
Users ──┐
        ├── Chamas ──┬── Transactions
        │            ├── Events
        │            ├── Loans
        │            └── Reports
        ├── Subscriptions
        ├── Notifications
        └── AuditLogs
```

## API Documentation

### Authentication Endpoints

#### POST /auth/login
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "remember_me": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "user@example.com",
    "is_admin": false
  },
  "redirect": "/dashboard"
}
```

#### POST /auth/register
```json
{
  "username": "johndoe",
  "email": "user@example.com",
  "password": "securepassword",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+254712345678"
}
```

### Chama Management Endpoints

#### GET /api/chamas
```json
{
  "chamas": [
    {
      "id": 1,
      "name": "Bidii Chama",
      "description": "Investment group for young professionals",
      "admin_id": 1,
      "member_count": 12,
      "total_contributions": 150000,
      "status": "active"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 10
}
```

#### POST /api/chamas
```json
{
  "name": "New Chama",
  "description": "Description of the chama",
  "meeting_day": "Saturday",
  "meeting_time": "14:00",
  "contribution_amount": 5000,
  "contribution_frequency": "monthly"
}
```

### Transaction Endpoints

#### POST /api/transactions
```json
{
  "chama_id": 1,
  "amount": 5000,
  "transaction_type": "contribution",
  "description": "Monthly contribution for January 2025"
}
```

#### GET /api/transactions/{transaction_id}
```json
{
  "id": 1,
  "chama_id": 1,
  "user_id": 1,
  "amount": 5000,
  "transaction_type": "contribution",
  "status": "completed",
  "created_at": "2025-01-15T10:30:00Z",
  "mpesa_receipt_number": "PH123456789"
}
```

## Security Implementation

### Authentication & Authorization
- **Password Hashing**: Bcrypt with salt rounds (12)
- **Session Management**: Flask-Login with secure session cookies
- **JWT Tokens**: For API authentication (future implementation)
- **Role-Based Access**: Admin, Secretary, Member roles
- **Two-Factor Authentication**: TOTP-based 2FA for admin accounts

### Data Protection
- **Encryption at Rest**: Database encryption for sensitive fields
- **Encryption in Transit**: HTTPS/TLS 1.3 for all communications
- **Input Validation**: SQLAlchemy ORM prevents SQL injection
- **CSRF Protection**: Built-in Flask-WTF CSRF tokens
- **XSS Prevention**: Jinja2 template auto-escaping

### Security Headers
```python
@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

### Rate Limiting
```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.environ.get('HTTP_X_REAL_IP', request.remote_addr),
    default_limits=["1000 per hour", "100 per minute"]
)

@app.route('/api/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    # Login implementation
    pass
```

## Performance Optimization

### Database Optimization
- **Indexing Strategy**: Composite indexes on frequently queried columns
- **Query Optimization**: Eager loading to prevent N+1 queries
- **Connection Pooling**: SQLAlchemy connection pool (pool_size=20)
- **Read Replicas**: For reporting and analytics queries

### Caching Strategy
```python
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0'
})

@cache.memoize(timeout=300)
def get_chama_statistics(chama_id):
    # Expensive database query
    pass
```

### Frontend Optimization
- **Asset Compression**: Gzip compression for static files
- **CDN Integration**: CloudFlare for global content delivery
- **Lazy Loading**: Progressive loading of images and data
- **Minification**: CSS and JavaScript minification

### Monitoring & Metrics
```python
from prometheus_flask_exporter import PrometheusMetrics

metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Application info', version='1.0.0')

@metrics.counter('requests_by_status', 'Request count by status',
                labels={'status': lambda: request.status})
def track_requests():
    pass
```

## Deployment Guide

### Production Environment Setup

#### Server Requirements
- **OS**: Ubuntu 20.04 LTS or CentOS 8
- **CPU**: 4 cores minimum (8 cores recommended)
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 100GB SSD minimum
- **Network**: 1Gbps connection

#### Installation Script
```bash
#!/bin/bash
# ChamaLink Production Deployment Script

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.8 python3.8-venv python3-pip postgresql postgresql-contrib nginx redis-server

# Create application user
sudo useradd -m -s /bin/bash chamalink

# Clone repository
sudo -u chamalink git clone https://github.com/RahasoftBwire/chamalink.git /home/chamalink/app

# Setup virtual environment
sudo -u chamalink python3.8 -m venv /home/chamalink/app/venv
sudo -u chamalink /home/chamalink/app/venv/bin/pip install -r /home/chamalink/app/requirements.txt

# Setup database
sudo -u postgres createdb chamalink_prod
sudo -u postgres createuser chamalink

# Configure environment
sudo -u chamalink cp /home/chamalink/app/.env.example /home/chamalink/app/.env
# Edit .env file with production values

# Run migrations
sudo -u chamalink /home/chamalink/app/venv/bin/flask db upgrade

# Setup systemd service
sudo cp /home/chamalink/app/deployment/chamalink.service /etc/systemd/system/
sudo systemctl enable chamalink
sudo systemctl start chamalink

# Configure Nginx
sudo cp /home/chamalink/app/deployment/nginx.conf /etc/nginx/sites-available/chamalink
sudo ln -s /etc/nginx/sites-available/chamalink /etc/nginx/sites-enabled/
sudo systemctl reload nginx

# Setup SSL with Let's Encrypt
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

#### Nginx Configuration
```nginx
server {
    listen 80;
    server_name chamalink.com www.chamalink.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name chamalink.com www.chamalink.com;

    ssl_certificate /etc/letsencrypt/live/chamalink.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/chamalink.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /home/chamalink/app/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

#### Systemd Service
```ini
[Unit]
Description=ChamaLink Flask Application
After=network.target

[Service]
User=chamalink
Group=chamalink
WorkingDirectory=/home/chamalink/app
Environment=PATH=/home/chamalink/app/venv/bin
ExecStart=/home/chamalink/app/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:8000 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

## Monitoring & Maintenance

### Application Monitoring
- **Uptime Monitoring**: Pingdom or UptimeRobot
- **Performance Monitoring**: New Relic or DataDog
- **Error Tracking**: Sentry for exception monitoring
- **Log Management**: ELK Stack (Elasticsearch, Logstash, Kibana)

### Health Check Endpoint
```python
@app.route('/health')
def health_check():
    try:
        # Check database connectivity
        db.session.execute('SELECT 1')
        
        # Check Redis connectivity
        cache.get('health_check')
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': app.config.get('VERSION', '1.0.0')
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500
```

### Backup Strategy
```bash
#!/bin/bash
# Database backup script
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/chamalink"
DB_NAME="chamalink_prod"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
pg_dump $DB_NAME | gzip > $BACKUP_DIR/chamalink_$DATE.sql.gz

# Upload to cloud storage (AWS S3, Google Cloud, etc.)
aws s3 cp $BACKUP_DIR/chamalink_$DATE.sql.gz s3://chamalink-backups/

# Keep only last 30 days of local backups
find $BACKUP_DIR -name "chamalink_*.sql.gz" -mtime +30 -delete
```

### Maintenance Tasks
```python
# Scheduled maintenance tasks using Celery
from celery import Celery

@celery.task
def cleanup_expired_sessions():
    """Remove expired user sessions"""
    expired_sessions = UserSession.query.filter(
        UserSession.expires_at < datetime.utcnow()
    ).all()
    
    for session in expired_sessions:
        db.session.delete(session)
    
    db.session.commit()
    return f"Cleaned up {len(expired_sessions)} expired sessions"

@celery.task
def generate_daily_reports():
    """Generate daily financial reports"""
    for chama in Chama.query.filter_by(status='active').all():
        report = generate_financial_report(chama.id)
        send_report_email(chama.admin_email, report)
    
    return "Daily reports generated and sent"
```

### Performance Tuning
- **Database Query Optimization**: Regular EXPLAIN ANALYZE reviews
- **Memory Usage**: Monitor and optimize Python memory usage
- **Response Times**: Target < 2 seconds for all endpoints
- **Concurrent Users**: Load testing for 10,000+ concurrent users
- **Resource Scaling**: Auto-scaling based on CPU/memory thresholds

---

*This technical documentation is maintained by the ChamaLink development team. Last updated: July 2025*
