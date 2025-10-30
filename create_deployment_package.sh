#!/bin/bash

#############################################
# HexaBid ERP - Create Deployment Package
# Creates a zip file ready for VPN deployment
#############################################

set -e

echo "========================================"
echo "Creating HexaBid Deployment Package"
echo "========================================"

# Package details
PACKAGE_NAME="hexabid-erp-deployment"
PACKAGE_VERSION="v1.0"
OUTPUT_DIR="/tmp/$PACKAGE_NAME"
ZIP_FILE="/app/${PACKAGE_NAME}_${PACKAGE_VERSION}.tar.gz"

# Create temporary directory
echo "[INFO] Creating package directory..."
rm -rf $OUTPUT_DIR
mkdir -p $OUTPUT_DIR

# Copy backend files
echo "[INFO] Copying backend files..."
mkdir -p $OUTPUT_DIR/backend
cp -r /app/backend/* $OUTPUT_DIR/backend/ 2>/dev/null || true

# Exclude unnecessary files from backend
rm -rf $OUTPUT_DIR/backend/__pycache__
rm -rf $OUTPUT_DIR/backend/.pytest_cache
rm -rf $OUTPUT_DIR/backend/venv
rm -f $OUTPUT_DIR/backend/*.pyc

# Copy frontend files
echo "[INFO] Copying frontend files..."
mkdir -p $OUTPUT_DIR/frontend
cp -r /app/frontend/* $OUTPUT_DIR/frontend/ 2>/dev/null || true

# Exclude unnecessary files from frontend
rm -rf $OUTPUT_DIR/frontend/node_modules
rm -rf $OUTPUT_DIR/frontend/build
rm -rf $OUTPUT_DIR/frontend/.cache

# Copy deployment scripts
echo "[INFO] Copying deployment scripts..."
cp /app/deploy.sh $OUTPUT_DIR/
cp /app/configure_scraper.sh $OUTPUT_DIR/

# Copy documentation
echo "[INFO] Copying documentation..."
cp /app/README_DEPLOYMENT.md $OUTPUT_DIR/
cp /app/PRODUCTION_DEPLOYMENT_GUIDE.md $OUTPUT_DIR/
cp /app/HexaBid_Technical_Documentation_v3.md $OUTPUT_DIR/ 2>/dev/null || true
cp /app/COMPLETE_SYSTEM_SUMMARY.md $OUTPUT_DIR/ 2>/dev/null || true

# Create package info file
echo "[INFO] Creating package info..."
cat > $OUTPUT_DIR/PACKAGE_INFO.txt <<EOF
HexaBid ERP - Deployment Package
================================

Package Version: $PACKAGE_VERSION
Created: $(date)
Platform: Ubuntu 20.04+ / VPN Server

Contents:
---------
- Backend API (FastAPI + Python)
- Frontend (React)
- Deployment scripts
- Configuration scripts
- Complete documentation

Server Details:
--------------
IP: 66.116.197.150
Domain: app.hexabid.co.in
User: root
Password: Hexabid@666

Quick Start:
-----------
1. Extract this package on server
2. cd hexabid-erp-deployment
3. chmod +x *.sh
4. ./deploy.sh

For detailed instructions, see README_DEPLOYMENT.md

Support: admin@hexabid.co.in
EOF

# Create directory structure info
echo "[INFO] Creating directory structure..."
cat > $OUTPUT_DIR/STRUCTURE.txt <<'EOF'
hexabid-erp-deployment/
│
├── backend/                    # Backend application
│   ├── server.py              # Main FastAPI server
│   ├── gem_scraper.py         # GeM portal scraper
│   ├── document_generator.py  # Document generation
│   ├── requirements.txt       # Python dependencies
│   ├── .env.production        # Production environment template
│   └── ...
│
├── frontend/                   # Frontend application
│   ├── src/                   # React source code
│   │   ├── App.js
│   │   ├── pages/
│   │   └── components/
│   ├── public/                # Static files
│   ├── package.json           # Node dependencies
│   ├── .env.production        # Frontend environment
│   └── ...
│
├── deploy.sh                   # 🚀 Main deployment script
├── configure_scraper.sh        # GeM scraper setup
│
├── README_DEPLOYMENT.md        # Quick start guide
├── PRODUCTION_DEPLOYMENT_GUIDE.md  # Detailed guide
├── HexaBid_Technical_Documentation_v3.md
├── COMPLETE_SYSTEM_SUMMARY.md
│
├── PACKAGE_INFO.txt           # Package information
└── STRUCTURE.txt              # This file
EOF

# Make scripts executable
chmod +x $OUTPUT_DIR/*.sh

# Create compressed archive
echo "[INFO] Creating compressed archive..."
cd /tmp
tar -czf $ZIP_FILE $PACKAGE_NAME/

# Get file size
FILE_SIZE=$(du -h $ZIP_FILE | cut -f1)

# Cleanup temp directory
rm -rf $OUTPUT_DIR

echo ""
echo "========================================"
echo "Package Created Successfully!"
echo "========================================"
echo ""
echo "Package: $ZIP_FILE"
echo "Size: $FILE_SIZE"
echo ""
echo "To transfer to server:"
echo "  scp $ZIP_FILE root@66.116.197.150:/root/"
echo ""
echo "On server, extract with:"
echo "  cd /root"
echo "  tar -xzf $(basename $ZIP_FILE)"
echo "  cd $PACKAGE_NAME"
echo "  ./deploy.sh"
echo ""
echo "Package contents:"
ls -lh $ZIP_FILE
echo ""

exit 0
