begin;

create policy entry_versions_insert_patient on public.entry_versions for insert to authenticated
with check (
  changed_by = (select auth.uid())
  and changed_by_role = 'patient'
  and public.is_linked_patient(patient_id, clinic_id)
);

drop policy audit_insert_actor on public.audit_events;
create policy audit_insert_actor on public.audit_events for insert to authenticated
with check (
  actor_id = (select auth.uid())
  and (
    public.has_clinic_role(clinic_id, array['staff', 'clinician']::public.clinic_role[])
    or (actor_role = 'patient' and patient_id is not null and public.is_linked_patient(patient_id, clinic_id))
  )
);

create function public.create_manual_entry(
  p_patient_id uuid,
  p_entry_type public.entry_type,
  p_visibility public.entry_visibility,
  p_content text,
  p_occurred_at timestamptz default now()
)
returns public.entries
language plpgsql
security invoker
set search_path = ''
as $$
declare
  target_patient public.patients;
  target_care_note public.care_notes;
  new_source public.source_records;
  new_entry public.entries;
  caller_role public.author_role;
begin
  if char_length(trim(p_content)) = 0 then
    raise exception using errcode = '22023', message = 'Entry content cannot be empty';
  end if;

  select * into target_patient
  from public.patients
  where id = p_patient_id;

  if not found then
    raise exception using errcode = 'P0002', message = 'Patient not found';
  end if;

  select * into target_care_note
  from public.care_notes
  where patient_id = target_patient.id
    and clinic_id = target_patient.clinic_id;

  if p_entry_type = 'staff_note'
     and p_visibility = 'internal'
     and public.has_clinic_role(target_patient.clinic_id, array['staff']::public.clinic_role[]) then
    caller_role := 'staff';
  elsif p_entry_type in ('clinician_note', 'patient_summary', 'patient_instruction')
     and public.has_clinic_role(target_patient.clinic_id, array['clinician']::public.clinic_role[]) then
    caller_role := 'clinician';
  elsif p_entry_type = 'patient_insight'
     and p_visibility = 'internal'
     and public.is_linked_patient(target_patient.id, target_patient.clinic_id) then
    caller_role := 'patient';
  else
    raise exception using errcode = '42501', message = 'Role cannot create this entry type';
  end if;

  insert into public.source_records (
    clinic_id,
    patient_id,
    source_type,
    external_reference,
    occurred_at,
    metadata,
    created_by
  )
  values (
    target_patient.clinic_id,
    target_patient.id,
    'manual',
    'manual:' || extensions.gen_random_uuid()::text,
    p_occurred_at,
    jsonb_build_object('synthetic', true),
    auth.uid()
  )
  returning * into new_source;

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
    target_patient.clinic_id,
    target_patient.id,
    target_care_note.id,
    auth.uid(),
    caller_role,
    p_entry_type,
    p_visibility,
    p_content,
    p_content,
    new_source.id,
    p_occurred_at
  )
  returning * into new_entry;

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
    new_entry.clinic_id,
    new_entry.patient_id,
    new_entry.id,
    1,
    new_entry.content,
    auth.uid(),
    caller_role,
    'Created entry'
  );

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
    new_entry.clinic_id,
    new_entry.patient_id,
    auth.uid(),
    caller_role,
    'created',
    'entry',
    new_entry.id,
    jsonb_build_object('version', 1, 'entry_type', new_entry.entry_type)
  );

  return new_entry;
end;
$$;

create function public.update_entry(
  p_entry_id uuid,
  p_expected_version integer,
  p_content text,
  p_change_reason text default null
)
returns public.entries
language plpgsql
security invoker
set search_path = ''
as $$
declare
  current_entry public.entries;
  updated_entry public.entries;
begin
  if char_length(trim(p_content)) = 0 then
    raise exception using errcode = '22023', message = 'Entry content cannot be empty';
  end if;

  select * into current_entry
  from public.entries
  where id = p_entry_id
  for update;

  if not found then
    raise exception using errcode = 'P0002', message = 'Entry not found';
  end if;

  if current_entry.current_version <> p_expected_version then
    raise exception using
      errcode = '40001',
      message = 'Entry version conflict',
      detail = 'Expected version ' || p_expected_version || ', current version ' || current_entry.current_version;
  end if;

  if current_entry.author_id <> auth.uid()
     or current_entry.author_role not in ('staff', 'clinician') then
    raise exception using errcode = '42501', message = 'Only the owning role can edit this entry';
  end if;

  update public.entries
  set
    content = p_content,
    content_plaintext = p_content,
    current_version = current_version + 1
  where id = p_entry_id
  returning * into updated_entry;

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
    updated_entry.clinic_id,
    updated_entry.patient_id,
    updated_entry.id,
    updated_entry.current_version,
    updated_entry.content,
    auth.uid(),
    updated_entry.author_role,
    p_change_reason
  );

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
    updated_entry.clinic_id,
    updated_entry.patient_id,
    auth.uid(),
    updated_entry.author_role,
    'updated',
    'entry',
    updated_entry.id,
    jsonb_build_object('version', updated_entry.current_version)
  );

  return updated_entry;
end;
$$;

revoke all on function public.create_manual_entry(uuid, public.entry_type, public.entry_visibility, text, timestamptz) from public;
revoke all on function public.update_entry(uuid, integer, text, text) from public;
grant execute on function public.create_manual_entry(uuid, public.entry_type, public.entry_visibility, text, timestamptz) to authenticated;
grant execute on function public.update_entry(uuid, integer, text, text) to authenticated;

commit;
