#!/bin/bash

# HexaBid ERP - Backup Script
# This script creates a complete backup of the application including code and database

BACKUP_DIR="/backup/hexabid"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="hexabid_backup_${TIMESTAMP}.tar.gz"
DB_BACKUP_DIR="/tmp/hexabid_db_${TIMESTAMP}"

echo "=================================="
echo "HexaBid ERP Backup Script"
echo "=================================="
echo "Starting backup at $(date)"
echo ""

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

echo "[1/4] Backing up MongoDB database..."
mongodump --db hexabid_erp --out "${DB_BACKUP_DIR}"
if [ $? -eq 0 ]; then
    echo "  ✓ Database backup successful"
else
    echo "  ✗ Database backup failed"
    exit 1
fi

echo ""
echo "[2/4] Creating application backup..."
cd /app
tar -czf "${BACKUP_DIR}/${BACKUP_FILE}" \
    --exclude='node_modules' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='*.pyc' \
    --exclude='build' \
    backend/ \
    frontend/ \
    README.md \
    DEPLOYMENT_GUIDE.md

if [ $? -eq 0 ]; then
    echo "  ✓ Application backup successful"
else
    echo "  ✗ Application backup failed"
    exit 1
fi

echo ""
echo "[3/4] Adding database backup to archive..."
cd "${DB_BACKUP_DIR}/.."
tar -czf "${BACKUP_DIR}/hexabid_db_${TIMESTAMP}.tar.gz" "hexabid_db_${TIMESTAMP}"
if [ $? -eq 0 ]; then
    echo "  ✓ Database archive created"
    rm -rf "${DB_BACKUP_DIR}"
else
    echo "  ✗ Database archive failed"
fi

echo ""
echo "[4/4] Cleaning old backups (keeping last 7 days)..."
find "${BACKUP_DIR}" -name "hexabid_*" -type f -mtime +7 -delete
echo "  ✓ Cleanup complete"

echo ""
echo "=================================="
echo "Backup Complete!"
echo "=================================="
echo "Backup files created:"
echo "  - ${BACKUP_DIR}/${BACKUP_FILE}"
echo "  - ${BACKUP_DIR}/hexabid_db_${TIMESTAMP}.tar.gz"
echo ""
echo "Total size:"
du -sh "${BACKUP_DIR}/${BACKUP_FILE}"
du -sh "${BACKUP_DIR}/hexabid_db_${TIMESTAMP}.tar.gz"
echo ""
echo "Backup completed at $(date)"
echo ""
echo "To restore this backup:"
echo "  1. Extract application: tar -xzf ${BACKUP_FILE}"
echo "  2. Extract database: tar -xzf hexabid_db_${TIMESTAMP}.tar.gz"
echo "  3. Restore database: mongorestore hexabid_db_${TIMESTAMP}/"
echo "=================================="
