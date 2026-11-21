-- W5: FHIR ingestion. Identifiers never land here; see app/ingest/pseudo.py.
CREATE TABLE fhir_sync_run (
  id serial PRIMARY KEY, started_at timestamptz NOT NULL, finished_at timestamptz,
  duration_ms int, status text NOT NULL CHECK (status IN ('completed','partial','failed')),
  mode text NOT NULL CHECK (mode IN ('full','incremental')), since text, cursor text,
  triggered_by text NOT NULL, counts jsonb NOT NULL DEFAULT '{}', errors jsonb NOT NULL DEFAULT '[]'
);
-- Separate mapping table: the only place a (keyed, irreversible) hospital identifier hash lives.
-- No API route reads it.
CREATE TABLE pseudonym_map (
  pseudonym text PRIMARY KEY, mrn_hmac text NOT NULL UNIQUE,
  participant_id text NOT NULL UNIQUE REFERENCES participant, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE fhir_fact (
  resource_type text NOT NULL, fhir_id text NOT NULL, participant_id text NOT NULL REFERENCES participant,
  last_updated timestamptz, code text, display text, value text, effective text, status text,
  data jsonb NOT NULL, sync_run_id int REFERENCES fhir_sync_run,
  PRIMARY KEY (resource_type, fhir_id)
);
CREATE INDEX ON fhir_fact (participant_id, resource_type);
ALTER TABLE source_document ADD COLUMN source_system text NOT NULL DEFAULT 'bundled';
ALTER TABLE source_document ADD COLUMN ingested_run_id int REFERENCES fhir_sync_run;
