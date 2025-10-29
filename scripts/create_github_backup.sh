#!/bin/bash

# HexaBid ERP - GitHub Export & Zip Backup Script
# This creates a clean export ready for GitHub and a zip backup

echo "==================================="
echo "HexaBid ERP - GitHub Export Script"
echo "==================================="
echo ""

# Configuration
PROJECT_DIR="/app"
EXPORT_DIR="/tmp/hexabid-export"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ZIP_BACKUP="/tmp/hexabid_source_backup_${TIMESTAMP}.zip"

# Clean up old export if exists
if [ -d "${EXPORT_DIR}" ]; then
    echo "[1/5] Cleaning old export directory..."
    rm -rf "${EXPORT_DIR}"
fi

echo "[1/5] Creating export directory..."
mkdir -p "${EXPORT_DIR}"

echo "[2/5] Copying project files..."
cd "${PROJECT_DIR}"

# Copy backend files
mkdir -p "${EXPORT_DIR}/backend"
cp -r backend/*.py "${EXPORT_DIR}/backend/" 2>/dev/null
cp backend/requirements.txt "${EXPORT_DIR}/backend/"
cp backend/.env.example "${EXPORT_DIR}/backend/" 2>/dev/null || cp backend/.env "${EXPORT_DIR}/backend/.env.example"

# Copy frontend files
mkdir -p "${EXPORT_DIR}/frontend/src"
mkdir -p "${EXPORT_DIR}/frontend/public"

# Copy all frontend source files
cp -r frontend/src/* "${EXPORT_DIR}/frontend/src/" 2>/dev/null
cp -r frontend/public/* "${EXPORT_DIR}/frontend/public/" 2>/dev/null
cp frontend/package.json "${EXPORT_DIR}/frontend/"
cp frontend/tailwind.config.js "${EXPORT_DIR}/frontend/" 2>/dev/null
cp frontend/postcss.config.js "${EXPORT_DIR}/frontend/" 2>/dev/null
cp frontend/craco.config.js "${EXPORT_DIR}/frontend/" 2>/dev/null
cp frontend/.env.example "${EXPORT_DIR}/frontend/" 2>/dev/null || cp frontend/.env "${EXPORT_DIR}/frontend/.env.example"

# Copy documentation
cp README.md "${EXPORT_DIR}/"
cp DEPLOYMENT_GUIDE.md "${EXPORT_DIR}/"

# Copy scripts
mkdir -p "${EXPORT_DIR}/scripts"
cp scripts/*.sh "${EXPORT_DIR}/scripts/" 2>/dev/null

echo "  ✓ Files copied successfully"

echo "[3/5] Creating .gitignore..."
cat > "${EXPORT_DIR}/.gitignore" << 'EOF'
# Dependencies
node_modules/
venv/
__pycache__/
*.pyc
*.pyo
*.pyd

# Environment variables
.env
.env.local
.env.production

# Build outputs
build/
dist/
*.egg-info/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Testing
coverage/
.pytest_cache/

# Backup files
*.bak
*.backup
EOF

echo "[4/5] Creating GitHub README..."
cat > "${EXPORT_DIR}/GITHUB_SETUP.md" << 'EOF'
# GitHub Setup Guide

## Initial Setup

1. Create a new repository on GitHub:
   - Repository name: `hexabid-erp`
   - Visibility: Private (recommended) or Public
   - Don't initialize with README (we already have one)

2. Link and push code:
```bash
cd /path/to/hexabid-export
git init
git add .
git commit -m "Initial commit - HexaBid ERP v3.0"
git branch -M main
git remote add origin https://github.com/hexatechpl/hexabid-erp.git
git push -u origin main
```

## Environment Variables

Before deploying, create `.env` files from `.env.example`:

**Backend:**
```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your values
```

**Frontend:**
```bash
cp frontend/.env.example frontend/.env
# Edit frontend/.env with your values
```

## Quick Clone & Deploy

To clone and deploy on your VPN:

```bash
# Clone repository
git clone https://github.com/hexatechpl/hexabid-erp.git
cd hexabid-erp

# Follow DEPLOYMENT_GUIDE.md for complete setup
```

## Updating from GitHub

```bash
cd /var/www/hexabid-erp
git pull origin main

# Restart services
sudo systemctl restart hexabid-backend
sudo systemctl reload nginx
```
EOF

echo "[5/5] Creating zip backup..."
cd /tmp
zip -r "${ZIP_BACKUP}" hexabid-export/ -q
BACKUP_SIZE=$(du -h "${ZIP_BACKUP}" | cut -f1)

echo ""
echo "==================================="
echo "Export Complete!"
echo "==================================="
echo ""
echo "Export directory: ${EXPORT_DIR}"
echo "Zip backup: ${ZIP_BACKUP}"
echo "Backup size: ${BACKUP_SIZE}"
echo ""
echo "Next steps:"
echo "1. Review files in: ${EXPORT_DIR}"
echo "2. Push to GitHub:"
echo "   cd ${EXPORT_DIR}"
echo "   git init"
echo "   git add ."
echo "   git commit -m 'Initial commit'"
echo "   git remote add origin https://github.com/hexatechpl/hexabid-erp.git"
echo "   git push -u origin main"
echo ""
echo "3. Download zip backup:"
echo "   The source code backup is available at: ${ZIP_BACKUP}"
echo ""
echo "==================================="
