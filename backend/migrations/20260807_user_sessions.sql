CREATE TABLE IF NOT EXISTS user_sessions (
  id BIGSERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  jti VARCHAR(64) NOT NULL UNIQUE,
  user_agent VARCHAR(500), ip_address VARCHAR(64),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  revoked_at TIMESTAMPTZ, revoke_reason VARCHAR(100)
);
CREATE INDEX IF NOT EXISTS ix_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS ix_user_sessions_jti ON user_sessions(jti);
CREATE INDEX IF NOT EXISTS ix_user_sessions_revoked_at ON user_sessions(revoked_at);
