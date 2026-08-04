-- Preserves all rate rows and production data. Replaces only the structured-rate overlap rule.
CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE OR REPLACE FUNCTION validate_jaipur_bank_rate_city()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    district_name TEXT;
BEGIN
    IF NEW.company_id IS NULL AND NEW.district_id IS NULL THEN
        RETURN NEW; -- Legacy Bank + City row.
    END IF;

    SELECT lower(btrim(name)) INTO district_name FROM districts WHERE id = NEW.district_id;
    IF district_name IS DISTINCT FROM 'jaipur' AND NULLIF(btrim(NEW.city), '') IS NOT NULL THEN
        RAISE EXCEPTION 'City-specific rates are allowed only for Jaipur district.'
            USING ERRCODE = '23514';
    END IF;
    NEW.city := NULLIF(btrim(NEW.city), '');
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_validate_jaipur_bank_rate_city ON bank_payout_rates;
CREATE TRIGGER trg_validate_jaipur_bank_rate_city
BEFORE INSERT OR UPDATE OF company_id, district_id, city ON bank_payout_rates
FOR EACH ROW EXECUTE FUNCTION validate_jaipur_bank_rate_city();

ALTER TABLE bank_payout_rates DROP CONSTRAINT IF EXISTS ex_bank_rate_company_bank_district_dates;
ALTER TABLE bank_payout_rates ADD CONSTRAINT ex_bank_rate_company_bank_district_city_dates
    EXCLUDE USING gist (
        company_id WITH =,
        bank_id WITH =,
        district_id WITH =,
        (lower(btrim(COALESCE(city, '')))) WITH =,
        daterange(effective_from, COALESCE(effective_to, 'infinity'::date), '[]') WITH &&
    ) WHERE (is_active AND company_id IS NOT NULL AND district_id IS NOT NULL);

CREATE INDEX IF NOT EXISTS ix_bank_rates_jaipur_city_lookup
    ON bank_payout_rates (company_id, bank_id, district_id, lower(btrim(city)), effective_from, effective_to)
    WHERE is_active AND company_id IS NOT NULL AND district_id IS NOT NULL;
