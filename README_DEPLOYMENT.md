# HexaBid ERP - VPN Deployment Package

## Quick Start Guide

This package contains everything needed to deploy HexaBid ERP on your VPN server at **app.hexabid.co.in**.

### Your Deployment Credentials

**Server Access:**
- Server IP: `66.116.197.150`
- SSH User: `root`
- SSH Password: `Hexabid@666`

**AAPanel:**
- URL: https://66.116.197.150:37711/
- Username: `Hexabid`
- Password: `6f1f4f74`

**GeM Portal:**
- Email: `prashant.hexatech@gmail.com`
- Password: `Hexa@gem123`

---

## Deployment Methods

### Option 1: Automated Deployment (Recommended)

```bash
# 1. SSH into your server
ssh root@66.116.197.150

# 2. Transfer this package to server
# (On your local machine)
scp -r hexabid-erp-deployment root@66.116.197.150:/root/

# 3. On server, navigate to package
cd /root/hexabid-erp-deployment

# 4. Make scripts executable
chmod +x *.sh

# 5. Run deployment
./deploy.sh
```

The deployment script will automatically:
- ✅ Install all system dependencies
- ✅ Setup MongoDB database
- ✅ Deploy backend API
- ✅ Build and deploy frontend
- ✅ Configure Nginx web server
- ✅ Setup SSL certificate (optional)
- ✅ Create systemd services
- ✅ Configure firewall

**Total deployment time: ~10-15 minutes**

### Option 2: Manual Deployment

If you prefer step-by-step control, follow the comprehensive guide:
📖 **See:** [PRODUCTION_DEPLOYMENT_GUIDE.md](./PRODUCTION_DEPLOYMENT_GUIDE.md)

---

## Post-Deployment Configuration

After deployment, configure additional services:

### 1. GeM Scraper (Immediate)

```bash
./configure_scraper.sh
```

This configures the GeM portal scraper with your credentials.

### 2. Email Alerts (When API Keys Available)

Edit `/var/www/hexabid/backend/.env`:
```bash
EMAIL_SERVICE_ENABLED=true
EMAIL_API_KEY=your_api_key
```

### 3. WhatsApp Alerts (When API Keys Available)

Edit `/var/www/hexabid/backend/.env`:
```bash
WHATSAPP_ENABLED=true
WHATSAPP_ACCOUNT_SID=your_sid
WHATSAPP_AUTH_TOKEN=your_token
```

### 4. Payment Gateway (When Credentials Available)

Edit `/var/www/hexabid/backend/.env`:
```bash
PAYMENT_ENABLED=true
PAYMENT_KEY_ID=your_key
PAYMENT_KEY_SECRET=your_secret
```

---

## Package Contents

```
hexabid-erp-deployment/
├── backend/                    # FastAPI backend application
│   ├── server.py              # Main API server
│   ├── gem_scraper.py         # GeM portal scraper
│   ├── document_generator.py  # Document generation module
│   ├── requirements.txt       # Python dependencies
│   ├── .env.production        # Production environment template
│   └── ...
│
├── frontend/                   # React frontend application
│   ├── src/                   # Source code
│   ├── public/                # Static assets
│   ├── package.json           # Node dependencies
│   ├── .env.production        # Frontend environment template
│   └── ...
│
├── deploy.sh                   # 🚀 Main deployment script
├── configure_scraper.sh        # GeM scraper configuration
│
├── README_DEPLOYMENT.md        # ← You are here
├── PRODUCTION_DEPLOYMENT_GUIDE.md  # Detailed deployment guide
├── HexaBid_Technical_Documentation_v3.md  # Technical documentation
└── COMPLETE_SYSTEM_SUMMARY.md  # System overview

```

---

## Application Features

### Core Modules (15+)
1. ✅ User Authentication & Authorization
2. ✅ Dashboard with Analytics
3. ✅ Tender Search & Management
4. ✅ AI Tender Analysis
5. ✅ Technical Review Assistant
6. ✅ Product Suggestions
7. ✅ Competitor Analysis
8. ✅ Price Analyzer
9. ✅ Win Prediction
10. ✅ CRM System
11. ✅ Reports & Export
12. ✅ AI Chat Assistant
13. ✅ Notifications Center
14. ✅ Support System
15. ✅ Admin Panel
16. ✅ Analytics Dashboard
17. ✅ Subscription Management
18. ✅ Document Management
19. ✅ Document Preparation (BOQ, etc.)

### Data Sources
- 🌐 Real-time GeM portal data
- 📊 Historical tender analytics
- 🏢 Integration-ready for MSME, GST, PAN APIs

---

## Verification Steps

After deployment, verify everything is working:

### 1. Check Services

```bash
# Backend API
systemctl status hexabid-backend
curl http://localhost:8001/api/health

# Nginx
systemctl status nginx

# MongoDB
systemctl status mongod
```

### 2. Access Application

Open browser:
- **URL:** https://app.hexabid.co.in
- **Expected:** Login page loads successfully

### 3. Test GeM Scraper

```bash
cd /var/www/hexabid/backend
source venv/bin/activate
python3 -c "from gem_scraper import GeMScraper; print('✓ Scraper OK')"
```

### 4. Check Logs

```bash
# Backend logs
journalctl -u hexabid-backend -n 50

# Nginx logs
tail -50 /var/log/nginx/error.log
```

---

## Common Post-Deployment Tasks

### Update Application

```bash
# Stop services
systemctl stop hexabid-backend

# Update code
cd /var/www/hexabid/backend
git pull  # if using git
# OR copy new files

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Rebuild frontend
cd /var/www/hexabid/frontend
yarn install
yarn build

# Restart services
systemctl start hexabid-backend
systemctl reload nginx
```

### View Application Logs

```bash
# Real-time backend logs
journalctl -u hexabid-backend -f

# Real-time Nginx access logs
tail -f /var/log/nginx/access.log

# Real-time Nginx error logs
tail -f /var/log/nginx/error.log
```

### Restart Services

```bash
# Restart backend
systemctl restart hexabid-backend

# Reload Nginx (no downtime)
systemctl reload nginx

# Restart Nginx (brief downtime)
systemctl restart nginx

# Restart MongoDB
systemctl restart mongod
```

### Database Backup

```bash
# Manual backup
mongodump --db=hexabid_erp_production --out=/var/backups/hexabid/manual_backup_$(date +%Y%m%d)

# Automated backups are configured via cron (see deployment guide)
```

---

## Troubleshooting

### Issue: Backend not starting

```bash
# Check logs
journalctl -u hexabid-backend -n 100 --no-pager

# Common fix: Reinstall dependencies
cd /var/www/hexabid/backend
source venv/bin/activate
pip install -r requirements.txt
systemctl restart hexabid-backend
```

### Issue: Frontend shows blank page

```bash
# Rebuild frontend
cd /var/www/hexabid/frontend
yarn build
systemctl reload nginx
```

### Issue: SSL certificate error

```bash
# Ensure DNS is pointing to server
nslookup app.hexabid.co.in

# Run certbot
certbot --nginx -d app.hexabid.co.in
```

### Issue: GeM scraper not working

```bash
# Verify ChromeDriver
chromedriver --version

# Reinstall
apt-get install --reinstall chromium-browser chromium-chromedriver

# Reconfigure
./configure_scraper.sh
```

**For detailed troubleshooting**, see [PRODUCTION_DEPLOYMENT_GUIDE.md](./PRODUCTION_DEPLOYMENT_GUIDE.md#troubleshooting)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│            Users (Browser)                      │
│         https://app.hexabid.co.in               │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│              Nginx (Port 80/443)                │
│  - Serves React frontend (static files)         │
│  - Proxies /api/* to backend                    │
│  - SSL termination                              │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│         FastAPI Backend (Port 8001)             │
│  - REST API endpoints                           │
│  - Authentication & Authorization               │
│  - Business logic                               │
│  - GeM scraper integration                      │
│  - AI/LLM processing                            │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│         MongoDB (Port 27017)                    │
│  - User data                                    │
│  - Tender information                           │
│  - Analytics data                               │
│  - Documents metadata                           │
└─────────────────────────────────────────────────┘
```

---

## Technology Stack

### Backend
- **Framework:** FastAPI (Python)
- **Database:** MongoDB
- **Scraping:** Selenium + BeautifulSoup4
- **AI Guidance:** HexaBid deterministic heuristics
- **Authentication:** JWT

### Frontend
- **Framework:** React 18
- **UI Components:** Shadcn/UI
- **Styling:** Tailwind CSS
- **State Management:** React Context
- **Routing:** React Router v6

### Infrastructure
- **Web Server:** Nginx
- **Process Manager:** systemd
- **SSL:** Let's Encrypt (Certbot)
- **OS:** Ubuntu 20.04+

---

## Security Considerations

### Already Configured
- ✅ JWT-based authentication
- ✅ Password hashing (bcrypt)
- ✅ CORS configuration
- ✅ Environment variable protection
- ✅ HTTPS (after SSL setup)

### Recommended Additional Steps
1. **Change default JWT secret** in `/var/www/hexabid/backend/.env`
2. **Configure firewall** (UFW) to only allow ports 22, 80, 443
3. **Setup MongoDB authentication** for production
4. **Regular security updates**: `apt-get update && apt-get upgrade`
5. **Configure rate limiting** in Nginx
6. **Setup intrusion detection** (fail2ban)

---

## Support & Documentation

### Documentation Files
- 📘 **Deployment Guide:** [PRODUCTION_DEPLOYMENT_GUIDE.md](./PRODUCTION_DEPLOYMENT_GUIDE.md)
- 📗 **Technical Docs:** [HexaBid_Technical_Documentation_v3.md](./HexaBid_Technical_Documentation_v3.md)
- 📙 **System Summary:** [COMPLETE_SYSTEM_SUMMARY.md](./COMPLETE_SYSTEM_SUMMARY.md)

### Quick Links
- **GeM Portal:** https://gem.gov.in
- **MongoDB Docs:** https://docs.mongodb.com
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **React Docs:** https://react.dev

### Contact
- **Email:** admin@hexabid.co.in
- **Project Repository:** github.com/hexatechpl

---

## Maintenance Schedule

### Daily
- ✅ Automated database backups (2:00 AM)
- ✅ Log rotation
- ✅ GeM scraper runs (configurable)

### Weekly
- 📊 Review application logs
- 📈 Check system resources (CPU, memory, disk)
- 🔍 Review security logs

### Monthly
- 🔄 System updates (`apt-get update && apt-get upgrade`)
- 🔐 SSL certificate auto-renewal check
- 💾 Verify backup integrity
- 📊 Performance optimization

---

## Next Steps After Deployment

1. ✅ **Verify deployment** - Check all services are running
2. ✅ **Configure SSL** - Run certbot for HTTPS
3. ✅ **Setup GeM scraper** - Run configure_scraper.sh
4. ✅ **Create admin user** - First login credentials
5. ⏳ **Configure email service** - When API keys available
6. ⏳ **Configure WhatsApp alerts** - When API keys available
7. ⏳ **Setup payment gateway** - When credentials available
8. ✅ **Test all features** - Comprehensive application testing
9. ✅ **Setup monitoring** - Uptime and performance monitoring
10. ✅ **Train users** - User onboarding and training

---

## License & Credits

**HexaBid ERP** - AI-Powered Tender Bidding System  
Developed for Government Contractors and Suppliers  
© 2024 HexaTech. All rights reserved.

---

**Ready to Deploy?** 🚀

1. SSH into server: `ssh root@66.116.197.150`
2. Upload this package
3. Run: `./deploy.sh`
4. Access: https://app.hexabid.co.in

**Deployment complete in ~15 minutes!**

For support: admin@hexabid.co.in
