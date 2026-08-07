CREATE TABLE case_import_sessions (
    id SERIAL PRIMARY KEY,
    token VARCHAR(64) NOT NULL UNIQUE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ NULL
);

CREATE INDEX ix_case_import_sessions_token ON case_import_sessions(token);
CREATE INDEX ix_case_import_sessions_user_id ON case_import_sessions(user_id);
CREATE INDEX ix_case_import_sessions_expires_at ON case_import_sessions(expires_at);

CREATE TABLE case_import_rows (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES case_import_sessions(id) ON DELETE CASCADE,
    row_number INTEGER NOT NULL,
    data_json TEXT NOT NULL,
    state VARCHAR(20) NOT NULL,
    intended_action VARCHAR(50) NOT NULL,
    errors_json TEXT NOT NULL DEFAULT '[]',
    warnings_json TEXT NOT NULL DEFAULT '[]',
    imported_at TIMESTAMPTZ NULL,
    CONSTRAINT uq_case_import_rows_session_row UNIQUE (session_id, row_number)
);

CREATE INDEX ix_case_import_rows_session_id ON case_import_rows(session_id);
CREATE INDEX ix_case_import_rows_state ON case_import_rows(state);
