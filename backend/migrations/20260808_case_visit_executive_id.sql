ALTER TABLE case_visits ADD COLUMN IF NOT EXISTS executive_id INTEGER;

CREATE INDEX IF NOT EXISTS ix_case_visits_executive_id ON case_visits (executive_id);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_case_visits_executive_id') THEN
    ALTER TABLE case_visits ADD CONSTRAINT fk_case_visits_executive_id
      FOREIGN KEY (executive_id) REFERENCES executives(id) ON DELETE SET NULL;
  END IF;
END $$;

UPDATE case_visits AS visit
SET executive_id = executive.id
FROM executives AS executive
WHERE visit.executive_id IS NULL
  AND lower(trim(visit.executive)) = lower(trim(executive.full_name))
  AND NOT EXISTS (
    SELECT 1 FROM executives AS duplicate
    WHERE duplicate.id <> executive.id
      AND lower(trim(duplicate.full_name)) = lower(trim(executive.full_name))
  );
