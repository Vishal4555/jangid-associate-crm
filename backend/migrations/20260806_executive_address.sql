ALTER TABLE executives ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE executives ADD COLUMN IF NOT EXISTS district_id INTEGER;
ALTER TABLE executives ADD COLUMN IF NOT EXISTS city VARCHAR(100);
ALTER TABLE executives ADD COLUMN IF NOT EXISTS pincode VARCHAR(10);
CREATE INDEX IF NOT EXISTS ix_executives_district_id ON executives (district_id);
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_executives_district_id') THEN
    ALTER TABLE executives ADD CONSTRAINT fk_executives_district_id FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE SET NULL;
  END IF;
END $$;
