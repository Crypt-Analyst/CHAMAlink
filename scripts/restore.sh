#!/bin/bash
# Restore database from backup
# Usage: ./restore.sh <backup_file.sql.gz>

set -e
DB_NAME="chamalink_db"  # Change to your actual DB name
DB_USER="chamalink_user"  # Change to your actual DB user

if [ $# -ne 1 ]; then
  echo "Usage: $0 <backup_file.sql.gz>"
  exit 1
fi

BACKUP_FILE="$1"
gunzip -c "$BACKUP_FILE" | psql -U "$DB_USER" "$DB_NAME"

if [ $? -eq 0 ]; then
  echo "Restore successful from: $BACKUP_FILE"
else
  echo "Restore failed!"
  exit 1
fi
