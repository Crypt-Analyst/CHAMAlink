#!/bin/bash
# Automated database backup script for CHAMAlink
# Usage: ./backup.sh

set -e
BACKUP_DIR="$(dirname "$0")/../backups"
DATE=$(date +"%Y-%m-%d_%H-%M-%S")
DB_NAME="chamalink_db"  # Change to your actual DB name
DB_USER="chamalink_user"  # Change to your actual DB user

mkdir -p "$BACKUP_DIR"
FILENAME="$BACKUP_DIR/chamalink_backup_$DATE.sql.gz"

pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$FILENAME"

if [ $? -eq 0 ]; then
  echo "Backup successful: $FILENAME"
else
  echo "Backup failed!"
  exit 1
fi
