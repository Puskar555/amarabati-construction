-- Ammarabati v0.1 local primary database. Private PostgreSQL only.
CREATE TABLE IF NOT EXISTS users (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'customer' CHECK (role IN ('customer','regional_admin','super_admin')),
  region TEXT, totp_secret_enc TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS sessions (
  token_hash CHAR(64) PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  csrf_hash CHAR(64) NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL, revoked_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_sessions_user ON sessions(user_id);
CREATE TABLE IF NOT EXISTS categories (
  slug TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS products (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, slug TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL, category TEXT NOT NULL REFERENCES categories(slug),
  unit TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', specification TEXT NOT NULL DEFAULT '',
  image_key TEXT, published BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS material_rates (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  product_id BIGINT NOT NULL REFERENCES products(id),
  region TEXT NOT NULL, currency CHAR(3) NOT NULL DEFAULT 'NPR',
  unit_rate NUMERIC(16,2) NOT NULL CHECK (unit_rate > 0), note TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected')),
  proposed_by BIGINT NOT NULL REFERENCES users(id), approved_by BIGINT REFERENCES users(id),
  proposed_at TIMESTAMPTZ NOT NULL DEFAULT now(), approved_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_rates_lookup ON material_rates(product_id, region, approved_at DESC) WHERE status='approved';
CREATE TABLE IF NOT EXISTS consents (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id BIGINT REFERENCES users(id) ON DELETE SET NULL, visitor_ref CHAR(36),
  analytics BOOLEAN NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS activity_events (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  event_id TEXT NOT NULL UNIQUE, visitor_ref CHAR(36), user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  event_name TEXT NOT NULL, details JSONB NOT NULL DEFAULT '{}',
  region TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_events_time ON activity_events(created_at DESC);
CREATE INDEX IF NOT EXISTS ix_events_region ON activity_events(region, created_at DESC);
CREATE TABLE IF NOT EXISTS orders (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES users(id),
  delivery_region TEXT NOT NULL, notes TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'awaiting_payment_integration',
  total_amount NUMERIC(16,2), currency CHAR(3) NOT NULL DEFAULT 'NPR',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS order_lines (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  order_id BIGINT NOT NULL REFERENCES orders(id), product_id BIGINT NOT NULL REFERENCES products(id),
  quantity INTEGER NOT NULL CHECK(quantity>0), unit_rate NUMERIC(16,2),
  product_name_snapshot TEXT NOT NULL, line_total NUMERIC(16,2)
);
CREATE TABLE IF NOT EXISTS projects (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id), title TEXT NOT NULL,
  project_type TEXT NOT NULL CHECK(project_type IN ('residential','commercial')),
  municipality TEXT NOT NULL, width_m NUMERIC(12,2) NOT NULL, depth_m NUMERIC(12,2) NOT NULL,
  floors SMALLINT NOT NULL, requirements JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS audit_events (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  actor_id BIGINT REFERENCES users(id), action TEXT NOT NULL,
  subject_type TEXT NOT NULL, subject_id TEXT NOT NULL,
  info JSONB NOT NULL DEFAULT '{}', created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_audit_time ON audit_events(created_at DESC);
