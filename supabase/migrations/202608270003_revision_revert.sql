begin;

create function public.update_section(
  p_section_id uuid,
  p_expected_version integer,
  p_content text,
  p_change_reason text default null
)
returns public.note_sections
language plpgsql
security invoker
set search_path = ''
as $$
declare
  current_section public.note_sections;
  updated_section public.note_sections;
begin
  if p_expected_version < 1 or char_length(trim(p_content)) = 0 then
    raise exception using errcode = '22023', message = 'Invalid section update';
  end if;

  select * into current_section
  from public.note_sections
  where id = p_section_id
  for update;

  if not found then
    raise exception using errcode = 'P0002', message = 'Section not found';
  end if;

  if current_section.current_version <> p_expected_version then
    raise exception using
      errcode = '40001',
      message = 'Section version conflict',
      detail = 'Expected version ' || p_expected_version
        || ', current version ' || current_section.current_version;
  end if;

  if (current_section.owner_role = 'staff'
      and not public.has_clinic_role(
        current_section.clinic_id,
        array['staff']::public.clinic_role[]
      ))
     or (current_section.owner_role = 'clinician'
      and not public.has_clinic_role(
        current_section.clinic_id,
        array['clinician']::public.clinic_role[]
      )) then
    raise exception using errcode = '42501', message = 'Role cannot update this section';
  end if;

  update public.note_sections
  set content = p_content,
      current_version = current_version + 1
  where id = current_section.id
  returning * into updated_section;

  insert into public.section_versions (
    clinic_id, patient_id, section_id, version_number, content_snapshot,
    changed_by, changed_by_role, change_reason
  )
  values (
    updated_section.clinic_id,
    updated_section.patient_id,
    updated_section.id,
    updated_section.current_version,
    updated_section.content,
    auth.uid(),
    updated_section.owner_role,
    p_change_reason
  );

  insert into public.audit_events (
    clinic_id, patient_id, actor_id, actor_role, action,
    resource_type, resource_id, metadata
  )
  values (
    updated_section.clinic_id,
    updated_section.patient_id,
    auth.uid(),
    updated_section.owner_role,
    'updated',
    'section',
    updated_section.id,
    jsonb_build_object('version', updated_section.current_version)
  );

  return updated_section;
end;
$$;

create function public.revert_entry(
  p_entry_id uuid,
  p_source_version integer,
  p_expected_version integer,
  p_change_reason text default null
)
returns public.entries
language plpgsql
security invoker
set search_path = ''
as $$
declare
  current_entry public.entries;
  source_snapshot public.entry_versions;
  reverted_entry public.entries;
begin
  if p_source_version < 1 or p_expected_version < 1 then
    raise exception using errcode = '22023', message = 'Invalid entry version';
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
      detail = 'Expected version ' || p_expected_version
        || ', current version ' || current_entry.current_version;
  end if;

  if current_entry.author_id <> auth.uid()
     or current_entry.author_role not in ('staff', 'clinician') then
    raise exception using errcode = '42501', message = 'Only the owning author can revert';
  end if;

  select * into source_snapshot
  from public.entry_versions
  where entry_id = current_entry.id
    and clinic_id = current_entry.clinic_id
    and patient_id = current_entry.patient_id
    and version_number = p_source_version;

  if not found then
    raise exception using errcode = 'P0002', message = 'Entry version not found';
  end if;

  update public.entries
  set content = source_snapshot.content_snapshot,
      content_plaintext = source_snapshot.content_snapshot,
      current_version = current_version + 1
  where id = current_entry.id
  returning * into reverted_entry;

  insert into public.entry_versions (
    clinic_id, patient_id, entry_id, version_number, content_snapshot,
    changed_by, changed_by_role, change_reason
  )
  values (
    reverted_entry.clinic_id,
    reverted_entry.patient_id,
    reverted_entry.id,
    reverted_entry.current_version,
    reverted_entry.content,
    auth.uid(),
    reverted_entry.author_role,
    coalesce(p_change_reason, 'Reverted to version ' || p_source_version)
  );

  insert into public.audit_events (
    clinic_id, patient_id, actor_id, actor_role, action,
    resource_type, resource_id, metadata
  )
  values (
    reverted_entry.clinic_id,
    reverted_entry.patient_id,
    auth.uid(),
    reverted_entry.author_role,
    'reverted',
    'entry',
    reverted_entry.id,
    jsonb_build_object(
      'source_version', p_source_version,
      'new_version', reverted_entry.current_version
    )
  );

  return reverted_entry;
end;
$$;

create function public.revert_section(
  p_section_id uuid,
  p_source_version integer,
  p_expected_version integer,
  p_change_reason text default null
)
returns public.note_sections
language plpgsql
security invoker
set search_path = ''
as $$
declare
  current_section public.note_sections;
  source_snapshot public.section_versions;
  reverted_section public.note_sections;
begin
  if p_source_version < 1 or p_expected_version < 1 then
    raise exception using errcode = '22023', message = 'Invalid section version';
  end if;

  select * into current_section
  from public.note_sections
  where id = p_section_id
  for update;

  if not found then
    raise exception using errcode = 'P0002', message = 'Section not found';
  end if;

  if current_section.current_version <> p_expected_version then
    raise exception using
      errcode = '40001',
      message = 'Section version conflict',
      detail = 'Expected version ' || p_expected_version
        || ', current version ' || current_section.current_version;
  end if;

  if (current_section.owner_role = 'staff'
      and not public.has_clinic_role(
        current_section.clinic_id,
        array['staff']::public.clinic_role[]
      ))
     or (current_section.owner_role = 'clinician'
      and not public.has_clinic_role(
        current_section.clinic_id,
        array['clinician']::public.clinic_role[]
      )) then
    raise exception using errcode = '42501', message = 'Role cannot revert this section';
  end if;

  select * into source_snapshot
  from public.section_versions
  where section_id = current_section.id
    and clinic_id = current_section.clinic_id
    and patient_id = current_section.patient_id
    and version_number = p_source_version;

  if not found then
    raise exception using errcode = 'P0002', message = 'Section version not found';
  end if;

  update public.note_sections
  set content = source_snapshot.content_snapshot,
      current_version = current_version + 1
  where id = current_section.id
  returning * into reverted_section;

  insert into public.section_versions (
    clinic_id, patient_id, section_id, version_number, content_snapshot,
    changed_by, changed_by_role, change_reason
  )
  values (
    reverted_section.clinic_id,
    reverted_section.patient_id,
    reverted_section.id,
    reverted_section.current_version,
    reverted_section.content,
    auth.uid(),
    reverted_section.owner_role,
    coalesce(p_change_reason, 'Reverted to version ' || p_source_version)
  );

  insert into public.audit_events (
    clinic_id, patient_id, actor_id, actor_role, action,
    resource_type, resource_id, metadata
  )
  values (
    reverted_section.clinic_id,
    reverted_section.patient_id,
    auth.uid(),
    reverted_section.owner_role,
    'reverted',
    'section',
    reverted_section.id,
    jsonb_build_object(
      'source_version', p_source_version,
      'new_version', reverted_section.current_version
    )
  );

  return reverted_section;
end;
$$;

revoke all on function public.update_section(uuid, integer, text, text) from public;
revoke all on function public.revert_entry(uuid, integer, integer, text) from public;
revoke all on function public.revert_section(uuid, integer, integer, text) from public;
grant execute on function public.update_section(uuid, integer, text, text) to authenticated;
grant execute on function public.revert_entry(uuid, integer, integer, text) to authenticated;
grant execute on function public.revert_section(uuid, integer, integer, text) to authenticated;

commit;
