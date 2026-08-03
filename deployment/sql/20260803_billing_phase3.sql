-- Billing Phase 3: additive, production-safe PostgreSQL migration. Do not run automatically.
BEGIN;

CREATE TABLE IF NOT EXISTS billing_months (
 id BIGSERIAL PRIMARY KEY, billing_month DATE NOT NULL, status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
 finalized_at TIMESTAMPTZ, finalized_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
 reopened_at TIMESTAMPTZ, reopened_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
 revision_number INTEGER NOT NULL DEFAULT 0, notes TEXT,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 CONSTRAINT uq_billing_months_month UNIQUE (billing_month),
 CONSTRAINT ck_billing_months_first_day CHECK (billing_month = date_trunc('month', billing_month)::date),
 CONSTRAINT ck_billing_months_status CHECK (status IN ('DRAFT','FINALIZED','REOPENED')),
 CONSTRAINT ck_billing_months_revision CHECK (revision_number >= 0)
);

CREATE TABLE IF NOT EXISTS executive_monthly_billing_snapshots (
 id BIGSERIAL PRIMARY KEY, billing_month_id BIGINT NOT NULL REFERENCES billing_months(id) ON DELETE CASCADE,
 executive_id INTEGER REFERENCES executives(id) ON DELETE SET NULL, executive_name VARCHAR(200) NOT NULL,
 rate_display VARCHAR(200) NOT NULL, total_points INTEGER NOT NULL, gross_payment NUMERIC(14,2) NOT NULL,
 advance_amount NUMERIC(14,2) NOT NULL DEFAULT 0, net_payment NUMERIC(14,2) NOT NULL,
 paid_amount NUMERIC(14,2) NOT NULL DEFAULT 0, balance_amount NUMERIC(14,2) NOT NULL,
 payment_status VARCHAR(30) NOT NULL, bank_counts JSONB NOT NULL DEFAULT '{}'::jsonb,
 rate_status VARCHAR(20) NOT NULL, remarks TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 CONSTRAINT uq_exec_snapshot_month_executive UNIQUE NULLS NOT DISTINCT (billing_month_id, executive_id),
 CONSTRAINT ck_exec_snapshot_points CHECK (total_points >= 0),
 CONSTRAINT ck_exec_snapshot_amounts CHECK (gross_payment >= 0 AND advance_amount >= 0 AND net_payment >= 0 AND paid_amount >= 0 AND balance_amount >= 0),
 CONSTRAINT ck_exec_snapshot_payment CHECK (paid_amount <= net_payment AND balance_amount = net_payment - paid_amount),
 CONSTRAINT ck_exec_snapshot_status CHECK (payment_status IN ('Pending','Partially Paid','Paid','Cancelled')),
 CONSTRAINT ck_exec_snapshot_rate_status CHECK (rate_status IN ('MATCHED','MISSING','AMBIGUOUS')),
 CONSTRAINT ck_exec_snapshot_bank_counts CHECK (jsonb_typeof(bank_counts) = 'object')
);

CREATE TABLE IF NOT EXISTS bank_monthly_billing_snapshots (
 id BIGSERIAL PRIMARY KEY, billing_month_id BIGINT NOT NULL REFERENCES billing_months(id) ON DELETE CASCADE,
 case_id INTEGER REFERENCES cases(id) ON DELETE SET NULL, date DATE NOT NULL, bank VARCHAR(200), los_no VARCHAR(200),
 applicant VARCHAR(255), address TEXT, city VARCHAR(100), mobile VARCHAR(50), case_status VARCHAR(100) NOT NULL,
 remark TEXT, rate NUMERIC(14,2) NOT NULL, rate_status VARCHAR(20) NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 CONSTRAINT ck_bank_snapshot_rate CHECK (rate >= 0),
 CONSTRAINT ck_bank_snapshot_rate_status CHECK (rate_status IN ('MATCHED','MISSING','AMBIGUOUS'))
);

CREATE TABLE IF NOT EXISTS bank_monthly_payments (
 id BIGSERIAL PRIMARY KEY, billing_month DATE NOT NULL, bank VARCHAR(200) NOT NULL, city VARCHAR(100) NOT NULL DEFAULT '',
 billed_amount NUMERIC(14,2) NOT NULL, received_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
 balance_amount NUMERIC(14,2) NOT NULL, status VARCHAR(30) NOT NULL DEFAULT 'Pending', payment_date DATE,
 payment_reference VARCHAR(200), remarks TEXT, is_finalized BOOLEAN NOT NULL DEFAULT false,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 created_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL, updated_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
 CONSTRAINT uq_bank_payment_month_bank_city UNIQUE (billing_month, bank, city),
 CONSTRAINT ck_bank_payment_first_day CHECK (billing_month = date_trunc('month', billing_month)::date),
 CONSTRAINT ck_bank_payment_amounts CHECK (billed_amount >= 0 AND received_amount >= 0 AND received_amount <= billed_amount),
 CONSTRAINT ck_bank_payment_balance CHECK (balance_amount = billed_amount - received_amount),
 CONSTRAINT ck_bank_payment_status CHECK (status IN ('Pending','Partially Paid','Paid','Cancelled'))
);

CREATE INDEX IF NOT EXISTS ix_exec_snapshots_month ON executive_monthly_billing_snapshots(billing_month_id);
CREATE INDEX IF NOT EXISTS ix_exec_snapshots_executive ON executive_monthly_billing_snapshots(executive_id);
CREATE INDEX IF NOT EXISTS ix_bank_snapshots_month ON bank_monthly_billing_snapshots(billing_month_id);
CREATE INDEX IF NOT EXISTS ix_bank_snapshots_bank_city ON bank_monthly_billing_snapshots(bank, city);
CREATE INDEX IF NOT EXISTS ix_bank_payments_month ON bank_monthly_payments(billing_month);
CREATE INDEX IF NOT EXISTS ix_bank_payments_bank_city ON bank_monthly_payments(bank, city);

COMMIT;

-- Backfill behavior: no legacy billing or payment data is copied automatically. Existing billing,
-- rate, and executive_monthly_payments tables remain authoritative until a month is first finalized.
