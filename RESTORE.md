# Disaster Recovery: Database Restore Guide

To restore your database from a backup:

1. Place the desired backup file (e.g., `chamalink_backup_YYYY-MM-DD_HH-MM-SS.sql.gz`) in the `backups/` directory.
2. Run the restore script:

```sh
./scripts/restore.sh backups/chamalink_backup_YYYY-MM-DD_HH-MM-SS.sql.gz
```

- Make sure to update `DB_NAME` and `DB_USER` in `restore.sh` to match your environment.
- The script will decompress and restore the backup to your database.
- Always test restores in a staging environment before production use.
