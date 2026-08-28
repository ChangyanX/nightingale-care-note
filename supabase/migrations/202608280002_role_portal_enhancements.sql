begin;

alter table public.profiles
  add column preferred_name text,
  add column birth_date date,
  add column avatar_path text,
  add column avatar_mime_type text;

update public.profiles set preferred_name = display_name where preferred_name is null;

alter table public.profiles
  alter column preferred_name set not null,
  add constraint profiles_preferred_name_length
    check (char_length(preferred_name) between 1 and 80),
  add constraint profiles_birth_date_reasonable
    check (birth_date is null or birth_date between date '1900-01-01' and current_date),
  add constraint profiles_avatar_mime_type_safe
    check (avatar_mime_type is null or avatar_mime_type in ('image/png', 'image/jpeg', 'image/webp')),
  add constraint profiles_avatar_fields_together
    check ((avatar_path is null) = (avatar_mime_type is null));

create function public.set_profile_preferred_name()
returns trigger language plpgsql set search_path = '' as $$
begin
  new.preferred_name := coalesce(nullif(trim(new.preferred_name), ''), new.display_name);
  return new;
end;
$$;
create trigger profiles_preferred_name_before_write
before insert or update on public.profiles
for each row execute function public.set_profile_preferred_name();

alter table public.notification_outbox add column read_at timestamptz;
alter table public.notification_outbox drop constraint notification_outbox_event_type_check;
alter table public.notification_outbox add constraint notification_outbox_event_type_check
  check (event_type in (
    'mention', 'assignment', 'ai_job_completed', 'care_update',
    'appointment_update', 'report_released'
  ));

create function public.validate_notification_recipient_scope()
returns trigger language plpgsql set search_path = '' as $$
declare recipient_is_member boolean;
declare recipient_is_patient boolean;
begin
  recipient_is_member := exists (
    select 1 from public.clinic_memberships membership
    where membership.clinic_id = new.clinic_id
      and membership.profile_id = new.recipient_id
  );
  recipient_is_patient := exists (
    select 1 from public.patients patient
    where patient.clinic_id = new.clinic_id
      and patient.id = new.patient_id
      and patient.linked_profile_id = new.recipient_id
  );
  if not recipient_is_member and not recipient_is_patient then
    raise exception using errcode = '23514', message = 'Notification recipient is outside clinic scope';
  end if;
  if recipient_is_patient and not recipient_is_member and (
    new.event_type not in ('care_update', 'appointment_update', 'report_released')
    or new.resource_type not in (
      'patient_summary', 'patient_instruction', 'appointment_request', 'patient_report'
    )
  ) then
    raise exception using errcode = '23514', message = 'Patient notification target is restricted';
  end if;
  return new;
end;
$$;
create trigger notification_recipient_scope_before_write
before insert or update on public.notification_outbox
for each row execute function public.validate_notification_recipient_scope();

create type public.appointment_request_status as enum (
  'requested', 'confirmed', 'declined', 'cancelled'
);
create type public.patient_report_status as enum ('preparing', 'available', 'withdrawn');

create table public.appointment_requests (
  id uuid primary key default gen_random_uuid(),
  clinic_id uuid not null,
  patient_id uuid not null,
  requested_by uuid not null references public.profiles(id) on delete restrict,
  preferred_date date not null check (preferred_date >= current_date),
  time_preference text not null check (time_preference in ('morning', 'afternoon', 'either')),
  reason_category text not null check (reason_category in ('follow_up', 'new_symptom', 'medication', 'other')),
  note text check (note is null or char_length(note) <= 500),
  status public.appointment_request_status not null default 'requested',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (id, clinic_id, patient_id),
  foreign key (patient_id, clinic_id) references public.patients(id, clinic_id) on delete cascade
);

create table public.patient_reports (
  id uuid primary key default gen_random_uuid(),
  clinic_id uuid not null,
  patient_id uuid not null,
  title text not null check (char_length(title) between 1 and 160),
  report_type text not null check (report_type in ('lab', 'imaging', 'care_plan', 'other')),
  status public.patient_report_status not null default 'preparing',
  released_at timestamptz,
  released_by uuid references public.profiles(id) on delete set null,
  patient_safe_summary text check (patient_safe_summary is null or char_length(patient_safe_summary) <= 2000),
  created_at timestamptz not null default now(),
  unique (id, clinic_id, patient_id),
  foreign key (patient_id, clinic_id) references public.patients(id, clinic_id) on delete cascade,
  check ((status = 'available' and released_at is not null and patient_safe_summary is not null)
    or status <> 'available')
);

create table public.patient_observations (
  id uuid primary key default gen_random_uuid(),
  clinic_id uuid not null,
  patient_id uuid not null,
  recorded_by uuid references public.profiles(id) on delete set null,
  observation_type text not null check (observation_type in ('peak_flow', 'sleep_hours', 'symptom_score')),
  value numeric(10,2) not null,
  unit text not null check (char_length(unit) between 1 and 30),
  observed_at timestamptz not null,
  created_at timestamptz not null default now(),
  unique (id, clinic_id, patient_id),
  foreign key (patient_id, clinic_id) references public.patients(id, clinic_id) on delete cascade
);

create index appointment_requests_patient_time_idx
  on public.appointment_requests(patient_id, created_at desc);
create index patient_reports_patient_release_idx
  on public.patient_reports(patient_id, released_at desc);
create index patient_observations_patient_time_idx
  on public.patient_observations(patient_id, observed_at desc);

create trigger appointment_requests_updated_at before update on public.appointment_requests
for each row execute function public.set_updated_at();

create function public.update_own_profile(p_changes jsonb)
returns public.profiles language plpgsql security definer set search_path = '' as $$
declare updated_profile public.profiles;
declare preferred text;
declare requested_birth_date date;
begin
  if p_changes is null or jsonb_typeof(p_changes) <> 'object'
     or (p_changes - array['preferred_name', 'birth_date', 'avatar_path', 'avatar_mime_type']) <> '{}'::jsonb then
    raise exception using errcode = '22023', message = 'Invalid profile fields';
  end if;
  if p_changes ? 'preferred_name' then
    preferred := trim(p_changes->>'preferred_name');
    if char_length(preferred) not between 1 and 80 then
      raise exception using errcode = '22023', message = 'Invalid preferred name';
    end if;
  end if;
  if p_changes ? 'birth_date' and p_changes->>'birth_date' is not null then
    requested_birth_date := (p_changes->>'birth_date')::date;
    if requested_birth_date not between date '1900-01-01' and current_date then
      raise exception using errcode = '22023', message = 'Invalid birth date';
    end if;
  end if;
  if p_changes ? 'avatar_path' and p_changes->>'avatar_path' is not null
     and p_changes->>'avatar_path' !~ ('^' || auth.uid()::text || '/avatar\.(png|jpg|webp)$') then
    raise exception using errcode = '22023', message = 'Invalid avatar path';
  end if;
  if p_changes ? 'avatar_mime_type' and p_changes->>'avatar_mime_type' is not null
     and p_changes->>'avatar_mime_type' not in ('image/png', 'image/jpeg', 'image/webp') then
    raise exception using errcode = '22023', message = 'Invalid avatar type';
  end if;

  update public.profiles set
    preferred_name = case when p_changes ? 'preferred_name' then preferred else preferred_name end,
    display_name = case when p_changes ? 'preferred_name' then preferred else display_name end,
    birth_date = case when p_changes ? 'birth_date' then requested_birth_date else birth_date end,
    avatar_path = case when p_changes ? 'avatar_path' then p_changes->>'avatar_path' else avatar_path end,
    avatar_mime_type = case when p_changes ? 'avatar_mime_type' then p_changes->>'avatar_mime_type' else avatar_mime_type end
  where id = auth.uid()
  returning * into updated_profile;
  if updated_profile.id is null then
    raise exception using errcode = 'P0002', message = 'Profile not found';
  end if;
  return updated_profile;
end;
$$;

create function public.mark_notification_read(p_notification_id uuid)
returns public.notification_outbox language plpgsql security definer set search_path = '' as $$
declare notification public.notification_outbox;
begin
  update public.notification_outbox
  set read_at = coalesce(read_at, now())
  where id = p_notification_id and recipient_id = auth.uid()
  returning * into notification;
  if notification.id is null then
    raise exception using errcode = 'P0002', message = 'Notification not found';
  end if;
  return notification;
end;
$$;

create function public.dismiss_own_notification(p_notification_id uuid)
returns public.notification_outbox language plpgsql security definer set search_path = '' as $$
declare notification public.notification_outbox;
begin
  update public.notification_outbox
  set status = 'dismissed', read_at = coalesce(read_at, now())
  where id = p_notification_id and recipient_id = auth.uid()
  returning * into notification;
  if notification.id is null then
    raise exception using errcode = 'P0002', message = 'Notification not found';
  end if;
  return notification;
end;
$$;

create function public.create_patient_portal_entry(
  p_kind text,
  p_content text,
  p_structured jsonb default '{}'::jsonb
)
returns public.entries language plpgsql security definer set search_path = '' as $$
declare target_patient public.patients;
declare target_note public.care_notes;
declare new_source public.source_records;
declare new_entry public.entries;
declare selected_source_type public.source_type;
begin
  if p_kind not in ('symptom_update', 'ai_question') or char_length(trim(p_content)) not between 1 and 2000 then
    raise exception using errcode = '22023', message = 'Invalid patient update';
  end if;
  if jsonb_typeof(coalesce(p_structured, '{}'::jsonb)) <> 'object'
     or octet_length(coalesce(p_structured, '{}'::jsonb)::text) > 4000 then
    raise exception using errcode = '22023', message = 'Invalid structured data';
  end if;
  select * into target_patient from public.patients
  where linked_profile_id = auth.uid() limit 1;
  if target_patient.id is null then
    raise exception using errcode = '42501', message = 'Patient portal unavailable';
  end if;
  select * into target_note from public.care_notes
  where patient_id = target_patient.id and clinic_id = target_patient.clinic_id;
  if target_note.id is null then
    raise exception using errcode = 'P0002', message = 'Care note not found';
  end if;
  selected_source_type := case when p_kind = 'ai_question'
    then 'ai_patient_session'::public.source_type else 'manual'::public.source_type end;
  insert into public.source_records (
    clinic_id, patient_id, source_type, external_reference, occurred_at, metadata, created_by
  ) values (
    target_patient.clinic_id, target_patient.id, selected_source_type,
    'portal:' || p_kind || ':' || extensions.gen_random_uuid()::text, now(),
    jsonb_build_object('synthetic', true, 'portal_kind', p_kind) || coalesce(p_structured, '{}'::jsonb),
    auth.uid()
  ) returning * into new_source;
  insert into public.entries (
    clinic_id, patient_id, care_note_id, author_id, author_role, entry_type,
    visibility, content, content_plaintext, source_record_id, occurred_at
  ) values (
    target_patient.clinic_id, target_patient.id, target_note.id, auth.uid(), 'patient',
    'patient_insight', 'internal', trim(p_content), trim(p_content), new_source.id, now()
  ) returning * into new_entry;
  insert into public.entry_versions (
    clinic_id, patient_id, entry_id, version_number, content_snapshot,
    changed_by, changed_by_role, change_reason
  ) values (
    new_entry.clinic_id, new_entry.patient_id, new_entry.id, 1, new_entry.content,
    auth.uid(), 'patient', 'Patient portal submission'
  );
  return new_entry;
end;
$$;

alter table public.appointment_requests enable row level security;
alter table public.patient_reports enable row level security;
alter table public.patient_observations enable row level security;

revoke all on public.appointment_requests, public.patient_reports, public.patient_observations
from anon, authenticated;
grant select, insert, update on public.appointment_requests to authenticated;
grant select on public.patient_reports, public.patient_observations to authenticated;

create policy appointment_requests_select_scoped on public.appointment_requests
for select to authenticated using (
  public.has_clinic_role(clinic_id, array['staff','clinician','admin']::public.clinic_role[])
  or (requested_by = auth.uid() and public.is_linked_patient(patient_id, clinic_id))
);
create policy appointment_requests_insert_patient on public.appointment_requests
for insert to authenticated with check (
  requested_by = auth.uid() and status = 'requested'
  and public.is_linked_patient(patient_id, clinic_id)
);
create policy appointment_requests_update_clinical on public.appointment_requests
for update to authenticated using (
  public.has_clinic_role(clinic_id, array['staff','clinician']::public.clinic_role[])
) with check (
  public.has_clinic_role(clinic_id, array['staff','clinician']::public.clinic_role[])
);
create policy patient_reports_select_scoped on public.patient_reports
for select to authenticated using (
  public.has_clinic_role(clinic_id, array['staff','clinician','admin']::public.clinic_role[])
  or (status = 'available' and released_at is not null and public.is_linked_patient(patient_id, clinic_id))
);
create policy patient_observations_select_scoped on public.patient_observations
for select to authenticated using (
  public.has_clinic_role(clinic_id, array['staff','clinician','admin']::public.clinic_role[])
  or public.is_linked_patient(patient_id, clinic_id)
);
create policy care_tasks_select_patient_visible on public.care_tasks
for select to authenticated using (
  patient_visible and public.is_linked_patient(patient_id, clinic_id)
);

revoke all on function public.update_own_profile(jsonb) from public;
grant execute on function public.update_own_profile(jsonb) to authenticated;
revoke all on function public.mark_notification_read(uuid) from public;
grant execute on function public.mark_notification_read(uuid) to authenticated;
revoke all on function public.dismiss_own_notification(uuid) from public;
grant execute on function public.dismiss_own_notification(uuid) to authenticated;
revoke all on function public.create_patient_portal_entry(text, text, jsonb) from public;
grant execute on function public.create_patient_portal_entry(text, text, jsonb) to authenticated;

-- Notification read state is changed only through the ownership-checking RPC.
-- Direct UPDATE would allow a caller to attempt changes to delivery metadata.
revoke update on public.notification_outbox from authenticated;
drop policy if exists optional_own_notification_update on public.notification_outbox;

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'profile-avatars', 'profile-avatars', false, 1048576,
  array['image/png', 'image/jpeg', 'image/webp']
)
on conflict (id) do update set
  public = false,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

create policy profile_avatar_select_own on storage.objects
for select to authenticated using (
  bucket_id = 'profile-avatars' and (storage.foldername(name))[1] = auth.uid()::text
);
create policy profile_avatar_insert_own on storage.objects
for insert to authenticated with check (
  bucket_id = 'profile-avatars' and (storage.foldername(name))[1] = auth.uid()::text
);
create policy profile_avatar_update_own on storage.objects
for update to authenticated using (
  bucket_id = 'profile-avatars' and (storage.foldername(name))[1] = auth.uid()::text
) with check (
  bucket_id = 'profile-avatars' and (storage.foldername(name))[1] = auth.uid()::text
);

commit;
