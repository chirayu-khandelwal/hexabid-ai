# HexaBid ERP - Complete Deployment Guide

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Server Requirements](#server-requirements)
3. [Initial Server Setup](#initial-server-setup)
4. [Application Deployment](#application-deployment)
5. [Service Configuration](#service-configuration)
6. [SSL Certificate Setup](#ssl-certificate-setup)
7. [Post-Deployment Tasks](#post-deployment-tasks)
8. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

Before deploying HexaBid ERP, ensure you have:

- [x] VPN Server Access (root@66.116.197.150)
- [x] Domain name configured (app.hexabid.co.in)
- [x] DNS A record pointing to server IP (66.116.197.150)
- [x] AAPanel access (https://66.116.197.150:37711/)
  - Username: Hexabid
  - Password: 6f1f4f74
- [x] GeM Portal credentials
  - Email: prashant.hexatech@gmail.com
  - Password: Hexa@gem123
- [ ] Email service API keys (optional)
- [ ] WhatsApp service API keys (optional)
- [ ] Payment gateway credentials (optional)

---

## Server Requirements

### Minimum Specifications
- **OS**: Ubuntu 20.04 LTS or higher
- **CPU**: 2 cores minimum (4 recommended)
- **RAM**: 4 GB minimum (8 GB recommended)
- **Storage**: 50 GB minimum
- **Network**: Public IP with ports 80, 443 open

### Required Software
- Python 3.8+
- Node.js 16+ and Yarn
- MongoDB 4.4+
- Nginx
- Chrome/Chromium browser (for scraping)
- Certbot (for SSL)

---

## Initial Server Setup

### Step 1: Connect to Server

```bash
# SSH into the server
ssh root@66.116.197.150
# Password: Hexabid@666
```

### Step 2: Update System

```bash
apt-get update
apt-get upgrade -y
apt-get install -y curl wget git
```

### Step 3: Install Required Software

```bash
# Install Python 3 and pip
apt-get install -y python3 python3-pip python3-venv

# Install Node.js and Yarn
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs
npm install -g yarn

# Install MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/4.4 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-4.4.list
apt-get update
apt-get install -y mongodb-org

# Start MongoDB
systemctl start mongod
systemctl enable mongod

# Install Nginx
apt-get install -y nginx

# Install Certbot for SSL
apt-get install -y certbot python3-certbot-nginx

# Install Chrome/Chromium for scraping
apt-get install -y chromium-browser chromium-chromedriver
```

---

## Application Deployment

### Method 1: Using Automated Deployment Script

1. **Transfer application files to server**

```bash
# On your local machine, create a deployment package
cd /path/to/hexabid-erp
tar -czf hexabid-erp.tar.gz backend/ frontend/ deploy.sh configure_scraper.sh

# Transfer to server
scp hexabid-erp.tar.gz root@66.116.197.150:/root/

# On server, extract files
ssh root@66.116.197.150
cd /root
tar -xzf hexabid-erp.tar.gz
```

2. **Run deployment script**

```bash
chmod +x deploy.sh
./deploy.sh
```

The script will:
- Install all dependencies
- Create application directories at `/var/www/hexabid`
- Setup backend Python virtual environment
- Build frontend production bundle
- Configure Nginx
- Create and start systemd service for backend
- Optionally setup SSL certificate

### Method 2: Manual Deployment

If you prefer manual deployment, follow these steps:

#### A. Create Application Directory

```bash
mkdir -p /var/www/hexabid/backend
mkdir -p /var/www/hexabid/frontend
mkdir -p /var/log/hexabid
```

#### B. Deploy Backend

```bash
cd /var/www/hexabid/backend

# Copy backend files (adjust source path)
cp -r /root/backend/* .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Setup environment variables
cp .env.production .env

# Edit .env file with production values
nano .env

deactivate
```

#### C. Deploy Frontend

```bash
cd /var/www/hexabid/frontend

# Copy frontend files
cp -r /root/frontend/* .

# Setup environment
cp .env.production .env

# Edit .env to point to production domain
nano .env
# Update: REACT_APP_BACKEND_URL=https://app.hexabid.co.in

# Install dependencies
yarn install

# Build production bundle
yarn build
```

#### D. Configure Nginx

```bash
# Create Nginx configuration
nano /etc/nginx/sites-available/hexabid-erp
```

Paste the following configuration:

```nginx
# Backend API Server
upstream backend_api {
    server 127.0.0.1:8001;
}

server {
    listen 80;
    listen [::]:80;
    server_name app.hexabid.co.in;

    root /var/www/hexabid/frontend/build;
    index index.html;

    # Frontend static files
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend API proxy
    location /api/ {
        proxy_pass http://backend_api/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    client_max_body_size 50M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss application/rss+xml font/truetype font/opentype application/vnd.ms-fontobject image/svg+xml;
}
```

Enable the site:

```bash
ln -s /etc/nginx/sites-available/hexabid-erp /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx
```

#### E. Create Backend Systemd Service

```bash
nano /etc/systemd/system/hexabid-backend.service
```

Paste:

```ini
[Unit]
Description=HexaBid ERP Backend API
After=network.target mongodb.service

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/hexabid/backend
Environment="PATH=/var/www/hexabid/backend/venv/bin"
ExecStart=/var/www/hexabid/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start the service:

```bash
systemctl daemon-reload
systemctl start hexabid-backend
systemctl enable hexabid-backend
systemctl status hexabid-backend
```

---

## Service Configuration

### 1. GeM Scraper Configuration

Run the scraper configuration script:

```bash
chmod +x /root/configure_scraper.sh
./configure_scraper.sh
```

This will:
- Install Chrome/Chromium and ChromeDriver
- Configure GeM portal credentials
- Test the scraper (optional)

The scraper credentials are already set:
- Email: prashant.hexatech@gmail.com
- Password: Hexa@gem123

### 2. Email Alerts Configuration (When Available)

Edit `/var/www/hexabid/backend/.env`:

```bash
EMAIL_SERVICE_ENABLED=true
EMAIL_PROVIDER=sendgrid  # or ses, smtp
EMAIL_API_KEY=your_sendgrid_api_key
EMAIL_FROM_ADDRESS=noreply@hexabid.co.in
EMAIL_FROM_NAME=HexaBid ERP
```

Restart backend:
```bash
systemctl restart hexabid-backend
```

### 3. WhatsApp Alerts Configuration (When Available)

Edit `/var/www/hexabid/backend/.env`:

```bash
WHATSAPP_ENABLED=true
WHATSAPP_PROVIDER=twilio
WHATSAPP_ACCOUNT_SID=your_account_sid
WHATSAPP_AUTH_TOKEN=your_auth_token
WHATSAPP_FROM_NUMBER=+14155238886
```

Restart backend:
```bash
systemctl restart hexabid-backend
```

### 4. Payment Gateway Configuration (When Available)

For Razorpay (recommended for India):

```bash
PAYMENT_ENABLED=true
PAYMENT_PROVIDER=razorpay
PAYMENT_KEY_ID=rzp_live_xxxxx
PAYMENT_KEY_SECRET=your_secret_key
PAYMENT_WEBHOOK_SECRET=your_webhook_secret
```

Restart backend:
```bash
systemctl restart hexabid-backend
```

---

## SSL Certificate Setup

### Using Certbot (Let's Encrypt)

**Important**: Ensure DNS is pointing to the server before running this.

```bash
# Verify DNS is resolving correctly
nslookup app.hexabid.co.in

# Run certbot
certbot --nginx -d app.hexabid.co.in

# Follow the prompts:
# - Enter email: admin@hexabid.co.in
# - Agree to terms: Yes
# - Share email: Your choice
# - Redirect HTTP to HTTPS: Yes (recommended)
```

Certbot will:
- Obtain SSL certificate
- Automatically configure Nginx for HTTPS
- Setup auto-renewal

Test SSL:
```bash
# Check certificate
certbot certificates

# Test auto-renewal
certbot renew --dry-run
```

---

## Post-Deployment Tasks

### 1. Verify Services are Running

```bash
# Check backend
systemctl status hexabid-backend
curl http://localhost:8001/api/health

# Check Nginx
systemctl status nginx
curl http://localhost

# Check MongoDB
systemctl status mongod
mongosh --eval "db.version()"
```

### 2. Test Application Access

Open browser and navigate to:
- HTTP: http://app.hexabid.co.in (should redirect to HTTPS if SSL is configured)
- HTTPS: https://app.hexabid.co.in

### 3. Create Admin User

You can create an admin user via the registration page or using MongoDB:

```bash
mongosh
use hexabid_erp_production

db.users.insertOne({
  id: "admin-001",
  email: "admin@hexabid.co.in",
  password_hash: "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aqO6x8H4wqWK",  # Hash for: admin123
  full_name: "System Administrator",
  role: "admin",
  company_name: "HexaTech",
  status: "active",
  created_at: new Date().toISOString(),
  subscription_tier: "enterprise",
  subscription_status: "active"
})
```

**Default Admin Credentials** (change after first login):
- Email: admin@hexabid.co.in
- Password: admin123

### 4. Setup Automated Backups

Create backup directory:
```bash
mkdir -p /var/backups/hexabid
```

Create backup script `/root/backup_hexabid.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/hexabid"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup MongoDB
mongodump --db=hexabid_erp_production --out=$BACKUP_DIR/mongo_$DATE

# Backup uploaded files (if any)
tar -czf $BACKUP_DIR/files_$DATE.tar.gz /var/www/hexabid/backend/uploads/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "mongo_*" -mtime +7 -exec rm -rf {} \;
find $BACKUP_DIR -name "files_*" -mtime +7 -delete

echo "Backup completed: $DATE"
```

Make executable and add to cron:
```bash
chmod +x /root/backup_hexabid.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add line:
0 2 * * * /root/backup_hexabid.sh >> /var/log/hexabid/backup.log 2>&1
```

### 5. Configure Log Rotation

Create `/etc/logrotate.d/hexabid`:

```
/var/log/hexabid/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 root root
    sharedscripts
    postrotate
        systemctl reload hexabid-backend > /dev/null 2>&1 || true
    endscript
}
```

### 6. Setup Monitoring (Optional but Recommended)

Install basic monitoring:

```bash
# Install htop for system monitoring
apt-get install -y htop

# Setup log monitoring
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
journalctl -u hexabid-backend -f
```

For production, consider:
- Uptime monitoring (UptimeRobot, Pingdom)
- Application monitoring (New Relic, DataDog)
- Error tracking (Sentry)

---

## Troubleshooting

### Backend Not Starting

```bash
# Check service status
systemctl status hexabid-backend

# Check logs
journalctl -u hexabid-backend -n 50 --no-pager

# Common issues:
# 1. Port 8001 already in use
sudo lsof -i :8001
# Kill process if needed

# 2. Python dependencies missing
cd /var/www/hexabid/backend
source venv/bin/activate
pip install -r requirements.txt

# 3. Environment variables not set
cat .env
# Verify all required variables are present

# Restart service
systemctl restart hexabid-backend
```

### Frontend Not Loading

```bash
# Check Nginx status
systemctl status nginx

# Check Nginx error logs
tail -f /var/log/nginx/error.log

# Verify build exists
ls -la /var/www/hexabid/frontend/build

# Rebuild if needed
cd /var/www/hexabid/frontend
yarn build

# Test Nginx config
nginx -t

# Reload Nginx
systemctl reload nginx
```

### MongoDB Connection Issues

```bash
# Check MongoDB status
systemctl status mongod

# Check MongoDB logs
tail -f /var/log/mongodb/mongod.log

# Test connection
mongosh

# Restart MongoDB
systemctl restart mongod
```

### GeM Scraper Not Working

```bash
# Check ChromeDriver
chromedriver --version

# Reinstall if needed
apt-get install --reinstall chromium-browser chromium-chromedriver

# Test scraper manually
cd /var/www/hexabid/backend
source venv/bin/activate
python3 -c "from gem_scraper import GeMScraper; import asyncio; s=GeMScraper(); print('Scraper initialized')"

# Check GeM credentials
cat .env | grep GEM
```

### SSL Certificate Issues

```bash
# Check certificate status
certbot certificates

# Renew certificate
certbot renew

# If renewal fails, check DNS
nslookup app.hexabid.co.in

# Check if ports 80 and 443 are open
sudo ufw status
sudo netstat -tulpn | grep -E '(:80|:443)'
```

### Application Performance Issues

```bash
# Check system resources
htop

# Check disk space
df -h

# Check memory usage
free -h

# Check MongoDB performance
mongosh --eval "db.currentOp()"

# Optimize MongoDB
mongosh hexabid_erp_production --eval "db.tenders.createIndex({published_date: -1})"
mongosh hexabid_erp_production --eval "db.tenders.createIndex({status: 1, submission_deadline: 1})"
```

---

## Useful Commands

### Service Management

```bash
# Backend
systemctl start hexabid-backend
systemctl stop hexabid-backend
systemctl restart hexabid-backend
systemctl status hexabid-backend

# Nginx
systemctl reload nginx
systemctl restart nginx

# MongoDB
systemctl start mongod
systemctl stop mongod
systemctl restart mongod
```

### Log Viewing

```bash
# Backend logs
journalctl -u hexabid-backend -f
journalctl -u hexabid-backend -n 100 --no-pager

# Nginx access logs
tail -f /var/log/nginx/access.log

# Nginx error logs
tail -f /var/log/nginx/error.log

# MongoDB logs
tail -f /var/log/mongodb/mongod.log
```

### Database Operations

```bash
# Access MongoDB
mongosh

# Use production database
use hexabid_erp_production

# View collections
show collections

# Count tenders
db.tenders.countDocuments()

# View recent tenders
db.tenders.find().sort({created_at: -1}).limit(5)

# Create indexes
db.tenders.createIndex({tender_id: 1})
db.tenders.createIndex({status: 1})
db.users.createIndex({email: 1}, {unique: true})
```

---

## Additional Resources

- **GeM Portal**: https://gem.gov.in
- **HexaBid Documentation**: See README.md and technical documentation
- **MongoDB Documentation**: https://docs.mongodb.com
- **Nginx Documentation**: https://nginx.org/en/docs/
- **Let's Encrypt**: https://letsencrypt.org

---

## Support

For technical support or issues during deployment:
- Email: admin@hexabid.co.in
- Documentation: /app/HexaBid_Technical_Documentation_v3.md

---

**Deployment Guide Version**: 1.0  
**Last Updated**: October 2024  
**For**: HexaBid ERP Production Deployment
