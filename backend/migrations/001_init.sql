-- Yammic demo backend schema v1. All data is synthetic.
CREATE TABLE study (
  id text PRIMARY KEY, short_name text NOT NULL, title text NOT NULL, phase text,
  status text, target_enrolment int, meta jsonb NOT NULL DEFAULT '{}'
);
CREATE TABLE site (
  id text PRIMARY KEY, study_id text NOT NULL REFERENCES study, name text NOT NULL,
  short_name text, city text, principal_investigator text, target_enrolment int
);
CREATE TABLE app_user (
  id serial PRIMARY KEY, username text UNIQUE NOT NULL, display_name text NOT NULL,
  role text NOT NULL CHECK (role IN ('nurse','monitor','pi','service')),
  password_hash text NOT NULL
);
CREATE TABLE participant (
  id text PRIMARY KEY, study_id text NOT NULL REFERENCES study, site_id text NOT NULL REFERENCES site,
  status text NOT NULL, status_detail text, age int, sex text, summary text,
  diagnosis_date date, enrolled_date date, treatments jsonb NOT NULL DEFAULT '[]'
);
CREATE TABLE visit (
  id serial PRIMARY KEY, participant_id text NOT NULL REFERENCES participant,
  name text NOT NULL, visit_date date, status text, note text
);
CREATE TABLE ecrf_field (
  id text PRIMARY KEY, study_id text NOT NULL REFERENCES study, form_id text NOT NULL,
  ord int NOT NULL, label text NOT NULL, section text, value_type text, required boolean NOT NULL,
  unit text, terminology jsonb, help text, cdisc jsonb
);
CREATE TABLE source_document (
  id text PRIMARY KEY, participant_id text NOT NULL REFERENCES participant,
  doc_type text NOT NULL, title text NOT NULL, language text, document_date date,
  text text NOT NULL, sha256 text NOT NULL
);
CREATE TABLE extraction_run (
  id serial PRIMARY KEY, participant_id text NOT NULL REFERENCES participant,
  document_id text REFERENCES source_document,
  status text NOT NULL CHECK (status IN ('queued','running','completed','failed')),
  total int NOT NULL DEFAULT 0, done int NOT NULL DEFAULT 0, error text,
  provider text, model text, prompt_version text,
  created_by text, created_at timestamptz NOT NULL DEFAULT now(), finished_at timestamptz
);
CREATE TABLE extraction (
  id text PRIMARY KEY, run_id int NOT NULL REFERENCES extraction_run,
  document_id text NOT NULL REFERENCES source_document,
  participant_id text NOT NULL REFERENCES participant,
  field_id text NOT NULL REFERENCES ecrf_field,
  status text NOT NULL CHECK (status IN ('proposed','abstained')),
  value text, normalized_value jsonb, unit text, confidence real NOT NULL DEFAULT 0,
  proposed_code jsonb, abstention_reason text,
  span_start int, span_end int, evidence jsonb NOT NULL DEFAULT '[]',
  provider text NOT NULL, model text NOT NULL, prompt_version text NOT NULL,
  review_state text NOT NULL DEFAULT 'pending'
    CHECK (review_state IN ('pending','accepted','corrected','rejected','deferred')),
  seeded_issue jsonb, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ON extraction (participant_id);
CREATE INDEX ON extraction (document_id);
CREATE INDEX ON extraction (run_id);
CREATE TABLE review_decision (
  id serial PRIMARY KEY, extraction_id text NOT NULL REFERENCES extraction,
  decision text NOT NULL CHECK (decision IN ('accept','correct','reject','defer')),
  corrected_value text, reason text, username text NOT NULL, role text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE ecrf_value (
  participant_id text NOT NULL REFERENCES participant,
  field_id text NOT NULL REFERENCES ecrf_field,
  value text NOT NULL, code jsonb, source_extraction_id text REFERENCES extraction,
  verified_by text NOT NULL, verified_at timestamptz NOT NULL DEFAULT now(),
  sdv_by text, sdv_at timestamptz,
  PRIMARY KEY (participant_id, field_id)
);
CREATE TABLE data_query (
  id serial PRIMARY KEY, participant_id text NOT NULL REFERENCES participant,
  site_id text NOT NULL REFERENCES site, field_id text REFERENCES ecrf_field,
  status text NOT NULL DEFAULT 'open' CHECK (status IN ('open','closed')),
  severity text NOT NULL DEFAULT 'low', text text NOT NULL,
  opened_by text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
  closed_by text, closed_at timestamptz
);
CREATE TABLE audit_event (
  seq bigserial PRIMARY KEY, ts timestamptz NOT NULL,
  actor text NOT NULL, role text NOT NULL, action text NOT NULL,
  entity_type text NOT NULL, entity_id text NOT NULL, participant_id text,
  before jsonb, after jsonb,
  source text NOT NULL CHECK (source IN ('human','ai')),
  model text, prompt_version text,
  prev_hash text NOT NULL, hash text NOT NULL
);
CREATE INDEX ON audit_event (participant_id);
CREATE INDEX ON audit_event (entity_type, entity_id);
-- Append-only: block UPDATE, DELETE and TRUNCATE.
CREATE FUNCTION audit_event_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'audit_event is append-only'; END $$;
CREATE TRIGGER audit_event_no_change BEFORE UPDATE OR DELETE ON audit_event
  FOR EACH ROW EXECUTE FUNCTION audit_event_immutable();
CREATE TRIGGER audit_event_no_truncate BEFORE TRUNCATE ON audit_event
  FOR EACH STATEMENT EXECUTE FUNCTION audit_event_immutable();
