# Synthetic review assignment evidence

The demo PI can assign a pending or deferred extraction to a demo nurse with a date. Nurses can decide their own or unassigned items; the PI may decide any item. Monitors cannot assign or decide. Assignment changes are audited with before and after values and the actor. Completion is the existing accepted, corrected or rejected decision state; deferral stays open. Production roles and institution policy remain undecided.

Verification: focused API tests passed (2 tests) using a dedicated local PostgreSQL database and `TEST_SITE_ID=SITE-01`, including reload, validation, role restrictions, due-date change audit, deferral, completion, terminal assignment rejection, unassigned review, and audit-chain verification. An initial test run used the unmodified multi-site fictional seed; the final run used only one fictional site. No real data or presentation stack was used. Dart analysis of the review feature passed. No browser walkthrough was run.
