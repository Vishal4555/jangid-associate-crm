-- Additive migration only. Existing legacy Bank + City rate data remains intact.
CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(50),
    source_type VARCHAR(20) NOT NULL DEFAULT 'Other' CONSTRAINT ck_companies_source_type CHECK (source_type IN ('WhatsApp','Email','Both','Other')),
    contact_person VARCHAR(200), email VARCHAR(255), mobile VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT TRUE, remarks TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_companies_name_ci ON companies (lower(btrim(name)));
CREATE UNIQUE INDEX IF NOT EXISTS uq_companies_code ON companies (code) WHERE code IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_companies_active ON companies (is_active);

CREATE TABLE IF NOT EXISTS districts (
    id SERIAL PRIMARY KEY, name VARCHAR(100) NOT NULL, state VARCHAR(100) NOT NULL DEFAULT 'Rajasthan',
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_districts_state_name_ci ON districts (lower(btrim(state)), lower(btrim(name)));
CREATE INDEX IF NOT EXISTS ix_districts_state_active ON districts (state, is_active);

CREATE TABLE IF NOT EXISTS company_banks (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    bank_id INTEGER NOT NULL REFERENCES banks(id) ON DELETE RESTRICT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE, remarks TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_company_banks_company_bank UNIQUE (company_id, bank_id)
);
CREATE INDEX IF NOT EXISTS ix_company_banks_company_active ON company_banks (company_id, is_active);
CREATE INDEX IF NOT EXISTS ix_company_banks_bank ON company_banks (bank_id);

ALTER TABLE cases ADD COLUMN IF NOT EXISTS company_id INTEGER REFERENCES companies(id) ON DELETE SET NULL;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS company VARCHAR(200);
ALTER TABLE cases ADD COLUMN IF NOT EXISTS district_id INTEGER REFERENCES districts(id) ON DELETE SET NULL;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS district VARCHAR(100);
CREATE INDEX IF NOT EXISTS ix_cases_company_id ON cases (company_id);
CREATE INDEX IF NOT EXISTS ix_cases_district_id ON cases (district_id);

ALTER TABLE bank_payout_rates ADD COLUMN IF NOT EXISTS company_id INTEGER REFERENCES companies(id) ON DELETE RESTRICT;
ALTER TABLE bank_payout_rates ADD COLUMN IF NOT EXISTS district_id INTEGER REFERENCES districts(id) ON DELETE RESTRICT;
CREATE INDEX IF NOT EXISTS ix_bank_rates_company_bank_district ON bank_payout_rates (company_id, bank_id, district_id, effective_from, effective_to) WHERE is_active AND company_id IS NOT NULL AND district_id IS NOT NULL;
ALTER TABLE bank_payout_rates ADD CONSTRAINT ex_bank_rate_company_bank_district_dates
    EXCLUDE USING gist (company_id WITH =, bank_id WITH =, district_id WITH =,
        (lower(btrim(COALESCE(city, '')))) WITH =,
        daterange(effective_from, COALESCE(effective_to, 'infinity'::date), '[]') WITH &&)
    WHERE (is_active AND company_id IS NOT NULL AND district_id IS NOT NULL);

ALTER TABLE bank_monthly_billing_snapshots ADD COLUMN IF NOT EXISTS company VARCHAR(200);
ALTER TABLE bank_monthly_billing_snapshots ADD COLUMN IF NOT EXISTS district VARCHAR(100);
ALTER TABLE bank_monthly_payments ADD COLUMN IF NOT EXISTS company VARCHAR(200) NOT NULL DEFAULT '';
ALTER TABLE bank_monthly_payments ADD COLUMN IF NOT EXISTS district VARCHAR(100) NOT NULL DEFAULT '';
CREATE INDEX IF NOT EXISTS ix_bank_monthly_payments_company_month ON bank_monthly_payments (billing_month, company, bank, district);
