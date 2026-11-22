-- Marks participants that arrived through FHIR sync (as opposed to the seeded baseline cohort).
ALTER TABLE participant ADD COLUMN IF NOT EXISTS synced_from_fhir boolean NOT NULL DEFAULT false;
UPDATE participant SET synced_from_fhir = true WHERE status_detail = 'synced_from_fhir';
