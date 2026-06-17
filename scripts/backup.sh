#!/bin/bash
# backup.sh — Respaldo automático de la base de datos
# Ejecutar: ./scripts/backup.sh
# Para backup automático diario, agregar cron:
#   0 6 * * * /home/aiks/mipresupuestoapp/scripts/backup.sh

set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/aiks/mipresupuestoapp/backups"
COMPOSE_DIR="/home/aiks/mipresupuestoapp"
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando backup..."

docker compose -f "$COMPOSE_DIR/docker-compose.yml" exec -T db pg_dump \
    -U finanzas_user \
    -d finanzas_hogar \
    --clean \
    --if-exists \
    --no-owner \
    --no-acl \
    --format=custom \
    --file "/backups/finanzas_hogar_$TIMESTAMP.dump"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup completado: backups/finanzas_hogar_$TIMESTAMP.dump"

# Limpiar backups antiguos
find "$BACKUP_DIR" -name "finanzas_hogar_*.dump" -type f -mtime +$RETENTION_DAYS -delete
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backups más antiguos de $RETENTION_DAYS días eliminados."

# Backup de .env
if [ -f "$COMPOSE_DIR/.env" ]; then
    cp "$COMPOSE_DIR/.env" "$BACKUP_DIR/env_backup_$TIMESTAMP.txt" 2>/dev/null || echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  No se pudo copiar .env (permisos), continuando..."
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup disponible localmente en: backups/finanzas_hogar_$TIMESTAMP.dump"
