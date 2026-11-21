-- SEC-02: the runtime DB role may only INSERT/SELECT on audit_event (role exists on the docker stack only).
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'yamicc_app') THEN
    REVOKE ALL ON audit_event FROM yamicc_app;
    GRANT SELECT, INSERT ON audit_event TO yamicc_app;
  END IF;
END $$;
