BEGIN;

CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE IF NOT EXISTS bank_payout_rates (
    id SERIAL PRIMARY KEY,
    bank_id INTEGER NOT NULL REFERENCES banks(id) ON DELETE RESTRICT,
    state VARCHAR(100) DEFAULT 'Rajasthan',
    city VARCHAR(100),
    loan_type VARCHAR(100),
    product_type VARCHAR(100),
    payout_rate NUMERIC(14,2) NOT NULL CONSTRAINT ck_bank_payout_rate_nonnegative CHECK (payout_rate >= 0),
    effective_from DATE NOT NULL,
    effective_to DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    remarks TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    updated_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT ck_bank_payout_rate_dates CHECK (effective_to IS NULL OR effective_to >= effective_from),
    CONSTRAINT ex_bank_payout_rate_dates EXCLUDE USING gist (
        bank_id WITH =,
        (lower(trim(coalesce(city, '')))) WITH =,
        (lower(trim(coalesce(loan_type, '')))) WITH =,
        (lower(trim(coalesce(product_type, '')))) WITH =,
        (daterange(effective_from, coalesce(effective_to, 'infinity'::date), '[]')) WITH &&
    )
);

CREATE TABLE IF NOT EXISTS executive_payout_rates (
    id SERIAL PRIMARY KEY,
    executive_id INTEGER NOT NULL REFERENCES executives(id) ON DELETE RESTRICT,
    bank_id INTEGER REFERENCES banks(id) ON DELETE RESTRICT,
    city VARCHAR(100),
    loan_type VARCHAR(100),
    product_type VARCHAR(100),
    payout_rate NUMERIC(14,2) NOT NULL CONSTRAINT ck_executive_payout_rate_nonnegative CHECK (payout_rate >= 0),
    effective_from DATE NOT NULL,
    effective_to DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    remarks TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    updated_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT ck_executive_payout_rate_dates CHECK (effective_to IS NULL OR effective_to >= effective_from),
    CONSTRAINT ex_executive_payout_rate_dates EXCLUDE USING gist (
        executive_id WITH =,
        (coalesce(bank_id, 0)) WITH =,
        (lower(trim(coalesce(city, '')))) WITH =,
        (lower(trim(coalesce(loan_type, '')))) WITH =,
        (lower(trim(coalesce(product_type, '')))) WITH =,
        (daterange(effective_from, coalesce(effective_to, 'infinity'::date), '[]')) WITH &&
    )
);

CREATE INDEX IF NOT EXISTS ix_bank_payout_rates_lookup ON bank_payout_rates (bank_id, effective_from, effective_to) WHERE is_active;
CREATE INDEX IF NOT EXISTS ix_executive_payout_rates_lookup ON executive_payout_rates (executive_id, effective_from, effective_to) WHERE is_active;

ALTER TABLE billing ADD COLUMN IF NOT EXISTS bank_payout_rate_id INTEGER REFERENCES bank_payout_rates(id) ON DELETE SET NULL;
ALTER TABLE billing ADD COLUMN IF NOT EXISTS executive_payout_rate_id INTEGER REFERENCES executive_payout_rates(id) ON DELETE SET NULL;

COMMIT;
