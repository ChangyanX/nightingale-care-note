begin;

create policy consult_recordings_select_clinical
on storage.objects
for select
to authenticated
using (
  bucket_id = 'consult-recordings'
  and exists (
    select 1
    from public.clinic_memberships membership
    where membership.profile_id = (select auth.uid())
      and membership.clinic_id::text = (storage.foldername(name))[1]
      and membership.role in ('staff', 'clinician', 'admin')
  )
);

create policy consult_recordings_insert_clinical
on storage.objects
for insert
to authenticated
with check (
  bucket_id = 'consult-recordings'
  and exists (
    select 1
    from public.clinic_memberships membership
    where membership.profile_id = (select auth.uid())
      and membership.clinic_id::text = (storage.foldername(name))[1]
      and membership.role in ('staff', 'clinician')
  )
);

commit;
