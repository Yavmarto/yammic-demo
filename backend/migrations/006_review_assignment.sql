ALTER TABLE extraction ADD COLUMN assigned_to text REFERENCES app_user(username);
ALTER TABLE extraction ADD COLUMN due_date date;
ALTER TABLE extraction ADD CONSTRAINT assignment_due_pair CHECK ((assigned_to IS NULL) = (due_date IS NULL));
