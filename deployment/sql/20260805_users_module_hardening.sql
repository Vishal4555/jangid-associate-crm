BEGIN;

ALTER TABLE users ADD COLUMN IF NOT EXISTS mobile VARCHAR(20);
ALTER TABLE users ADD COLUMN IF NOT EXISTS executive_id INTEGER REFERENCES executives(id) ON DELETE RESTRICT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS ix_users_executive_id ON users(executive_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_username_ci ON users(lower(trim(username)));
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email_ci ON users(lower(trim(email)));
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_active_executive
    ON users(executive_id) WHERE is_active = true AND executive_id IS NOT NULL;

ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_executive_link;
ALTER TABLE users ADD CONSTRAINT ck_users_executive_link CHECK (
    (role = 'Executive' AND executive_id IS NOT NULL)
    OR (role IN ('Admin', 'Manager') AND executive_id IS NULL)
) NOT VALID;

CREATE TABLE IF NOT EXISTS user_audit_logs (
    id SERIAL PRIMARY KEY,
    target_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    actor_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    action VARCHAR(50) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_user_audit_logs_target_user_id ON user_audit_logs(target_user_id);
CREATE INDEX IF NOT EXISTS ix_user_audit_logs_actor_user_id ON user_audit_logs(actor_user_id);
CREATE INDEX IF NOT EXISTS ix_user_audit_logs_action ON user_audit_logs(action);

COMMIT;

-- The Executive-link check is intentionally NOT VALID so deployment does not
-- rewrite or reject legacy production rows. Link existing Executive users, then run:
-- ALTER TABLE users VALIDATE CONSTRAINT ck_users_executive_link;
