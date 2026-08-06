-- Additive only. Review and execute through the normal PostgreSQL release process.
ALTER TABLE bank_monthly_billing_snapshots ADD COLUMN IF NOT EXISTS visit_id INTEGER;
ALTER TABLE bank_monthly_billing_snapshots ADD COLUMN IF NOT EXISTS visit_type VARCHAR(30);
ALTER TABLE bank_monthly_billing_snapshots ADD COLUMN IF NOT EXISTS executive VARCHAR(200);
ALTER TABLE bank_monthly_billing_snapshots ADD COLUMN IF NOT EXISTS executive_rate NUMERIC(14, 2);
ALTER TABLE bank_monthly_billing_snapshots ADD COLUMN IF NOT EXISTS executive_rate_status VARCHAR(20);
CREATE INDEX IF NOT EXISTS ix_bank_monthly_billing_snapshots_visit_id ON bank_monthly_billing_snapshots (visit_id);
ALTER TABLE bank_monthly_billing_snapshots
  ADD CONSTRAINT fk_bank_monthly_billing_snapshots_visit_id
  FOREIGN KEY (visit_id) REFERENCES case_visits(id) ON DELETE SET NULL;
