#!/bin/sh
set -eu
# Runs only when PostgreSQL creates a fresh, empty data volume.
# Owner account creates a separate non-superuser runtime identity.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -v app_password="$APP_DB_PASSWORD" <<'SQL'
CREATE ROLE amarabati_app LOGIN PASSWORD :'app_password' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
SQL
