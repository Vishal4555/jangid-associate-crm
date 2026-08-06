BEGIN;

CREATE TABLE IF NOT EXISTS user_companies (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    assigned_by_user_id INTEGER REFERENCES users(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_user_companies_user_company UNIQUE(user_id, company_id)
);
CREATE INDEX IF NOT EXISTS ix_user_companies_user_id ON user_companies(user_id);
CREATE INDEX IF NOT EXISTS ix_user_companies_company_id ON user_companies(company_id);

INSERT INTO permissions(code,name,description,module) VALUES
('masters.view_assigned_companies','View assigned company masters','Read assigned company reference data','Masters'),
('masters.manage','Manage masters','Manage supported master data within scope','Masters'),
('companies.view_all','View all companies','Bypass assigned-company read scope','Masters'),
('companies.manage_all','Manage all companies','Bypass assigned-company write scope','Masters')
ON CONFLICT (code) DO UPDATE SET name=EXCLUDED.name, description=EXCLUDED.description, module=EXCLUDED.module;

COMMIT;
