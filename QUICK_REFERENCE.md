# HexaBid ERP - Quick Deployment Reference

## 🚀 Fast Deployment (15 Minutes)

### Step 1: Transfer Package
```bash
scp /app/hexabid-erp-deployment_v1.0.tar.gz root@66.116.197.150:/root/
```

### Step 2: Deploy
```bash
ssh root@66.116.197.150
# Password: Hexabid@666

cd /root
tar -xzf hexabid-erp-deployment_v1.0.tar.gz
cd hexabid-erp-deployment
chmod +x *.sh
./deploy.sh
```

### Step 3: Configure Scraper
```bash
./configure_scraper.sh
```

### Step 4: Access Application
```
https://app.hexabid.co.in
```

---

## 📋 Quick Access Credentials

### Server SSH
```
Host: 66.116.197.150
User: root
Pass: Hexabid@666
```

### AAPanel
```
URL: https://66.116.197.150:37711/
User: Hexabid
Pass: 6f1f4f74
```

### GeM Portal (Configured)
```
Email: prashant.hexatech@gmail.com
Pass: Hexa@gem123
```

---

## 🔧 Essential Commands

### Service Management
```bash
# Restart backend
systemctl restart hexabid-backend

# Reload Nginx
systemctl reload nginx

# Check status
systemctl status hexabid-backend nginx mongod
```

### View Logs
```bash
# Backend logs
journalctl -u hexabid-backend -f

# Nginx errors
tail -f /var/log/nginx/error.log

# MongoDB logs
tail -f /var/log/mongodb/mongod.log
```

### Database
```bash
# Access MongoDB
mongosh hexabid_erp_production

# Backup
mongodump --db=hexabid_erp_production --out=/var/backups/hexabid/backup_$(date +%Y%m%d)
```

---

## 📚 Documentation

1. **Quick Start:** `README_DEPLOYMENT.md`
2. **Full Guide:** `PRODUCTION_DEPLOYMENT_GUIDE.md`
3. **This Summary:** `DEPLOYMENT_SUMMARY.md`
4. **Technical Docs:** `HexaBid_Technical_Documentation_v3.md`

---

## ✅ Verification Checklist

After deployment:

```bash
# 1. Check services
systemctl status hexabid-backend nginx mongod

# 2. Test backend
curl http://localhost:8001/api/health

# 3. Test frontend
curl http://localhost

# 4. Check logs
journalctl -u hexabid-backend -n 20
```

Then open browser: https://app.hexabid.co.in

---

## 🆘 Common Issues

### Backend Not Starting
```bash
journalctl -u hexabid-backend -n 50
cd /var/www/hexabid/backend
source venv/bin/activate
pip install -r requirements.txt
systemctl restart hexabid-backend
```

### Frontend Not Loading
```bash
cd /var/www/hexabid/frontend
yarn build
systemctl reload nginx
```

### SSL Issues
```bash
certbot --nginx -d app.hexabid.co.in
```

---

## 📦 Package Contents

```
hexabid-erp-deployment_v1.0.tar.gz (296KB)
├── backend/          # FastAPI backend
├── frontend/         # React frontend
├── deploy.sh         # Main deployment
├── configure_scraper.sh
└── Documentation files
```

---

## 🎯 Post-Deployment

1. Setup SSL: `certbot --nginx -d app.hexabid.co.in`
2. Create admin user via registration
3. Test GeM scraper
4. Configure email/WhatsApp/payment when keys available

---

## 📞 Need Help?

Check `PRODUCTION_DEPLOYMENT_GUIDE.md` section:
- Pre-Deployment Checklist
- Troubleshooting
- Service Configuration

---

**Deployment Time:** ~15 minutes  
**Status:** Ready to Deploy  
**Version:** 1.0
