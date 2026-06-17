#!/bin/bash
# restore.sh — Restaurar base de datos desde un backup
# Uso: ./scripts/restore.sh backups/finanzas_hogar_20260616_120000.dump

set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Uso: $0 <archivo_backup.dump>"
    echo "Ej:  $0 backups/finanzas_hogar_20260617_060000.dump"
    exit 1
fi

BACKUP_FILE="$1"
COMPOSE_DIR="/home/aiks/mipresupuestoapp"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: No se encuentra el archivo $BACKUP_FILE"
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Restaurando desde $BACKUP_FILE..."

echo "⚠️  Se restaurará la base de datos. Los datos actuales se perderán."
read -p "¿Continuar? (s/N): " CONFIRM
if [ "$CONFIRM" != "s" ] && [ "$CONFIRM" != "S" ]; then
    echo "Restauración cancelada."
    exit 0
fi

docker compose -f "$COMPOSE_DIR/docker-compose.yml" exec -T db pg_restore \
    -U finanzas_user \
    -d finanzas_hogar \
    --clean \
    --if-exists \
    --no-owner \
    --no-acl \
    < "$BACKUP_FILE"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Restauración completada."
