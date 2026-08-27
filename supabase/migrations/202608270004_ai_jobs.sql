begin;

create type public.ai_interaction_type as enum (
  'doctor_consult',
  'nurse_consult',
  'ai_patient_session'
);

create type public.ai_job_status as enum (
  'queued',
  'processing',
  'succeeded',
  'failed',
  'dead_letter'
);

create table public.ai_jobs (
  id uuid primary key default gen_random_uuid(),
  clinic_id uuid not null,
  patient_id uuid not null,
  source_record_id uuid not null,
  interaction_type public.ai_interaction_type not null,
  requested_by uuid not null references public.profiles(id) on delete restrict,
  idempotency_key text not null check (char_length(idempotency_key) between 8 and 200),
  status public.ai_job_status not null default 'queued',
  attempt_count integer not null default 0 check (attempt_count between 0 and 10),
  max_attempts integer not null default 3 check (max_attempts between 1 and 10),
  available_at timestamptz not null default now(),
  claimed_at timestamptz,
  lease_expires_at timestamptz,
  completed_at timestamptz,
  safe_error_code text check (
    safe_error_code is null
    or safe_error_code ~ '^[a-z0-9_]{1,64}$'
  ),
  output_entry_id uuid,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (clinic_id, idempotency_key),
  unique (output_entry_id),
  foreign key (patient_id, clinic_id)
    references public.patients(id, clinic_id) on delete cascade,
  foreign key (source_record_id, clinic_id, patient_id)
    references public.source_records(id, clinic_id, patient_id) on delete restrict,
  foreign key (output_entry_id, clinic_id, patient_id)
    references public.entries(id, clinic_id, patient_id) on delete restrict,
  check (
    (status = 'queued'
      and claimed_at is null
      and lease_expires_at is null
      and completed_at is null
      and output_entry_id is null)
    or (status = 'processing'
      and claimed_at is not null
      and lease_expires_at is not null
      and completed_at is null
      and output_entry_id is null)
    or (status = 'succeeded'
      and completed_at is not null
      and output_entry_id is not null
      and safe_error_code is null)
    or (status in ('failed', 'dead_letter')
      and completed_at is not null
      and output_entry_id is null
      and safe_error_code is not null)
  )
);

comment on table public.ai_jobs is
  'Durable orchestration metadata only. Raw transcripts, prompts, and provider bodies are prohibited.';

create index ai_jobs_claim_idx
on public.ai_jobs(status, available_at, created_at)
where status in ('queued', 'processing');

create index ai_jobs_patient_created_idx
on public.ai_jobs(patient_id, created_at desc);

create trigger ai_jobs_updated_at before update on public.ai_jobs
for each row execute function public.set_updated_at();

create function public.validate_ai_job_source()
returns trigger
language plpgsql
set search_path = ''
as $$
declare
  source_kind public.source_type;
begin
  select source_type into source_kind
  from public.source_records
  where id = new.source_record_id
    and clinic_id = new.clinic_id
    and patient_id = new.patient_id;

  if not found
     or (new.interaction_type = 'doctor_consult' and source_kind <> 'doctor_consult')
     or (new.interaction_type = 'nurse_consult' and source_kind <> 'nurse_consult')
     or (new.interaction_type = 'ai_patient_session' and source_kind <> 'ai_patient_session') then
    raise exception using errcode = '23514', message = 'AI job source type mismatch';
  end if;
  return new;
end;
$$;

create trigger validate_ai_job_source_before_insert
before insert on public.ai_jobs
for each row execute function public.validate_ai_job_source();

alter table public.ai_jobs enable row level security;
revoke all on public.ai_jobs from anon, authenticated;
grant select, insert on public.ai_jobs to authenticated;

create policy ai_jobs_select_clinical
on public.ai_jobs for select to authenticated
using (
  public.has_clinic_role(
    clinic_id,
    array['staff', 'clinician', 'admin']::public.clinic_role[]
  )
);

create policy ai_jobs_insert_clinical
on public.ai_jobs for insert to authenticated
with check (
  requested_by = (select auth.uid())
  and status = 'queued'
  and attempt_count = 0
  and max_attempts = 3
  and claimed_at is null
  and lease_expires_at is null
  and completed_at is null
  and safe_error_code is null
  and output_entry_id is null
  and public.has_clinic_role(
    clinic_id,
    array['staff', 'clinician']::public.clinic_role[]
  )
);

create function public.submit_ai_scribe_job(
  p_patient_id uuid,
  p_source_record_id uuid,
  p_interaction_type public.ai_interaction_type,
  p_idempotency_key text
)
returns public.ai_jobs
language plpgsql
security invoker
set search_path = ''
as $$
declare
  source_row public.source_records;
  submitted_job public.ai_jobs;
begin
  if char_length(trim(p_idempotency_key)) not between 8 and 200 then
    raise exception using errcode = '22023', message = 'Invalid idempotency key';
  end if;

  select * into source_row
  from public.source_records
  where id = p_source_record_id
    and patient_id = p_patient_id;

  if not found then
    raise exception using errcode = 'P0002', message = 'Source record not found';
  end if;

  if not public.has_clinic_role(
    source_row.clinic_id,
    array['staff', 'clinician']::public.clinic_role[]
  ) then
    raise exception using errcode = '42501', message = 'Role cannot submit AI jobs';
  end if;

  insert into public.ai_jobs (
    clinic_id,
    patient_id,
    source_record_id,
    interaction_type,
    requested_by,
    idempotency_key
  )
  values (
    source_row.clinic_id,
    source_row.patient_id,
    source_row.id,
    p_interaction_type,
    auth.uid(),
    trim(p_idempotency_key)
  )
  on conflict (clinic_id, idempotency_key)
  do nothing
  returning * into submitted_job;

  if submitted_job.id is null then
    select * into submitted_job
    from public.ai_jobs
    where clinic_id = source_row.clinic_id
      and idempotency_key = trim(p_idempotency_key);
  end if;

  return submitted_job;
end;
$$;

create function public.claim_ai_scribe_job(p_lease_seconds integer default 120)
returns public.ai_jobs
language plpgsql
security invoker
set search_path = ''
as $$
declare
  claimed_job public.ai_jobs;
begin
  if p_lease_seconds not between 30 and 900 then
    raise exception using errcode = '22023', message = 'Invalid lease duration';
  end if;

  update public.ai_jobs
  set status = 'dead_letter',
      completed_at = now(),
      safe_error_code = 'claim_lease_exhausted'
  where status = 'processing'
    and lease_expires_at <= now()
    and attempt_count >= max_attempts;

  with candidate as (
    select id
    from public.ai_jobs
    where (
      (status = 'queued' and available_at <= now())
      or (status = 'processing' and lease_expires_at <= now())
    )
      and attempt_count < max_attempts
    order by available_at, created_at, id
    for update skip locked
    limit 1
  )
  update public.ai_jobs job
  set status = 'processing',
      attempt_count = job.attempt_count + 1,
      claimed_at = now(),
      lease_expires_at = now() + make_interval(secs => p_lease_seconds),
      safe_error_code = null
  from candidate
  where job.id = candidate.id
  returning job.* into claimed_job;

  return claimed_job;
end;
$$;

revoke all on function public.submit_ai_scribe_job(
  uuid, uuid, public.ai_interaction_type, text
) from public;
grant execute on function public.submit_ai_scribe_job(
  uuid, uuid, public.ai_interaction_type, text
) to authenticated;

revoke all on function public.claim_ai_scribe_job(integer) from public;
grant execute on function public.claim_ai_scribe_job(integer) to service_role;

alter table public.ai_jobs force row level security;

commit;
