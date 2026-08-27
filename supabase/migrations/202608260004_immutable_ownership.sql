begin;

create function public.protect_entry_identity()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if row(
    new.id,
    new.clinic_id,
    new.patient_id,
    new.care_note_id,
    new.author_id,
    new.author_role,
    new.entry_type,
    new.visibility,
    new.source_record_id,
    new.source_start_offset,
    new.source_end_offset,
    new.occurred_at,
    new.created_at
  ) is distinct from row(
    old.id,
    old.clinic_id,
    old.patient_id,
    old.care_note_id,
    old.author_id,
    old.author_role,
    old.entry_type,
    old.visibility,
    old.source_record_id,
    old.source_start_offset,
    old.source_end_offset,
    old.occurred_at,
    old.created_at
  ) then
    raise exception using errcode = '42501', message = 'Entry ownership and provenance are immutable';
  end if;
  return new;
end;
$$;

create trigger protect_entry_identity_before_update
before update on public.entries
for each row execute function public.protect_entry_identity();

create function public.protect_section_identity()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if row(
    new.id,
    new.clinic_id,
    new.patient_id,
    new.care_note_id,
    new.section_type,
    new.owner_role,
    new.created_by,
    new.created_at
  ) is distinct from row(
    old.id,
    old.clinic_id,
    old.patient_id,
    old.care_note_id,
    old.section_type,
    old.owner_role,
    old.created_by,
    old.created_at
  ) then
    raise exception using errcode = '42501', message = 'Section ownership is immutable';
  end if;
  return new;
end;
$$;

create trigger protect_section_identity_before_update
before update on public.note_sections
for each row execute function public.protect_section_identity();

create function public.protect_comment_identity()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if row(
    new.id,
    new.clinic_id,
    new.patient_id,
    new.entry_id,
    new.section_id,
    new.author_id,
    new.created_at
  ) is distinct from row(
    old.id,
    old.clinic_id,
    old.patient_id,
    old.entry_id,
    old.section_id,
    old.author_id,
    old.created_at
  ) then
    raise exception using errcode = '42501', message = 'Comment ownership and target are immutable';
  end if;
  return new;
end;
$$;

create trigger protect_comment_identity_before_update
before update on public.comments
for each row execute function public.protect_comment_identity();

commit;
