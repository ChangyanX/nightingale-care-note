begin;

-- PostgreSQL requires UPDATE privilege for SELECT ... FOR SHARE row locks used
-- by complete_ai_scribe_job, even though the worker never updates these rows.
grant update on table
  public.source_records,
  public.care_notes
to service_role;

commit;
