-- API app role can read/write app data but cannot create/drop database objects.
GRANT CONNECT ON DATABASE amarabati TO amarabati_app;
GRANT USAGE ON SCHEMA public TO amarabati_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO amarabati_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO amarabati_app;
-- Make audit entries append-only for the runtime DB role.
REVOKE UPDATE, DELETE ON audit_events FROM amarabati_app;
ALTER DEFAULT PRIVILEGES FOR ROLE amarabati_owner IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO amarabati_app;
ALTER DEFAULT PRIVILEGES FOR ROLE amarabati_owner IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO amarabati_app;
