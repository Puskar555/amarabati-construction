#!/bin/sh
set -eu
mkdir -p backups
out="backups/amarabati_$(date -u +%Y%m%d_%H%M%S).dump"
docker compose exec -T db sh -c 'exec pg_dump -U amarabati_owner -d amarabati -Fc' > "$out"
chmod 600 "$out"
echo "Backup created: $out. Encrypt and move to separately protected storage; test restoration regularly."
