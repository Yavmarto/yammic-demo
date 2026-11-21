-- Runs once, when the PostgreSQL data volume is first initialised.
-- The backend uses database "yammic" (created by POSTGRES_DB).
-- HAPI FHIR gets its own database on the same server.
CREATE DATABASE hapi OWNER yammic;
