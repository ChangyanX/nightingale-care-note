begin;

alter table public.comments
add column parent_comment_id uuid,
add column assigned_to uuid references public.profiles(id) on delete set null,
add constraint comments_identity_key unique (id, clinic_id, patient_id),
add constraint comments_parent_same_patient_fkey
  foreign key (parent_comment_id, clinic_id, patient_id)
  references public.comments(id, clinic_id, patient_id) on delete cascade,
add constraint comments_resolution_consistent check (
  (status = 'resolved' and resolved_at is not null)
  or (status = 'open' and resolved_at is null)
);

create function public.validate_comment_collaboration()
returns trigger
language plpgsql
set search_path = ''
as $$
declare
  parent_comment public.comments;
begin
  if new.assigned_to is not null
     and not public.is_profile_in_clinic(new.assigned_to, new.clinic_id) then
    raise exception using errcode = '23514', message = 'Comment assignee must belong to the clinic';
  end if;

  if new.parent_comment_id is not null then
    select * into parent_comment
    from public.comments
    where id = new.parent_comment_id
      and clinic_id = new.clinic_id
      and patient_id = new.patient_id;

    if not found
       or row(parent_comment.entry_id, parent_comment.section_id)
          is distinct from row(new.entry_id, new.section_id) then
      raise exception using errcode = '23514', message = 'Reply must share its parent target';
    end if;
  end if;

  return new;
end;
$$;

create trigger validate_comment_collaboration_before_write
before insert or update on public.comments
for each row execute function public.validate_comment_collaboration();

create or replace function public.protect_comment_identity()
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
    new.parent_comment_id,
    new.author_id,
    new.created_at
  ) is distinct from row(
    old.id,
    old.clinic_id,
    old.patient_id,
    old.entry_id,
    old.section_id,
    old.parent_comment_id,
    old.author_id,
    old.created_at
  ) then
    raise exception using errcode = '42501', message = 'Comment ownership and target are immutable';
  end if;
  return new;
end;
$$;

create table public.mentions (
  id uuid primary key default gen_random_uuid(),
  clinic_id uuid not null,
  patient_id uuid not null,
  comment_id uuid not null,
  mentioned_profile_id uuid not null references public.profiles(id) on delete cascade,
  created_by uuid not null references public.profiles(id) on delete restrict,
  created_at timestamptz not null default now(),
  unique (comment_id, mentioned_profile_id),
  foreign key (comment_id, clinic_id, patient_id)
    references public.comments(id, clinic_id, patient_id) on delete cascade
);

create index mentions_profile_created_idx
on public.mentions(mentioned_profile_id, created_at desc);

create function public.validate_mention_clinic()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if not public.is_profile_in_clinic(new.mentioned_profile_id, new.clinic_id) then
    raise exception using errcode = '23514', message = 'Mentioned profile must belong to the clinic';
  end if;
  return new;
end;
$$;

create trigger validate_mention_clinic_before_insert
before insert on public.mentions
for each row execute function public.validate_mention_clinic();

alter table public.mentions enable row level security;
revoke all on public.mentions from anon, authenticated;
grant select, insert on public.mentions to authenticated;

create policy mentions_select_clinical
on public.mentions for select to authenticated
using (
  public.has_clinic_role(
    clinic_id,
    array['staff', 'clinician', 'admin']::public.clinic_role[]
  )
);

create policy mentions_insert_clinical
on public.mentions for insert to authenticated
with check (
  created_by = (select auth.uid())
  and public.has_clinic_role(
    clinic_id,
    array['staff', 'clinician']::public.clinic_role[]
  )
  and public.is_profile_in_clinic(mentioned_profile_id, clinic_id)
);

create type public.highlight_status as enum ('suggested', 'accepted', 'rejected');
create type public.highlight_risk_level as enum ('information', 'attention', 'critical');
create type public.highlight_generator as enum ('rule', 'ai', 'clinician');

alter table public.entry_versions
add constraint entry_versions_provenance_identity_key
unique (id, clinic_id, patient_id, entry_id);

create table public.highlights (
  id uuid primary key default gen_random_uuid(),
  clinic_id uuid not null,
  patient_id uuid not null,
  source_entry_id uuid not null,
  source_version_id uuid not null,
  source_start_offset integer not null check (source_start_offset >= 0),
  source_end_offset integer not null check (source_end_offset > source_start_offset),
  quoted_text text not null check (char_length(quoted_text) > 0),
  normalized_claim text not null check (char_length(normalized_claim) between 1 and 1000),
  risk_level public.highlight_risk_level not null,
  risk_reason text not null check (char_length(risk_reason) between 1 and 500),
  score numeric(6, 3) not null check (score between 0 and 100),
  status public.highlight_status not null default 'suggested',
  generated_by public.highlight_generator not null,
  created_by uuid references public.profiles(id) on delete set null,
  reviewed_by uuid references public.profiles(id) on delete set null,
  reviewed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (id, clinic_id, patient_id),
  foreign key (patient_id, clinic_id)
    references public.patients(id, clinic_id) on delete cascade,
  foreign key (source_entry_id, clinic_id, patient_id)
    references public.entries(id, clinic_id, patient_id) on delete restrict,
  foreign key (source_version_id, clinic_id, patient_id, source_entry_id)
    references public.entry_versions(id, clinic_id, patient_id, entry_id) on delete restrict,
  check (
    (status = 'suggested' and reviewed_by is null and reviewed_at is null)
    or (status in ('accepted', 'rejected') and reviewed_by is not null and reviewed_at is not null)
  )
);

comment on column public.highlights.source_start_offset is
  'Zero-based half-open Unicode code-point offset over NFC-normalized historical content.';
comment on column public.highlights.source_end_offset is
  'Zero-based half-open Unicode code-point offset over NFC-normalized historical content.';

create index highlights_patient_status_score_idx
on public.highlights(patient_id, status, score desc, created_at desc);
create index highlights_source_idx
on public.highlights(source_entry_id, source_version_id);

create trigger highlights_updated_at before update on public.highlights
for each row execute function public.set_updated_at();

create function public.validate_highlight_provenance()
returns trigger
language plpgsql
set search_path = ''
as $$
declare
  historical_content text;
begin
  select version.content_snapshot into historical_content
  from public.entry_versions version
  where version.id = new.source_version_id
    and version.entry_id = new.source_entry_id
    and version.clinic_id = new.clinic_id
    and version.patient_id = new.patient_id;

  if not found then
    raise exception using errcode = '23503', message = 'Highlight source version is not resolvable';
  end if;

  if new.source_end_offset > char_length(historical_content)
     or substring(
       historical_content
       from new.source_start_offset + 1
       for new.source_end_offset - new.source_start_offset
     ) <> new.quoted_text then
    raise exception using errcode = '23514', message = 'Highlight quote does not match source span';
  end if;

  return new;
end;
$$;

create trigger validate_highlight_provenance_before_write
before insert or update on public.highlights
for each row execute function public.validate_highlight_provenance();

create function public.protect_highlight_provenance()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if row(
    new.id,
    new.clinic_id,
    new.patient_id,
    new.source_entry_id,
    new.source_version_id,
    new.source_start_offset,
    new.source_end_offset,
    new.quoted_text,
    new.normalized_claim,
    new.risk_level,
    new.risk_reason,
    new.score,
    new.generated_by,
    new.created_by,
    new.created_at
  ) is distinct from row(
    old.id,
    old.clinic_id,
    old.patient_id,
    old.source_entry_id,
    old.source_version_id,
    old.source_start_offset,
    old.source_end_offset,
    old.quoted_text,
    old.normalized_claim,
    old.risk_level,
    old.risk_reason,
    old.score,
    old.generated_by,
    old.created_by,
    old.created_at
  ) then
    raise exception using errcode = '42501', message = 'Highlight provenance is immutable';
  end if;
  return new;
end;
$$;

create trigger protect_highlight_provenance_before_update
before update on public.highlights
for each row execute function public.protect_highlight_provenance();

alter table public.highlights enable row level security;
revoke all on public.highlights from anon, authenticated;
grant select, insert, update on public.highlights to authenticated;

create policy highlights_select_clinical
on public.highlights for select to authenticated
using (
  public.has_clinic_role(
    clinic_id,
    array['staff', 'clinician', 'admin']::public.clinic_role[]
  )
);

create policy highlights_insert_clinician
on public.highlights for insert to authenticated
with check (
  created_by = (select auth.uid())
  and generated_by = 'clinician'
  and status = 'accepted'
  and reviewed_by = (select auth.uid())
  and reviewed_at is not null
  and public.has_clinic_role(clinic_id, array['clinician']::public.clinic_role[])
);

create policy highlights_update_clinician_review
on public.highlights for update to authenticated
using (public.has_clinic_role(clinic_id, array['clinician']::public.clinic_role[]))
with check (
  status in ('accepted', 'rejected')
  and reviewed_by = (select auth.uid())
  and reviewed_at is not null
  and public.has_clinic_role(clinic_id, array['clinician']::public.clinic_role[])
);

alter table public.comments replica identity full;
alter table public.mentions replica identity full;
alter table public.highlights replica identity full;

do $$
declare
  realtime_table text;
begin
  if exists (select 1 from pg_publication where pubname = 'supabase_realtime') then
    foreach realtime_table in array array['comments', 'mentions', 'highlights']
    loop
      if not exists (
        select 1
        from pg_publication_tables
        where pubname = 'supabase_realtime'
          and schemaname = 'public'
          and tablename = realtime_table
      ) then
        execute format(
          'alter publication supabase_realtime add table public.%I',
          realtime_table
        );
      end if;
    end loop;
  end if;
end;
$$;

commit;
