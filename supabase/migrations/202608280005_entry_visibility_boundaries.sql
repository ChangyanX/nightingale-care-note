begin;

drop policy entries_insert_clinician on public.entries;
create policy entries_insert_clinician on public.entries for insert to authenticated
with check (
  author_id = auth.uid()
  and author_role = 'clinician'
  and (
    (entry_type = 'clinician_note' and visibility = 'internal')
    or (
      entry_type in ('patient_summary', 'patient_instruction')
      and visibility = 'patient_facing'
    )
  )
  and public.has_clinic_role(clinic_id, array['clinician']::public.clinic_role[])
);

drop policy entries_update_clinician on public.entries;
create policy entries_update_clinician on public.entries for update to authenticated
using (
  author_id = auth.uid()
  and author_role = 'clinician'
  and public.has_clinic_role(clinic_id, array['clinician']::public.clinic_role[])
)
with check (
  author_id = auth.uid()
  and author_role = 'clinician'
  and (
    (entry_type = 'clinician_note' and visibility = 'internal')
    or (
      entry_type in ('patient_summary', 'patient_instruction')
      and visibility = 'patient_facing'
    )
  )
  and public.has_clinic_role(clinic_id, array['clinician']::public.clinic_role[])
);

commit;
