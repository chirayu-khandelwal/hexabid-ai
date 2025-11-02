# HexaBid ERP - Deployment Guide for VPN Hosting

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Prerequisites](#prerequisites)
3. [Installation Steps](#installation-steps)
4. [Configuration](#configuration)
5. [Running the Application](#running-the-application)
6. [Production Deployment](#production-deployment)
7. [Troubleshooting](#troubleshooting)

---

## System Requirements

- **OS**: AlmaLinux / CentOS / Ubuntu 20.04+
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: Minimum 20GB
- **CPU**: 2+ cores recommended
- **Python**: 3.11+
- **Node.js**: 18+ (with yarn)
- **MongoDB**: 5.0+

---

## Prerequisites

### 1. Install System Dependencies

#### For AlmaLinux/CentOS:
```bash
sudo dnf update -y
sudo dnf install -y python3.11 python3.11-pip nodejs mongodb-org git nginx
sudo dnf install -y npm
sudo npm install -g yarn
```

#### For Ubuntu:
```bash
sudo apt update
sudo apt install -y python3.11 python3.11-pip nodejs npm mongodb git nginx
sudo npm install -g yarn
```

### 2. Install MongoDB
```bash
# Start MongoDB service
sudo systemctl start mongodb
sudo systemctl enable mongodb

# Verify MongoDB is running
sudo systemctl status mongodb
```

---

## Installation Steps

### Step 1: Clone the Repository

```bash
# Navigate to your web directory
cd /var/www

# Clone from GitHub
git clone https://github.com/hexatechpl/hexabid-erp.git
cd hexabid-erp
```

### Step 2: Backend Setup

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Frontend Setup

```bash
cd ../frontend

# Install Node dependencies
yarn install
```

---

## Configuration

### 1. Backend Configuration

Edit `/var/www/hexabid-erp/backend/.env`:

```env
# MongoDB Configuration
MONGO_URL="mongodb://localhost:27017"
DB_NAME="hexabid_erp"

# Security
JWT_SECRET_KEY="your-super-secret-jwt-key-change-this-in-production"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# CORS (Update with your domain)
CORS_ORIGINS="https://app.hexabid.co.in,http://localhost:3000"

# AI Assistant configuration
AI_ASSISTANT_NAME="HexaBid Assistant"
```

**Important**: Change `JWT_SECRET_KEY` to a strong random value in production!

### 2. Frontend Configuration

Edit `/var/www/hexabid-erp/frontend/.env`:

```env
# Backend API URL (Update with your domain)
REACT_APP_BACKEND_URL=https://app.hexabid.co.in

# Optional settings
WDS_SOCKET_PORT=443
REACT_APP_ENABLE_VISUAL_EDITS=false
ENABLE_HEALTH_CHECK=false
```

---

## Running the Application

### Development Mode

#### Terminal 1 - Backend:
```bash
cd /var/www/hexabid-erp/backend
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

#### Terminal 2 - Frontend:
```bash
cd /var/www/hexabid-erp/frontend
yarn start
```

Access the application at `http://localhost:3000`

---

## Production Deployment

### Step 1: Build Frontend

```bash
cd /var/www/hexabid-erp/frontend
yarn build
```

This creates optimized production files in the `build/` directory.

### Step 2: Setup Nginx

Create Nginx configuration file:

```bash
sudo nano /etc/nginx/sites-available/hexabid
```

Add the following configuration:

```nginx
server {
    listen 80;
    server_name app.hexabid.co.in;

    # Frontend - Serve React build
    location / {
        root /var/www/hexabid-erp/frontend/build;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/hexabid /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 3: Setup Systemd Service for Backend

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/hexabid-backend.service
```

Add the following:

```ini
[Unit]
Description=HexaBid ERP Backend API
After=network.target mongodb.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/hexabid-erp/backend
Environment="PATH=/var/www/hexabid-erp/backend/venv/bin"
ExecStart=/var/www/hexabid-erp/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable hexabid-backend
sudo systemctl start hexabid-backend
sudo systemctl status hexabid-backend
```

### Step 4: Setup SSL with Let's Encrypt (Optional but Recommended)

```bash
sudo dnf install -y certbot python3-certbot-nginx
sudo certbot --nginx -d app.hexabid.co.in
```

Follow the prompts to setup SSL certificate.

---

## Verification

### 1. Check Services Status

```bash
# Check MongoDB
sudo systemctl status mongodb

# Check Backend
sudo systemctl status hexabid-backend

# Check Nginx
sudo systemctl status nginx
```

### 2. Test API Endpoints

```bash
# Test backend health
curl http://localhost:8001/api/

# Test from domain
curl https://app.hexabid.co.in/api/
```

### 3. Access Application

Open your browser and navigate to:
- **Production**: `https://app.hexabid.co.in`
- **Development**: `http://localhost:3000`

---

## Default Login Credentials

**Create your first account** by registering at the login page:
- Navigate to the Register tab
- Fill in your details
- Select your role (Contractor, Vendor, OEM, or Consultant)
- Click "Create Account"

---

## Troubleshooting

### Backend not starting?

Check logs:
```bash
sudo journalctl -u hexabid-backend -f
```

Common issues:
- Port 8001 already in use: Change port in systemd service
- MongoDB connection failed: Ensure MongoDB is running
- Missing dependencies: Reinstall requirements.txt

### Frontend build failing?

```bash
cd frontend
rm -rf node_modules
yarn install
yarn build
```

### Database connection issues?

```bash
# Check MongoDB status
sudo systemctl status mongodb

# Restart MongoDB
sudo systemctl restart mongodb

# Check MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log
```

### Nginx errors?

```bash
# Check Nginx configuration
sudo nginx -t

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log

# Restart Nginx
sudo systemctl restart nginx
```

---

## File Permissions

Ensure proper ownership:

```bash
sudo chown -R www-data:www-data /var/www/hexabid-erp
sudo chmod -R 755 /var/www/hexabid-erp
```

---

## Monitoring and Maintenance

### Check Application Logs

**Backend logs:**
```bash
sudo journalctl -u hexabid-backend -f
```

**Nginx access logs:**
```bash
sudo tail -f /var/log/nginx/access.log
```

**MongoDB logs:**
```bash
sudo tail -f /var/log/mongodb/mongod.log
```

### Backup Database

```bash
# Backup MongoDB
mongodump --db hexabid_erp --out /backup/hexabid-$(date +%Y%m%d)

# Restore MongoDB
mongorestore --db hexabid_erp /backup/hexabid-20250101/hexabid_erp
```

---

## Updating the Application

```bash
# Pull latest changes
cd /var/www/hexabid-erp
git pull origin main

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart hexabid-backend

# Update frontend
cd ../frontend
yarn install
yarn build
sudo systemctl reload nginx
```

---

## Security Checklist

- [ ] Changed JWT_SECRET_KEY in production
- [ ] Setup SSL certificate with Let's Encrypt
- [ ] Configured firewall (UFW/firewalld)
- [ ] MongoDB authentication enabled
- [ ] Regular backups scheduled
- [ ] Updated CORS_ORIGINS with actual domain
- [ ] Nginx security headers configured
- [ ] File permissions properly set

---

## Support

For issues or questions:
- **GitHub Issues**: https://github.com/hexatechpl/hexabid-erp/issues
- **Email**: support@hexabid.co.in
- **Documentation**: https://docs.hexabid.co.in

---

## API Integration Notes

### GeM API Integration
Currently using mock data. To integrate real GeM API:
1. Obtain API credentials from GeM portal
2. Update backend/server.py `generate_mock_tenders()` function
3. Add GeM API credentials to .env file

### MSME, GST, PAN, Aadhaar APIs
Currently using mock verification. For production:
1. Register with respective government portals
2. Obtain API keys
3. Update verification endpoints in backend/server.py

---

**Last Updated**: January 2025
**Version**: 3.0
