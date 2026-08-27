begin;

create type public.care_task_status as enum (
  'open',
  'in_progress',
  'completed',
  'cancelled'
);

create type public.care_task_priority as enum ('low', 'normal', 'high', 'urgent');

create table public.care_tasks (
  id uuid primary key default gen_random_uuid(),
  clinic_id uuid not null,
  patient_id uuid not null,
  source_entry_id uuid,
  title text not null check (char_length(title) between 1 and 240),
  assigned_to uuid references public.profiles(id) on delete set null,
  created_by uuid not null references public.profiles(id) on delete restrict,
  status public.care_task_status not null default 'open',
  priority public.care_task_priority not null default 'normal',
  due_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (id, clinic_id, patient_id),
  foreign key (patient_id, clinic_id)
    references public.patients(id, clinic_id) on delete cascade,
  foreign key (source_entry_id, clinic_id, patient_id)
    references public.entries(id, clinic_id, patient_id) on delete restrict,
  check (
    (status = 'completed' and completed_at is not null)
    or (status <> 'completed' and completed_at is null)
  )
);

create index care_tasks_patient_status_idx
on public.care_tasks(patient_id, status, priority, due_at);

create index care_tasks_assignee_status_idx
on public.care_tasks(assigned_to, status)
where assigned_to is not null;

create trigger care_tasks_updated_at before update on public.care_tasks
for each row execute function public.set_updated_at();

create function public.is_profile_in_clinic(target_profile_id uuid, target_clinic_id uuid)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from public.clinic_memberships membership
    where membership.profile_id = target_profile_id
      and membership.clinic_id = target_clinic_id
  );
$$;

revoke all on function public.is_profile_in_clinic(uuid, uuid) from public;
grant execute on function public.is_profile_in_clinic(uuid, uuid) to authenticated;

alter table public.care_tasks enable row level security;

revoke all on public.care_tasks from anon, authenticated;
grant select, insert, update on public.care_tasks to authenticated;

create policy care_tasks_select_clinical
on public.care_tasks
for select
to authenticated
using (
  public.has_clinic_role(
    clinic_id,
    array['staff', 'clinician', 'admin']::public.clinic_role[]
  )
);

create policy care_tasks_insert_clinical
on public.care_tasks
for insert
to authenticated
with check (
  created_by = (select auth.uid())
  and public.has_clinic_role(
    clinic_id,
    array['staff', 'clinician']::public.clinic_role[]
  )
  and (
    assigned_to is null
    or public.is_profile_in_clinic(assigned_to, clinic_id)
  )
);

create policy care_tasks_update_clinical
on public.care_tasks
for update
to authenticated
using (
  public.has_clinic_role(
    clinic_id,
    array['staff', 'clinician']::public.clinic_role[]
  )
)
with check (
  public.has_clinic_role(
    clinic_id,
    array['staff', 'clinician']::public.clinic_role[]
  )
  and (
    assigned_to is null
    or public.is_profile_in_clinic(assigned_to, clinic_id)
  )
);

create function public.protect_care_task_identity()
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
    new.created_by,
    new.created_at
  ) is distinct from row(
    old.id,
    old.clinic_id,
    old.patient_id,
    old.source_entry_id,
    old.created_by,
    old.created_at
  ) then
    raise exception using
      errcode = '42501',
      message = 'Care-task ownership and source are immutable';
  end if;
  return new;
end;
$$;

create trigger protect_care_task_identity_before_update
before update on public.care_tasks
for each row execute function public.protect_care_task_identity();

alter table public.entries replica identity full;
alter table public.care_tasks replica identity full;

do $$
begin
  if exists (
    select 1 from pg_publication where pubname = 'supabase_realtime'
  ) then
    if not exists (
      select 1
      from pg_publication_tables
      where pubname = 'supabase_realtime'
        and schemaname = 'public'
        and tablename = 'entries'
    ) then
      execute 'alter publication supabase_realtime add table public.entries';
    end if;

    if not exists (
      select 1
      from pg_publication_tables
      where pubname = 'supabase_realtime'
        and schemaname = 'public'
        and tablename = 'care_tasks'
    ) then
      execute 'alter publication supabase_realtime add table public.care_tasks';
    end if;
  end if;
end;
$$;

commit;
