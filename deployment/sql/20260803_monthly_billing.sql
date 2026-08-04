BEGIN;

CREATE EXTENSION IF NOT EXISTS btree_gist;

ALTER TABLE bank_payout_rates DROP CONSTRAINT IF EXISTS ex_bank_payout_rate_dates;
ALTER TABLE bank_payout_rates ADD CONSTRAINT ex_bank_payout_rate_dates EXCLUDE USING gist (
    bank_id WITH =,
    (lower(trim(coalesce(city, '')))) WITH =,
    (lower(trim(coalesce(loan_type, '')))) WITH =,
    (lower(trim(coalesce(product_type, '')))) WITH =,
    (daterange(effective_from, coalesce(effective_to, 'infinity'::date), '[]')) WITH &&
) WHERE (is_active);

ALTER TABLE executive_payout_rates DROP CONSTRAINT IF EXISTS ex_executive_payout_rate_dates;
ALTER TABLE executive_payout_rates ADD CONSTRAINT ex_executive_payout_rate_dates EXCLUDE USING gist (
    executive_id WITH =,
    (coalesce(bank_id, 0)) WITH =,
    (lower(trim(coalesce(city, '')))) WITH =,
    (lower(trim(coalesce(loan_type, '')))) WITH =,
    (lower(trim(coalesce(product_type, '')))) WITH =,
    (daterange(effective_from, coalesce(effective_to, 'infinity'::date), '[]')) WITH &&
) WHERE (is_active);

CREATE TABLE IF NOT EXISTS executive_monthly_payments (
    id SERIAL PRIMARY KEY,
    billing_month DATE NOT NULL,
    executive_id INTEGER NOT NULL REFERENCES executives(id) ON DELETE RESTRICT,
    gross_payment NUMERIC(14,2) NOT NULL CHECK (gross_payment >= 0),
    advance_amount NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (advance_amount >= 0),
    net_payment NUMERIC(14,2) NOT NULL CHECK (net_payment >= 0),
    paid_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
    balance_amount NUMERIC(14,2) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'Pending',
    payment_date DATE,
    payment_reference VARCHAR(200),
    remarks TEXT,
    is_finalized BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    updated_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT uq_monthly_payment_month_executive UNIQUE (billing_month, executive_id),
    CONSTRAINT ck_monthly_payment_paid_valid CHECK (paid_amount >= 0 AND paid_amount <= net_payment),
    CONSTRAINT ck_monthly_payment_balance_consistent CHECK (balance_amount = net_payment - paid_amount),
    CONSTRAINT ck_monthly_payment_status CHECK (status IN ('Pending', 'Partially Paid', 'Paid', 'Done'))
);

CREATE INDEX IF NOT EXISTS ix_monthly_payment_month ON executive_monthly_payments (billing_month);

-- Phase 1's billing table and Phase 2's detailed dimensions remain intact.
-- Monthly executive rates are rows where bank/city/loan_type/product_type are NULL.
-- Monthly bank rates are rows where city is populated and loan_type/product_type are NULL.

COMMIT;
