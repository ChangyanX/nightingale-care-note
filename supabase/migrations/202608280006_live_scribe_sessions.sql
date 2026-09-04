begin;

create function public.create_clinical_scribe_session(
  p_patient_id uuid,
  p_interaction_type public.ai_interaction_type,
  p_content text,
  p_idempotency_key text
)
returns public.ai_jobs
language plpgsql
security invoker
set search_path = ''
as $$
declare
  target_patient public.patients;
  target_note public.care_notes;
  existing_job public.ai_jobs;
  new_source public.source_records;
  new_entry public.entries;
  new_job public.ai_jobs;
  caller_role public.author_role;
  source_kind public.source_type;
  note_kind public.entry_type;
begin
  if p_interaction_type not in ('doctor_consult', 'nurse_consult')
     or char_length(trim(p_content)) not between 20 and 12000
     or char_length(trim(p_idempotency_key)) not between 8 and 200
     or trim(p_idempotency_key) !~ '^[A-Za-z0-9._:-]+$' then
    raise exception using errcode = '22023', message = 'Invalid live scribe session';
  end if;

  select * into target_patient
  from public.patients
  where id = p_patient_id;
  if not found then
    raise exception using errcode = 'P0002', message = 'Patient not found';
  end if;

  if p_interaction_type = 'doctor_consult'
     and public.has_clinic_role(
       target_patient.clinic_id,
       array['clinician']::public.clinic_role[]
     ) then
    caller_role := 'clinician';
    source_kind := 'doctor_consult';
    note_kind := 'clinician_note';
  elsif p_interaction_type = 'nurse_consult'
     and public.has_clinic_role(
       target_patient.clinic_id,
       array['staff']::public.clinic_role[]
     ) then
    caller_role := 'staff';
    source_kind := 'nurse_consult';
    note_kind := 'staff_note';
  else
    raise exception using errcode = '42501', message = 'Role cannot create this session';
  end if;

  select * into existing_job
  from public.ai_jobs
  where clinic_id = target_patient.clinic_id
    and idempotency_key = trim(p_idempotency_key);
  if found then
    return existing_job;
  end if;

  select * into target_note
  from public.care_notes
  where clinic_id = target_patient.clinic_id
    and patient_id = target_patient.id;
  if not found then
    raise exception using errcode = 'P0002', message = 'Care Note not found';
  end if;

  insert into public.source_records (
    clinic_id, patient_id, source_type, external_reference,
    occurred_at, metadata, created_by
  ) values (
    target_patient.clinic_id, target_patient.id, source_kind,
    'live-scribe:' || extensions.gen_random_uuid()::text,
    now(), jsonb_build_object('synthetic', true, 'capture', 'typed_live_demo'), auth.uid()
  ) returning * into new_source;

  insert into public.entries (
    clinic_id, patient_id, care_note_id, author_id, author_role, entry_type,
    visibility, content, content_plaintext, source_record_id, occurred_at
  ) values (
    target_patient.clinic_id, target_patient.id, target_note.id, auth.uid(),
    caller_role, note_kind, 'internal', trim(p_content), trim(p_content),
    new_source.id, new_source.occurred_at
  ) returning * into new_entry;

  insert into public.entry_versions (
    clinic_id, patient_id, entry_id, version_number, content_snapshot,
    changed_by, changed_by_role, change_reason
  ) values (
    new_entry.clinic_id, new_entry.patient_id, new_entry.id, 1, new_entry.content,
    auth.uid(), caller_role, 'Live AI-scribe source captured'
  );

  insert into public.audit_events (
    clinic_id, patient_id, actor_id, actor_role, action,
    resource_type, resource_id, metadata
  ) values (
    new_entry.clinic_id, new_entry.patient_id, auth.uid(), caller_role,
    'ai_scribe_source_created', 'entry', new_entry.id,
    jsonb_build_object('interaction_type', p_interaction_type, 'synthetic', true)
  );

  insert into public.ai_jobs (
    clinic_id, patient_id, source_record_id, interaction_type,
    requested_by, idempotency_key
  ) values (
    new_entry.clinic_id, new_entry.patient_id, new_source.id,
    p_interaction_type, auth.uid(), trim(p_idempotency_key)
  ) returning * into new_job;

  return new_job;
end;
$$;

create function public.submit_patient_ai_session(
  p_content text,
  p_idempotency_key text,
  p_structured jsonb default '{}'::jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  target_patient public.patients;
  target_note public.care_notes;
  existing_job public.ai_jobs;
  existing_entry public.entries;
  new_source public.source_records;
  new_entry public.entries;
  new_job public.ai_jobs;
begin
  if auth.uid() is null
     or char_length(trim(p_content)) not between 1 and 2000
     or char_length(trim(p_idempotency_key)) not between 8 and 200
     or trim(p_idempotency_key) !~ '^[A-Za-z0-9._:-]+$'
     or jsonb_typeof(coalesce(p_structured, '{}'::jsonb)) <> 'object'
     or octet_length(coalesce(p_structured, '{}'::jsonb)::text) > 4000 then
    raise exception using errcode = '22023', message = 'Invalid patient AI session';
  end if;

  select * into target_patient
  from public.patients
  where linked_profile_id = auth.uid()
  limit 1;
  if not found then
    raise exception using errcode = '42501', message = 'Patient portal unavailable';
  end if;

  select * into existing_job
  from public.ai_jobs
  where clinic_id = target_patient.clinic_id
    and requested_by = auth.uid()
    and interaction_type = 'ai_patient_session'
    and idempotency_key = trim(p_idempotency_key);
  if found then
    select * into existing_entry
    from public.entries
    where source_record_id = existing_job.source_record_id
      and author_id = auth.uid()
      and entry_type = 'patient_insight'
    limit 1;
    return jsonb_build_object(
      'entry', jsonb_build_object(
        'id', existing_entry.id,
        'entry_type', existing_entry.entry_type,
        'content', existing_entry.content,
        'occurred_at', existing_entry.occurred_at
      ),
      'job', jsonb_build_object(
        'id', existing_job.id,
        'status', existing_job.status,
        'created_at', existing_job.created_at,
        'updated_at', existing_job.updated_at,
        'completed_at', existing_job.completed_at,
        'safe_error_code', existing_job.safe_error_code
      )
    );
  end if;

  select * into target_note
  from public.care_notes
  where clinic_id = target_patient.clinic_id
    and patient_id = target_patient.id;
  if not found then
    raise exception using errcode = 'P0002', message = 'Care Note not found';
  end if;

  insert into public.source_records (
    clinic_id, patient_id, source_type, external_reference,
    occurred_at, metadata, created_by
  ) values (
    target_patient.clinic_id, target_patient.id, 'ai_patient_session',
    'portal:ai-question:' || extensions.gen_random_uuid()::text,
    now(), jsonb_build_object('synthetic', true, 'portal_kind', 'ai_question')
      || coalesce(p_structured, '{}'::jsonb), auth.uid()
  ) returning * into new_source;

  insert into public.entries (
    clinic_id, patient_id, care_note_id, author_id, author_role, entry_type,
    visibility, content, content_plaintext, source_record_id, occurred_at
  ) values (
    target_patient.clinic_id, target_patient.id, target_note.id, auth.uid(),
    'patient', 'patient_insight', 'internal', trim(p_content), trim(p_content),
    new_source.id, new_source.occurred_at
  ) returning * into new_entry;

  insert into public.entry_versions (
    clinic_id, patient_id, entry_id, version_number, content_snapshot,
    changed_by, changed_by_role, change_reason
  ) values (
    new_entry.clinic_id, new_entry.patient_id, new_entry.id, 1, new_entry.content,
    auth.uid(), 'patient', 'Patient AI session submitted'
  );

  insert into public.audit_events (
    clinic_id, patient_id, actor_id, actor_role, action,
    resource_type, resource_id, metadata
  ) values (
    new_entry.clinic_id, new_entry.patient_id, auth.uid(), 'patient',
    'patient_ai_session_submitted', 'entry', new_entry.id,
    jsonb_build_object('synthetic', true, 'non_diagnostic', true)
  );

  insert into public.ai_jobs (
    clinic_id, patient_id, source_record_id, interaction_type,
    requested_by, idempotency_key
  ) values (
    new_entry.clinic_id, new_entry.patient_id, new_source.id,
    'ai_patient_session', auth.uid(), trim(p_idempotency_key)
  ) returning * into new_job;

  return jsonb_build_object(
    'entry', jsonb_build_object(
      'id', new_entry.id,
      'entry_type', new_entry.entry_type,
      'content', new_entry.content,
      'occurred_at', new_entry.occurred_at
    ),
    'job', jsonb_build_object(
      'id', new_job.id,
      'status', new_job.status,
      'created_at', new_job.created_at,
      'updated_at', new_job.updated_at,
      'completed_at', new_job.completed_at,
      'safe_error_code', new_job.safe_error_code
    )
  );
end;
$$;

create function public.list_own_patient_ai_jobs()
returns table (
  id uuid,
  status public.ai_job_status,
  created_at timestamptz,
  updated_at timestamptz,
  completed_at timestamptz,
  safe_error_code text
)
language sql
security definer
set search_path = ''
stable
as $$
  select job.id, job.status, job.created_at, job.updated_at,
    job.completed_at, job.safe_error_code
  from public.ai_jobs job
  join public.patients patient
    on patient.id = job.patient_id and patient.clinic_id = job.clinic_id
  where patient.linked_profile_id = auth.uid()
    and job.requested_by = auth.uid()
    and job.interaction_type = 'ai_patient_session'
  order by job.created_at desc, job.id desc
  limit 20;
$$;

revoke all on function public.create_clinical_scribe_session(
  uuid, public.ai_interaction_type, text, text
) from public;
grant execute on function public.create_clinical_scribe_session(
  uuid, public.ai_interaction_type, text, text
) to authenticated;

revoke all on function public.submit_patient_ai_session(text, text, jsonb) from public;
grant execute on function public.submit_patient_ai_session(text, text, jsonb) to authenticated;

revoke all on function public.list_own_patient_ai_jobs() from public;
grant execute on function public.list_own_patient_ai_jobs() to authenticated;

commit;
