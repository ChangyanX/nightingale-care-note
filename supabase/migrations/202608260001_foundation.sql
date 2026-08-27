begin;

create extension if not exists pgcrypto with schema extensions;

create type public.clinic_role as enum ('staff', 'clinician', 'admin');
create type public.author_role as enum ('patient', 'staff', 'clinician', 'system');
create type public.entry_visibility as enum ('internal', 'patient_facing');
create type public.entry_type as enum (
  'staff_note',
  'clinician_note',
  'patient_insight',
  'patient_summary',
  'patient_instruction',
  'ai_doctor_consult_summary',
  'ai_nurse_consult_summary',
  'ai_patient_session_summary',
  'system_event'
);
create type public.source_type as enum (
  'manual',
  'doctor_consult',
  'nurse_consult',
  'ai_patient_session',
  'system'
);
create type public.section_type as enum ('assessment', 'plan', 'staff_note', 'patient_instruction');
create type public.comment_status as enum ('open', 'resolved');

create table public.clinics (
  id uuid primary key default gen_random_uuid(),
  name text not null check (char_length(name) between 1 and 160),
  created_at timestamptz not null default now()
);

create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text not null check (char_length(display_name) between 1 and 160),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.clinic_memberships (
  clinic_id uuid not null references public.clinics(id) on delete cascade,
  profile_id uuid not null references public.profiles(id) on delete cascade,
  role public.clinic_role not null,
  created_at timestamptz not null default now(),
  primary key (clinic_id, profile_id, role)
);

create table public.patients (
  id uuid primary key default gen_random_uuid(),
  clinic_id uuid not null references public.clinics(id) on delete restrict,
  linked_profile_id uuid references public.profiles(id) on delete set null,
  synthetic_identifier text not null,
  display_name text not null check (char_length(display_name) between 1 and 160),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (clinic_id, synthetic_identifier),
  unique (id, clinic_id),
  unique (id, clinic_id, linked_profile_id)
);

create table public.source_records (
  id uuid primary key default gen_random_uuid(),
  clinic_id uuid not null,
  patient_id uuid not null,
  source_type public.source_type not null,
  external_reference text,
  storage_object_path text,
  occurred_at timestamptz not null default now(),
  metadata jsonb not null default '{}'::jsonb,
  created_by uuid references public.profiles(id) on delete set null,
  created_at timestamptz not null default now(),
  unique (id, clinic_id, patient_id),
  foreign key (patient_id, clinic_id)
    references public.patients(id, clinic_id) on delete cascade
);

create table public.care_notes (
  id uuid primary key default gen_random_uuid(),
  clinic_id uuid not null,
  patient_id uuid not null,
  current_version integer not null default 1 check (current_version > 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (clinic_id, patient_id),
  unique (id, clinic_id, patient_id),
  foreign key (patient_id, clinic_id)
    references public.patients(id, clinic_id) on delete cascade
);

create table public.entries (
  id uuid primary key default gen_random_uuid(),
  clinic_id uuid not null,
  patient_id uuid not null,
  care_note_id uuid not null,
  author_id uuid references public.profiles(id) on delete set null,
  author_role public.author_role not null,
  entry_type public.entry_type not null,
  visibility public.entry_visibility not null default 'internal',
  content text not null check (char_length(content) > 0),
  content_plaintext text not null check (char_length(content_plaintext) > 0),
  source_record_id uuid not null,
  source_start_offset integer check (source_start_offset is null or source_start_offset >= 0),
  source_end_offset integer check (source_end_offset is null or source_end_offset >= 0),
  current_version integer not null default 1 check (current_version > 0),
  occurred_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (id, clinic_id, patient_id),
  foreign key (care_note_id, clinic_id, patient_id)
    references public.care_notes(id, clinic_id, patient_id) on delete cascade,
  foreign key (source_record_id, clinic_id, patient_id)
    references public.source_records(id, clinic_id, patient_id) on delete restrict,
  check (
    (source_start_offset is null and source_end_offset is null)
    or (source_start_offset is not null and source_end_offset > source_start_offset)
  ),
  check (
    (entry_type in (
      'ai_doctor_consult_summary',
      'ai_nurse_consult_summary',
      'ai_patient_session_summary',
      'system_event'
    ) and author_role = 'system')
    or (entry_type not in (
      'ai_doctor_consult_summary',
      'ai_nurse_consult_summary',
      'ai_patient_session_summary',
      'system_event'
    ) and author_role <> 'system')
  )
);

comment on column public.entries.source_start_offset is
  'Half-open Unicode code-point offset over NFC-normalized content_plaintext.';
comment on column public.entries.source_end_offset is
  'Half-open Unicode code-point offset over NFC-normalized content_plaintext.';

create table public.note_sections (
  id uuid primary key default gen_random_uuid(),
  clinic_id uuid not null,
  patient_id uuid not null,
  care_note_id uuid not null,
  section_type public.section_type not null,
  owner_role public.author_role not null check (owner_role in ('staff', 'clinician', 'system')),
  created_by uuid references public.profiles(id) on delete set null,
  visibility public.entry_visibility not null default 'internal',
  content text not null default '',
  current_version integer not null default 1 check (current_version > 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (care_note_id, section_type),
  unique (id, clinic_id, patient_id),
  foreign key (care_note_id, clinic_id, patient_id)
    references public.care_notes(id, clinic_id, patient_id) on delete cascade,
  check (
    (section_type = 'staff_note' and owner_role = 'staff')
    or (section_type in ('assessment', 'plan', 'patient_instruction') and owner_role = 'clinician')
  ),
  check (section_type = 'patient_instruction' or visibility = 'internal')
);

create table public.entry_versions (
  id uuid primary key default gen_random_uuid(),
  clinic_id uuid not null,
  patient_id uuid not null,
  entry_id uuid not null,
  version_number integer not null check (version_number > 0),
  content_snapshot text not null,
  changed_by uuid references public.profiles(id) on delete set null,
  changed_by_role public.author_role not null,
  change_reason text,
  created_at timestamptz not null default now(),
  unique (entry_id, version_number),
  foreign key (entry_id, clinic_id, patient_id)
    references public.entries(id, clinic_id, patient_id) on delete cascade
);

create table public.section_versions (
  id uuid primary key default gen_random_uuid(),
  clinic_id uuid not null,
  patient_id uuid not null,
  section_id uuid not null,
  version_number integer not null check (version_number > 0),
  content_snapshot text not null,
  changed_by uuid references public.profiles(id) on delete set null,
  changed_by_role public.author_role not null,
  change_reason text,
  created_at timestamptz not null default now(),
  unique (section_id, version_number),
  foreign key (section_id, clinic_id, patient_id)
    references public.note_sections(id, clinic_id, patient_id) on delete cascade
);

create table public.comments (
  id uuid primary key default gen_random_uuid(),
  clinic_id uuid not null,
  patient_id uuid not null,
  entry_id uuid,
  section_id uuid,
  author_id uuid not null references public.profiles(id) on delete restrict,
  body text not null check (char_length(body) > 0),
  status public.comment_status not null default 'open',
  created_at timestamptz not null default now(),
  resolved_at timestamptz,
  check (num_nonnulls(entry_id, section_id) = 1),
  foreign key (entry_id, clinic_id, patient_id)
    references public.entries(id, clinic_id, patient_id) on delete cascade,
  foreign key (section_id, clinic_id, patient_id)
    references public.note_sections(id, clinic_id, patient_id) on delete cascade
);

create table public.audit_events (
  id uuid primary key default gen_random_uuid(),
  clinic_id uuid not null references public.clinics(id) on delete restrict,
  patient_id uuid,
  actor_id uuid references public.profiles(id) on delete set null,
  actor_role public.author_role not null,
  action text not null,
  resource_type text not null,
  resource_id uuid not null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  foreign key (patient_id, clinic_id)
    references public.patients(id, clinic_id) on delete restrict
);

create index memberships_profile_idx on public.clinic_memberships(profile_id, clinic_id);
create index patients_clinic_idx on public.patients(clinic_id, display_name);
create index sources_patient_time_idx on public.source_records(patient_id, occurred_at desc);
create index entries_timeline_idx on public.entries(patient_id, occurred_at desc, id);
create index entries_clinic_type_idx on public.entries(clinic_id, entry_type);
create index sections_patient_idx on public.note_sections(patient_id, section_type);
create index entry_versions_lookup_idx on public.entry_versions(entry_id, version_number desc);
create index section_versions_lookup_idx on public.section_versions(section_id, version_number desc);
create index comments_patient_status_idx on public.comments(patient_id, status, created_at desc);
create index audit_patient_time_idx on public.audit_events(patient_id, created_at desc);

create function public.set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger profiles_updated_at before update on public.profiles
for each row execute function public.set_updated_at();
create trigger patients_updated_at before update on public.patients
for each row execute function public.set_updated_at();
create trigger care_notes_updated_at before update on public.care_notes
for each row execute function public.set_updated_at();
create trigger entries_updated_at before update on public.entries
for each row execute function public.set_updated_at();
create trigger note_sections_updated_at before update on public.note_sections
for each row execute function public.set_updated_at();

create function public.has_clinic_role(target_clinic_id uuid, allowed_roles public.clinic_role[])
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from public.clinic_memberships membership
    where membership.clinic_id = target_clinic_id
      and membership.profile_id = (select auth.uid())
      and membership.role = any(allowed_roles)
  );
$$;

create function public.is_linked_patient(target_patient_id uuid, target_clinic_id uuid)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from public.patients patient
    where patient.id = target_patient_id
      and patient.clinic_id = target_clinic_id
      and patient.linked_profile_id = (select auth.uid())
  );
$$;

create function public.shares_clinic_with(target_profile_id uuid)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from public.clinic_memberships mine
    join public.clinic_memberships theirs on theirs.clinic_id = mine.clinic_id
    where mine.profile_id = (select auth.uid())
      and theirs.profile_id = target_profile_id
  );
$$;

revoke all on function public.has_clinic_role(uuid, public.clinic_role[]) from public;
revoke all on function public.is_linked_patient(uuid, uuid) from public;
revoke all on function public.shares_clinic_with(uuid) from public;
grant execute on function public.has_clinic_role(uuid, public.clinic_role[]) to authenticated;
grant execute on function public.is_linked_patient(uuid, uuid) to authenticated;
grant execute on function public.shares_clinic_with(uuid) to authenticated;

alter table public.clinics enable row level security;
alter table public.profiles enable row level security;
alter table public.clinic_memberships enable row level security;
alter table public.patients enable row level security;
alter table public.source_records enable row level security;
alter table public.care_notes enable row level security;
alter table public.entries enable row level security;
alter table public.note_sections enable row level security;
alter table public.entry_versions enable row level security;
alter table public.section_versions enable row level security;
alter table public.comments enable row level security;
alter table public.audit_events enable row level security;

revoke all on all tables in schema public from anon, authenticated;
grant usage on schema public to authenticated;
grant select on public.clinics, public.profiles, public.clinic_memberships,
  public.patients, public.source_records, public.care_notes, public.entries,
  public.note_sections, public.entry_versions, public.section_versions,
  public.comments, public.audit_events to authenticated;
grant insert, update, delete on public.clinic_memberships to authenticated;
grant insert on public.source_records, public.entries, public.note_sections,
  public.entry_versions, public.section_versions, public.comments,
  public.audit_events to authenticated;
grant update on public.entries, public.note_sections, public.comments to authenticated;

create policy clinics_select_member on public.clinics for select to authenticated
using (public.has_clinic_role(id, array['staff', 'clinician', 'admin']::public.clinic_role[]));

create policy profiles_select_related on public.profiles for select to authenticated
using (id = (select auth.uid()) or public.shares_clinic_with(id));

create policy memberships_select_related on public.clinic_memberships for select to authenticated
using (profile_id = (select auth.uid()) or public.has_clinic_role(clinic_id, array['staff', 'clinician', 'admin']::public.clinic_role[]));
create policy memberships_insert_admin on public.clinic_memberships for insert to authenticated
with check (public.has_clinic_role(clinic_id, array['admin']::public.clinic_role[]));
create policy memberships_update_admin on public.clinic_memberships for update to authenticated
using (public.has_clinic_role(clinic_id, array['admin']::public.clinic_role[]))
with check (public.has_clinic_role(clinic_id, array['admin']::public.clinic_role[]));
create policy memberships_delete_admin on public.clinic_memberships for delete to authenticated
using (public.has_clinic_role(clinic_id, array['admin']::public.clinic_role[]));

create policy patients_select_scoped on public.patients for select to authenticated
using (
  public.has_clinic_role(clinic_id, array['staff', 'clinician', 'admin']::public.clinic_role[])
  or linked_profile_id = (select auth.uid())
);

create policy sources_select_clinical on public.source_records for select to authenticated
using (public.has_clinic_role(clinic_id, array['staff', 'clinician', 'admin']::public.clinic_role[]));
create policy sources_insert_clinical on public.source_records for insert to authenticated
with check (
  created_by = (select auth.uid())
  and public.has_clinic_role(clinic_id, array['staff', 'clinician']::public.clinic_role[])
);
create policy sources_insert_patient on public.source_records for insert to authenticated
with check (
  created_by = (select auth.uid())
  and source_type = 'manual'
  and public.is_linked_patient(patient_id, clinic_id)
);

create policy care_notes_select_scoped on public.care_notes for select to authenticated
using (
  public.has_clinic_role(clinic_id, array['staff', 'clinician', 'admin']::public.clinic_role[])
  or public.is_linked_patient(patient_id, clinic_id)
);

create policy entries_select_scoped on public.entries for select to authenticated
using (
  public.has_clinic_role(clinic_id, array['staff', 'clinician', 'admin']::public.clinic_role[])
  or (
    public.is_linked_patient(patient_id, clinic_id)
    and (
      (visibility = 'patient_facing' and entry_type in ('patient_summary', 'patient_instruction'))
      or (author_id = (select auth.uid()) and entry_type = 'patient_insight')
    )
  )
);
create policy entries_insert_staff on public.entries for insert to authenticated
with check (
  author_id = (select auth.uid())
  and author_role = 'staff'
  and entry_type = 'staff_note'
  and visibility = 'internal'
  and public.has_clinic_role(clinic_id, array['staff']::public.clinic_role[])
);
create policy entries_insert_clinician on public.entries for insert to authenticated
with check (
  author_id = (select auth.uid())
  and author_role = 'clinician'
  and entry_type in ('clinician_note', 'patient_summary', 'patient_instruction')
  and public.has_clinic_role(clinic_id, array['clinician']::public.clinic_role[])
);
create policy entries_insert_patient on public.entries for insert to authenticated
with check (
  author_id = (select auth.uid())
  and author_role = 'patient'
  and entry_type = 'patient_insight'
  and visibility = 'internal'
  and public.is_linked_patient(patient_id, clinic_id)
);
create policy entries_update_staff on public.entries for update to authenticated
using (author_id = (select auth.uid()) and author_role = 'staff' and entry_type = 'staff_note')
with check (
  author_id = (select auth.uid())
  and author_role = 'staff'
  and entry_type = 'staff_note'
  and visibility = 'internal'
  and public.has_clinic_role(clinic_id, array['staff']::public.clinic_role[])
);
create policy entries_update_clinician on public.entries for update to authenticated
using (author_id = (select auth.uid()) and author_role = 'clinician')
with check (
  author_id = (select auth.uid())
  and author_role = 'clinician'
  and entry_type in ('clinician_note', 'patient_summary', 'patient_instruction')
  and public.has_clinic_role(clinic_id, array['clinician']::public.clinic_role[])
);

create policy sections_select_scoped on public.note_sections for select to authenticated
using (
  public.has_clinic_role(clinic_id, array['staff', 'clinician', 'admin']::public.clinic_role[])
  or (public.is_linked_patient(patient_id, clinic_id) and section_type = 'patient_instruction' and visibility = 'patient_facing')
);
create policy sections_insert_staff on public.note_sections for insert to authenticated
with check (
  created_by = (select auth.uid())
  and owner_role = 'staff'
  and section_type = 'staff_note'
  and public.has_clinic_role(clinic_id, array['staff']::public.clinic_role[])
);
create policy sections_insert_clinician on public.note_sections for insert to authenticated
with check (
  created_by = (select auth.uid())
  and owner_role = 'clinician'
  and section_type in ('assessment', 'plan', 'patient_instruction')
  and public.has_clinic_role(clinic_id, array['clinician']::public.clinic_role[])
);
create policy sections_update_staff on public.note_sections for update to authenticated
using (owner_role = 'staff' and public.has_clinic_role(clinic_id, array['staff']::public.clinic_role[]))
with check (owner_role = 'staff' and section_type = 'staff_note' and public.has_clinic_role(clinic_id, array['staff']::public.clinic_role[]));
create policy sections_update_clinician on public.note_sections for update to authenticated
using (owner_role = 'clinician' and public.has_clinic_role(clinic_id, array['clinician']::public.clinic_role[]))
with check (owner_role = 'clinician' and section_type in ('assessment', 'plan', 'patient_instruction') and public.has_clinic_role(clinic_id, array['clinician']::public.clinic_role[]));

create policy entry_versions_select_clinical on public.entry_versions for select to authenticated
using (public.has_clinic_role(clinic_id, array['staff', 'clinician', 'admin']::public.clinic_role[]));
create policy entry_versions_insert_owner on public.entry_versions for insert to authenticated
with check (
  changed_by = (select auth.uid())
  and public.has_clinic_role(clinic_id, array['staff', 'clinician']::public.clinic_role[])
);

create policy section_versions_select_clinical on public.section_versions for select to authenticated
using (public.has_clinic_role(clinic_id, array['staff', 'clinician', 'admin']::public.clinic_role[]));
create policy section_versions_insert_owner on public.section_versions for insert to authenticated
with check (
  changed_by = (select auth.uid())
  and public.has_clinic_role(clinic_id, array['staff', 'clinician']::public.clinic_role[])
);

create policy comments_select_clinical on public.comments for select to authenticated
using (public.has_clinic_role(clinic_id, array['staff', 'clinician', 'admin']::public.clinic_role[]));
create policy comments_insert_clinical on public.comments for insert to authenticated
with check (
  author_id = (select auth.uid())
  and public.has_clinic_role(clinic_id, array['staff', 'clinician']::public.clinic_role[])
);
create policy comments_update_author on public.comments for update to authenticated
using (author_id = (select auth.uid()))
with check (
  author_id = (select auth.uid())
  and public.has_clinic_role(clinic_id, array['staff', 'clinician']::public.clinic_role[])
);

create policy audit_select_clinical on public.audit_events for select to authenticated
using (public.has_clinic_role(clinic_id, array['staff', 'clinician', 'admin']::public.clinic_role[]));
create policy audit_insert_actor on public.audit_events for insert to authenticated
with check (
  actor_id = (select auth.uid())
  and public.has_clinic_role(clinic_id, array['staff', 'clinician']::public.clinic_role[])
);

alter table public.entry_versions force row level security;
alter table public.section_versions force row level security;
alter table public.audit_events force row level security;

commit;
