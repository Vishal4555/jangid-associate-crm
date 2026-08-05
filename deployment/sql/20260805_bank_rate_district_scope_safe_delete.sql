-- Additive, data-preserving district scope migration.
ALTER TABLE bank_payout_rates ADD COLUMN IF NOT EXISTS district_scope VARCHAR(30);
ALTER TABLE bank_monthly_billing_snapshots
    ADD COLUMN IF NOT EXISTS bank_payout_rate_id INTEGER REFERENCES bank_payout_rates(id) ON DELETE RESTRICT;
CREATE INDEX IF NOT EXISTS ix_bank_monthly_snapshots_rate_id
    ON bank_monthly_billing_snapshots (bank_payout_rate_id) WHERE bank_payout_rate_id IS NOT NULL;

-- Explicit mapping for existing structured rows. Legacy rows (company_id IS NULL)
-- remain NULL and retain their legacy Bank + City matching behavior.
UPDATE bank_payout_rates r
SET district_scope = CASE
    WHEN r.district_id IS NULL THEN 'RAJASTHAN_EXCEPT_JAIPUR'
    WHEN lower(btrim(d.name)) = 'jaipur' THEN 'JAIPUR_ONLY'
    ELSE 'SELECTED_DISTRICTS'
END
FROM districts d
WHERE r.company_id IS NOT NULL
  AND r.district_id = d.id
  AND r.district_scope IS NULL;

UPDATE bank_payout_rates
SET district_scope = 'RAJASTHAN_EXCEPT_JAIPUR'
WHERE company_id IS NOT NULL AND district_id IS NULL AND district_scope IS NULL;

ALTER TABLE bank_payout_rates DROP CONSTRAINT IF EXISTS ck_bank_rate_district_scope;
ALTER TABLE bank_payout_rates ADD CONSTRAINT ck_bank_rate_district_scope
CHECK (
    company_id IS NULL OR
    (district_scope IS NOT NULL AND district_scope IN ('RAJASTHAN_EXCEPT_JAIPUR', 'JAIPUR_ONLY', 'SELECTED_DISTRICTS'))
);

CREATE OR REPLACE FUNCTION validate_jaipur_bank_rate_city()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE district_name TEXT;
BEGIN
    IF NEW.company_id IS NULL THEN RETURN NEW; END IF;
    SELECT lower(btrim(name)) INTO district_name FROM districts WHERE id = NEW.district_id;
    NEW.city := NULLIF(btrim(NEW.city), '');
    IF NEW.district_scope = 'RAJASTHAN_EXCEPT_JAIPUR'
       AND (NEW.district_id IS NOT NULL OR NEW.city IS NOT NULL) THEN
        RAISE EXCEPTION 'Rajasthan Except Jaipur rules cannot specify district or city' USING ERRCODE = '23514';
    ELSIF NEW.district_scope = 'JAIPUR_ONLY' AND district_name IS DISTINCT FROM 'jaipur' THEN
        RAISE EXCEPTION 'Jaipur Only scope must reference Jaipur district' USING ERRCODE = '23514';
    ELSIF NEW.district_scope = 'SELECTED_DISTRICTS' AND NEW.district_id IS NULL THEN
        RAISE EXCEPTION 'Selected Districts scope requires a district' USING ERRCODE = '23514';
    ELSIF NEW.district_scope = 'SELECTED_DISTRICTS'
          AND district_name IS DISTINCT FROM 'jaipur' AND NEW.city IS NOT NULL THEN
        RAISE EXCEPTION 'City-specific rates are allowed only for Jaipur district' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_validate_jaipur_bank_rate_city ON bank_payout_rates;
CREATE TRIGGER trg_validate_jaipur_bank_rate_city
BEFORE INSERT OR UPDATE OF company_id, district_scope, district_id, city ON bank_payout_rates
FOR EACH ROW EXECUTE FUNCTION validate_jaipur_bank_rate_city();

ALTER TABLE bank_payout_rates DROP CONSTRAINT IF EXISTS ex_bank_rate_normalized_dimensions_dates;
ALTER TABLE bank_payout_rates ADD CONSTRAINT ex_bank_rate_scoped_dimensions_dates
EXCLUDE USING gist (
    company_id WITH =,
    (COALESCE(bank_id, 0)) WITH =,
    district_scope WITH =,
    (COALESCE(district_id, 0)) WITH =,
    (lower(btrim(COALESCE(city, '')))) WITH =,
    daterange(effective_from, COALESCE(effective_to, 'infinity'::date), '[]') WITH &&
) WHERE (is_active AND company_id IS NOT NULL);

CREATE INDEX IF NOT EXISTS ix_bank_rates_scope_lookup
ON bank_payout_rates (company_id, district_scope, bank_id, district_id, lower(btrim(city)), effective_from, effective_to)
WHERE is_active AND company_id IS NOT NULL;
