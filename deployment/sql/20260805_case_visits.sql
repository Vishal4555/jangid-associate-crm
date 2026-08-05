-- Additive migration: multiple operational visits per parent case.
-- Existing case operational columns intentionally remain as legacy compatibility fields.
BEGIN;

CREATE TABLE IF NOT EXISTS case_visits (
    id BIGSERIAL PRIMARY KEY,
    case_id INTEGER NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    visit_type VARCHAR(30) NOT NULL,
    address VARCHAR(500),
    district_id INTEGER REFERENCES districts(id) ON DELETE SET NULL,
    district VARCHAR(100),
    city VARCHAR(100),
    landmark VARCHAR(300),
    executive VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    negative_reason VARCHAR(300),
    receive_date DATE,
    closed_date DATE,
    remarks VARCHAR(1000),
    next_follow_up_at TIMESTAMP,
    follow_up_note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    updated_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT ck_case_visits_type CHECK (visit_type IN ('Residence','Office','Permanent','Business','Other')),
    CONSTRAINT ck_case_visits_status CHECK (status IN ('Pending','Positive','Negative')),
    CONSTRAINT ck_case_visits_closed_date CHECK (
        (status = 'Pending' AND closed_date IS NULL) OR
        (status IN ('Positive','Negative') AND closed_date IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS ix_case_visits_case_id ON case_visits(case_id);
CREATE INDEX IF NOT EXISTS ix_case_visits_district_id ON case_visits(district_id);
CREATE INDEX IF NOT EXISTS ix_case_visits_receive_status ON case_visits(receive_date, status);
CREATE INDEX IF NOT EXISTS ix_case_visits_executive ON case_visits(executive);

INSERT INTO case_visits (
    case_id, visit_type, address, district_id, district, city, landmark,
    executive, status, negative_reason, receive_date, closed_date, remarks,
    next_follow_up_at, follow_up_note
)
SELECT c.id, 'Residence', c.address, c.district_id, c.district, c.city, c.landmark,
       c.executive,
       CASE WHEN c.status IN ('Positive','Negative') THEN c.status ELSE 'Pending' END,
       c.negative_reason, c.receive_date,
       CASE WHEN c.status IN ('Positive','Negative') THEN COALESCE(c.closed_date, CURRENT_DATE) ELSE NULL END,
       c.remarks, c.next_follow_up_at, c.follow_up_note
FROM cases c
WHERE NOT EXISTS (SELECT 1 FROM case_visits v WHERE v.case_id = c.id);

COMMENT ON TABLE case_visits IS 'Operational verification points; cases operational columns are legacy during transition';
COMMIT;
