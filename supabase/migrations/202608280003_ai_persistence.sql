begin;

create function public.complete_ai_scribe_job(
  p_job_id uuid,
  p_content text,
  p_schema_version text,
  p_provider_name text,
  p_model_name text,
  p_input_tokens integer default null,
  p_output_tokens integer default null,
  p_highlights jsonb default '[]'::jsonb
)
returns public.ai_jobs
language plpgsql
security invoker
set search_path = ''
as $$
declare
  current_job public.ai_jobs;
  source_row public.source_records;
  target_note public.care_notes;
  output_entry public.entries;
  output_version public.entry_versions;
  completed_job public.ai_jobs;
  output_entry_type public.entry_type;
  suggestion jsonb;
begin
  if char_length(trim(p_content)) not between 1 and 12000
     or p_schema_version !~ '^[0-9]+\.[0-9]+$'
     or char_length(trim(p_provider_name)) not between 1 and 80
     or char_length(trim(p_model_name)) not between 1 and 160
     or p_input_tokens is not null and p_input_tokens < 0
     or p_output_tokens is not null and p_output_tokens < 0
     or jsonb_typeof(p_highlights) <> 'array'
     or jsonb_array_length(p_highlights) > 10 then
    raise exception using errcode = '22023', message = 'Invalid AI persistence metadata';
  end if;

  select * into current_job
  from public.ai_jobs
  where id = p_job_id
  for update;

  if not found then
    raise exception using errcode = 'P0002', message = 'AI job not found';
  end if;

  -- An uncertain client response may retry after the transaction committed.
  -- Return the already linked job without creating another entry or highlight.
  if current_job.status = 'succeeded' and current_job.output_entry_id is not null then
    return current_job;
  end if;

  if current_job.status <> 'processing' or current_job.output_entry_id is not null then
    raise exception using errcode = '55000', message = 'AI job is not persistable';
  end if;

  select * into source_row
  from public.source_records
  where id = current_job.source_record_id
    and clinic_id = current_job.clinic_id
    and patient_id = current_job.patient_id
  for share;

  if not found
     or (current_job.interaction_type = 'doctor_consult'
       and source_row.source_type <> 'doctor_consult')
     or (current_job.interaction_type = 'nurse_consult'
       and source_row.source_type <> 'nurse_consult')
     or (current_job.interaction_type = 'ai_patient_session'
       and source_row.source_type <> 'ai_patient_session') then
    raise exception using errcode = '23514', message = 'AI job source no longer matches';
  end if;

  select * into target_note
  from public.care_notes
  where clinic_id = current_job.clinic_id
    and patient_id = current_job.patient_id
  for share;

  if not found then
    raise exception using errcode = 'P0002', message = 'Care Note not found';
  end if;

  output_entry_type := case current_job.interaction_type
    when 'doctor_consult' then 'ai_doctor_consult_summary'::public.entry_type
    when 'nurse_consult' then 'ai_nurse_consult_summary'::public.entry_type
    when 'ai_patient_session' then 'ai_patient_session_summary'::public.entry_type
  end;

  insert into public.entries (
    clinic_id,
    patient_id,
    care_note_id,
    author_id,
    author_role,
    entry_type,
    visibility,
    content,
    content_plaintext,
    source_record_id,
    occurred_at
  )
  values (
    current_job.clinic_id,
    current_job.patient_id,
    target_note.id,
    null,
    'system',
    output_entry_type,
    'internal',
    p_content,
    p_content,
    source_row.id,
    source_row.occurred_at
  )
  returning * into output_entry;

  insert into public.entry_versions (
    clinic_id,
    patient_id,
    entry_id,
    version_number,
    content_snapshot,
    changed_by,
    changed_by_role,
    change_reason
  )
  values (
    output_entry.clinic_id,
    output_entry.patient_id,
    output_entry.id,
    1,
    output_entry.content,
    null,
    'system',
    'Validated AI scribe output'
  )
  returning * into output_version;

  for suggestion in select value from jsonb_array_elements(p_highlights)
  loop
    if jsonb_typeof(suggestion) <> 'object' then
      raise exception using errcode = '22023', message = 'Invalid AI highlight metadata';
    end if;

    insert into public.highlights (
      clinic_id,
      patient_id,
      source_entry_id,
      source_version_id,
      source_start_offset,
      source_end_offset,
      quoted_text,
      normalized_claim,
      risk_level,
      risk_reason,
      score,
      status,
      generated_by,
      created_by
    )
    values (
      output_entry.clinic_id,
      output_entry.patient_id,
      output_entry.id,
      output_version.id,
      (suggestion->>'source_start_offset')::integer,
      (suggestion->>'source_end_offset')::integer,
      suggestion->>'quoted_text',
      suggestion->>'normalized_claim',
      (suggestion->>'risk_level')::public.highlight_risk_level,
      suggestion->>'risk_reason',
      (suggestion->>'score')::numeric,
      'suggested',
      'ai',
      null
    );
  end loop;

  insert into public.audit_events (
    clinic_id,
    patient_id,
    actor_id,
    actor_role,
    action,
    resource_type,
    resource_id,
    metadata
  )
  values (
    output_entry.clinic_id,
    output_entry.patient_id,
    null,
    'system',
    'ai_scribe_persisted',
    'entry',
    output_entry.id,
    jsonb_build_object(
      'job_id', current_job.id,
      'source_record_id', source_row.id,
      'interaction_type', current_job.interaction_type,
      'schema_version', p_schema_version,
      'provider', trim(p_provider_name),
      'model', trim(p_model_name),
      'highlight_count', jsonb_array_length(p_highlights)
    )
  );

  update public.ai_jobs
  set status = 'succeeded',
      completed_at = now(),
      lease_expires_at = null,
      safe_error_code = null,
      output_entry_id = output_entry.id,
      provider_name = trim(p_provider_name),
      model_name = trim(p_model_name),
      input_tokens = p_input_tokens,
      output_tokens = p_output_tokens
  where id = current_job.id
  returning * into completed_job;

  insert into public.ai_job_events (
    clinic_id, patient_id, job_id, event_kind, safe_metadata
  ) values (
    completed_job.clinic_id,
    completed_job.patient_id,
    completed_job.id,
    'completed',
    jsonb_build_object(
      'output_entry_id', completed_job.output_entry_id,
      'schema_version', p_schema_version,
      'model', trim(p_model_name)
    )
  );

  return completed_job;
end;
$$;

revoke all on function public.complete_ai_scribe_job(
  uuid, text, text, text, text, integer, integer, jsonb
) from public;
grant execute on function public.complete_ai_scribe_job(
  uuid, text, text, text, text, integer, integer, jsonb
) to service_role;

commit;
