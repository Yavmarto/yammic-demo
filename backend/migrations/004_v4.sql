-- v4: multi-site sync, screening workflow, data-quality rules + query lifecycle, form versions.
ALTER TABLE fhir_sync_run ADD COLUMN source_id text NOT NULL DEFAULT 'hospital-1';
ALTER TABLE fhir_sync_run ADD COLUMN source_name text;
ALTER TABLE pseudonym_map ADD COLUMN source_id text NOT NULL DEFAULT 'hospital-1';

ALTER TABLE participant ADD COLUMN screen_fail_reason text;
ALTER TABLE participant ADD COLUMN coordinator_signed_by text;
ALTER TABLE participant ADD COLUMN coordinator_signed_at timestamptz;
ALTER TABLE participant ADD COLUMN consented_date date;
ALTER TABLE participant ADD COLUMN enrolled_by text;
ALTER TABLE participant ADD COLUMN enrolled_at timestamptz;

CREATE TABLE screening_criterion (
  study_id text NOT NULL REFERENCES study,
  id text NOT NULL,
  ord int NOT NULL,
  type text NOT NULL CHECK (type IN ('inclusion','exclusion')),
  text text NOT NULL,
  data_needed text,
  version int NOT NULL DEFAULT 1,
  PRIMARY KEY (study_id, id)
);

CREATE TABLE screening_check (
  participant_id text NOT NULL REFERENCES participant,
  criterion_id text NOT NULL,
  ai_status text NOT NULL DEFAULT 'unknown' CHECK (ai_status IN ('met','not_met','unknown')),
  confidence real NOT NULL DEFAULT 0,
  rationale text,
  document_id text REFERENCES source_document,
  span_start int,
  span_end int,
  evidence jsonb NOT NULL DEFAULT '[]',
  provider text,
  model text,
  prompt_version text,
  coordinator_status text CHECK (coordinator_status IN ('met','not_met','unknown')),
  confirmed_by text,
  confirmed_at timestamptz,
  note text,
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (participant_id, criterion_id)
);

ALTER TABLE data_query DROP CONSTRAINT IF EXISTS data_query_status_check;
ALTER TABLE data_query ADD CONSTRAINT data_query_status_check CHECK (status IN ('open','answered','closed'));
ALTER TABLE data_query ADD COLUMN rule_id text;
ALTER TABLE data_query ADD COLUMN answer text;
ALTER TABLE data_query ADD COLUMN answered_by text;
ALTER TABLE data_query ADD COLUMN answered_at timestamptz;

ALTER TABLE ecrf_field ADD COLUMN min_val double precision;
ALTER TABLE ecrf_field ADD COLUMN max_val double precision;
ALTER TABLE ecrf_field ADD COLUMN allowed_values jsonb;
ALTER TABLE ecrf_field ADD COLUMN form_version int NOT NULL DEFAULT 1;

ALTER TABLE ecrf_value ADD COLUMN form_version int NOT NULL DEFAULT 1;

CREATE TABLE ecrf_form_version (
  id serial PRIMARY KEY,
  study_id text NOT NULL REFERENCES study,
  form_id text NOT NULL,
  version int NOT NULL,
  status text NOT NULL CHECK (status IN ('proposed','approved','rejected')),
  fields jsonb NOT NULL DEFAULT '[]',
  criteria jsonb NOT NULL DEFAULT '[]',
  protocol_text text,
  proposed_by text NOT NULL,
  proposed_at timestamptz NOT NULL DEFAULT now(),
  provider text,
  model text,
  prompt_version text,
  approved_by text,
  approved_at timestamptz,
  note text,
  UNIQUE (study_id, form_id, version)
);
