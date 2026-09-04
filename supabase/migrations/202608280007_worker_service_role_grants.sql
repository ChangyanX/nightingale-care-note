begin;

-- Worker RPCs intentionally use SECURITY INVOKER. Grant the service role only
-- the table operations needed to claim, load, persist, and fail durable jobs.
grant usage on schema public to service_role;

grant select on table
  public.ai_jobs,
  public.source_records,
  public.entries,
  public.entry_versions,
  public.patients,
  public.profiles,
  public.care_notes
to service_role;

grant update on table public.ai_jobs to service_role;

grant insert on table
  public.entries,
  public.entry_versions,
  public.highlights,
  public.audit_events,
  public.ai_job_events
to service_role;

commit;
