-- Additive, data-preserving hierarchical Bank Rate defaults and overrides.
-- NULL dimensions are normalized wildcards: bank=All Banks, district=All Rajasthan,
-- city=All Cities. Existing rows and finalized billing snapshots are untouched.
CREATE EXTENSION IF NOT EXISTS btree_gist;

ALTER TABLE bank_payout_rates ALTER COLUMN bank_id DROP NOT NULL;

ALTER TABLE bank_payout_rates DROP CONSTRAINT IF EXISTS ex_bank_rate_company_bank_district_dates;
ALTER TABLE bank_payout_rates DROP CONSTRAINT IF EXISTS ex_bank_rate_company_bank_district_city_dates;
ALTER TABLE bank_payout_rates ADD CONSTRAINT ex_bank_rate_normalized_dimensions_dates
    EXCLUDE USING gist (
        company_id WITH =,
        (COALESCE(bank_id, 0)) WITH =,
        (COALESCE(district_id, 0)) WITH =,
        (lower(btrim(COALESCE(city, '')))) WITH =,
        daterange(effective_from, COALESCE(effective_to, 'infinity'::date), '[]') WITH &&
    ) WHERE (is_active AND company_id IS NOT NULL);

DROP INDEX IF EXISTS ix_bank_rates_jaipur_city_lookup;
CREATE INDEX IF NOT EXISTS ix_bank_rates_hierarchical_lookup
    ON bank_payout_rates (company_id, bank_id, district_id, lower(btrim(city)), effective_from, effective_to)
    WHERE is_active AND company_id IS NOT NULL;
