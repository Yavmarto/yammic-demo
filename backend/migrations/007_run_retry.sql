ALTER TABLE extraction_run ADD COLUMN retry_of_run_id integer REFERENCES extraction_run(id);
CREATE UNIQUE INDEX extraction_run_retry_once ON extraction_run(retry_of_run_id) WHERE retry_of_run_id IS NOT NULL;
