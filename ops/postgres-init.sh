#!/bin/sh
# Runs once, when the PostgreSQL data volume is first initialised (docker-entrypoint-initdb.d).
#   yammic      superuser/owner: migrations, seed, admin (never used by the running app or HAPI)
#   yammic_app  the backend at runtime: DML on all tables, INSERT/SELECT only on audit_event (migration 003)
#   hapi        hospital 1 HAPI FHIR: owns database hapi only, no access to database yammic
#   hapi2       hospital 2 HAPI FHIR: owns database hapi2 only, no access to yammic or hapi
set -e
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d postgres <<SQL
CREATE ROLE yammic_app LOGIN PASSWORD '$APP_DB_PASSWORD';
CREATE ROLE hapi LOGIN PASSWORD '$HAPI_DB_PASSWORD';
CREATE ROLE hapi2 LOGIN PASSWORD '$HAPI2_DB_PASSWORD';
CREATE DATABASE hapi OWNER hapi;
CREATE DATABASE hapi2 OWNER hapi2;
REVOKE CONNECT ON DATABASE hapi FROM PUBLIC;
REVOKE CONNECT ON DATABASE hapi2 FROM PUBLIC;
REVOKE CONNECT ON DATABASE yammic FROM PUBLIC;
GRANT CONNECT ON DATABASE yammic TO yammic_app;
SQL
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d yammic <<SQL
GRANT USAGE ON SCHEMA public TO yammic_app;
ALTER DEFAULT PRIVILEGES FOR ROLE $POSTGRES_USER IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO yammic_app;
ALTER DEFAULT PRIVILEGES FOR ROLE $POSTGRES_USER IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO yammic_app;
SQL
