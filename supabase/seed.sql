-- Local development only. All people and clinical events below are fictional.
-- Demo password for local Supabase Auth users: NightingaleDemo2026!

insert into auth.users (
  instance_id,
  id,
  aud,
  role,
  email,
  encrypted_password,
  email_confirmed_at,
  raw_app_meta_data,
  raw_user_meta_data,
  created_at,
  updated_at,
  confirmation_token,
  email_change,
  email_change_token_new,
  recovery_token
)
values
  ('00000000-0000-0000-0000-000000000000', '20000000-0000-0000-0000-000000000001', 'authenticated', 'authenticated', 'admin.a@nightingale.local', extensions.crypt('NightingaleDemo2026!', extensions.gen_salt('bf')), now(), '{"provider":"email","providers":["email"]}', '{"display_name":"Avery Admin"}', now(), now(), '', '', '', ''),
  ('00000000-0000-0000-0000-000000000000', '20000000-0000-0000-0000-000000000002', 'authenticated', 'authenticated', 'staff.a@nightingale.local', extensions.crypt('NightingaleDemo2026!', extensions.gen_salt('bf')), now(), '{"provider":"email","providers":["email"]}', '{"display_name":"Sam Staff"}', now(), now(), '', '', '', ''),
  ('00000000-0000-0000-0000-000000000000', '20000000-0000-0000-0000-000000000003', 'authenticated', 'authenticated', 'clinician.a@nightingale.local', extensions.crypt('NightingaleDemo2026!', extensions.gen_salt('bf')), now(), '{"provider":"email","providers":["email"]}', '{"display_name":"Dr. Casey Clinician"}', now(), now(), '', '', '', ''),
  ('00000000-0000-0000-0000-000000000000', '20000000-0000-0000-0000-000000000004', 'authenticated', 'authenticated', 'patient.a@nightingale.local', extensions.crypt('NightingaleDemo2026!', extensions.gen_salt('bf')), now(), '{"provider":"email","providers":["email"]}', '{"display_name":"Parker Patient"}', now(), now(), '', '', '', ''),
  ('00000000-0000-0000-0000-000000000000', '20000000-0000-0000-0000-000000000005', 'authenticated', 'authenticated', 'staff.b@nightingale.local', extensions.crypt('NightingaleDemo2026!', extensions.gen_salt('bf')), now(), '{"provider":"email","providers":["email"]}', '{"display_name":"Taylor Staff"}', now(), now(), '', '', '', ''),
  ('00000000-0000-0000-0000-000000000000', '20000000-0000-0000-0000-000000000006', 'authenticated', 'authenticated', 'clinician.b@nightingale.local', extensions.crypt('NightingaleDemo2026!', extensions.gen_salt('bf')), now(), '{"provider":"email","providers":["email"]}', '{"display_name":"Dr. Jordan Clinician"}', now(), now(), '', '', '', ''),
  ('00000000-0000-0000-0000-000000000000', '20000000-0000-0000-0000-000000000007', 'authenticated', 'authenticated', 'patient.a2@nightingale.local', extensions.crypt('NightingaleDemo2026!', extensions.gen_salt('bf')), now(), '{"provider":"email","providers":["email"]}', '{"display_name":"Morgan Example (Synthetic)"}', now(), now(), '', '', '', ''),
  ('00000000-0000-0000-0000-000000000000', '20000000-0000-0000-0000-000000000008', 'authenticated', 'authenticated', 'patient.b@nightingale.local', extensions.crypt('NightingaleDemo2026!', extensions.gen_salt('bf')), now(), '{"provider":"email","providers":["email"]}', '{"display_name":"Riley Example (Synthetic)"}', now(), now(), '', '', '', ''),
  ('00000000-0000-0000-0000-000000000000', '20000000-0000-0000-0000-000000000009', 'authenticated', 'authenticated', 'patient.a3@nightingale.local', extensions.crypt('NightingaleDemo2026!', extensions.gen_salt('bf')), now(), '{"provider":"email","providers":["email"]}', '{"display_name":"Jamie Sample (Synthetic)"}', now(), now(), '', '', '', ''),
  ('00000000-0000-0000-0000-000000000000', '20000000-0000-0000-0000-000000000010', 'authenticated', 'authenticated', 'patient.b2@nightingale.local', extensions.crypt('NightingaleDemo2026!', extensions.gen_salt('bf')), now(), '{"provider":"email","providers":["email"]}', '{"display_name":"Quinn Sample (Synthetic)"}', now(), now(), '', '', '', '')
on conflict (id) do nothing;

insert into auth.identities (
  id,
  provider_id,
  user_id,
  identity_data,
  provider,
  last_sign_in_at,
  created_at,
  updated_at
)
values
  ('30000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001', '{"sub":"20000000-0000-0000-0000-000000000001","email":"admin.a@nightingale.local"}', 'email', now(), now(), now()),
  ('30000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000002', '{"sub":"20000000-0000-0000-0000-000000000002","email":"staff.a@nightingale.local"}', 'email', now(), now(), now()),
  ('30000000-0000-0000-0000-000000000003', '20000000-0000-0000-0000-000000000003', '20000000-0000-0000-0000-000000000003', '{"sub":"20000000-0000-0000-0000-000000000003","email":"clinician.a@nightingale.local"}', 'email', now(), now(), now()),
  ('30000000-0000-0000-0000-000000000004', '20000000-0000-0000-0000-000000000004', '20000000-0000-0000-0000-000000000004', '{"sub":"20000000-0000-0000-0000-000000000004","email":"patient.a@nightingale.local"}', 'email', now(), now(), now()),
  ('30000000-0000-0000-0000-000000000005', '20000000-0000-0000-0000-000000000005', '20000000-0000-0000-0000-000000000005', '{"sub":"20000000-0000-0000-0000-000000000005","email":"staff.b@nightingale.local"}', 'email', now(), now(), now()),
  ('30000000-0000-0000-0000-000000000006', '20000000-0000-0000-0000-000000000006', '20000000-0000-0000-0000-000000000006', '{"sub":"20000000-0000-0000-0000-000000000006","email":"clinician.b@nightingale.local"}', 'email', now(), now(), now()),
  ('30000000-0000-0000-0000-000000000007', '20000000-0000-0000-0000-000000000007', '20000000-0000-0000-0000-000000000007', '{"sub":"20000000-0000-0000-0000-000000000007","email":"patient.a2@nightingale.local"}', 'email', now(), now(), now()),
  ('30000000-0000-0000-0000-000000000008', '20000000-0000-0000-0000-000000000008', '20000000-0000-0000-0000-000000000008', '{"sub":"20000000-0000-0000-0000-000000000008","email":"patient.b@nightingale.local"}', 'email', now(), now(), now()),
  ('30000000-0000-0000-0000-000000000009', '20000000-0000-0000-0000-000000000009', '20000000-0000-0000-0000-000000000009', '{"sub":"20000000-0000-0000-0000-000000000009","email":"patient.a3@nightingale.local"}', 'email', now(), now(), now()),
  ('30000000-0000-0000-0000-000000000010', '20000000-0000-0000-0000-000000000010', '20000000-0000-0000-0000-000000000010', '{"sub":"20000000-0000-0000-0000-000000000010","email":"patient.b2@nightingale.local"}', 'email', now(), now(), now())
on conflict (id) do nothing;

insert into public.clinics (id, name)
values
  ('10000000-0000-0000-0000-000000000001', 'Harbour Family Clinic'),
  ('10000000-0000-0000-0000-000000000002', 'Orchard Community Clinic')
on conflict (id) do nothing;

insert into public.profiles (id, display_name)
values
  ('20000000-0000-0000-0000-000000000001', 'Avery Admin'),
  ('20000000-0000-0000-0000-000000000002', 'Sam Staff'),
  ('20000000-0000-0000-0000-000000000003', 'Dr. Casey Clinician'),
  ('20000000-0000-0000-0000-000000000004', 'Parker Patient'),
  ('20000000-0000-0000-0000-000000000005', 'Taylor Staff'),
  ('20000000-0000-0000-0000-000000000006', 'Dr. Jordan Clinician'),
  ('20000000-0000-0000-0000-000000000007', 'Morgan Example (Synthetic)'),
  ('20000000-0000-0000-0000-000000000008', 'Riley Example (Synthetic)'),
  ('20000000-0000-0000-0000-000000000009', 'Jamie Sample (Synthetic)'),
  ('20000000-0000-0000-0000-000000000010', 'Quinn Sample (Synthetic)')
on conflict (id) do update set display_name = excluded.display_name;

insert into public.clinic_memberships (clinic_id, profile_id, role)
values
  ('10000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001', 'admin'),
  ('10000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000002', 'staff'),
  ('10000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000003', 'clinician'),
  ('10000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000005', 'staff'),
  ('10000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000006', 'clinician')
on conflict do nothing;

insert into public.patients (id, clinic_id, linked_profile_id, synthetic_identifier, display_name)
values
  ('40000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000004', 'SYN-A-001', 'Parker Patient'),
  ('40000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000007', 'SYN-A-002', 'Morgan Example (Synthetic)'),
  ('40000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000008', 'SYN-B-001', 'Riley Example (Synthetic)'),
  ('40000000-0000-0000-0000-000000000004', '10000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000009', 'SYN-A-003', 'Jamie Sample (Synthetic)'),
  ('40000000-0000-0000-0000-000000000005', '10000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000010', 'SYN-B-002', 'Quinn Sample (Synthetic)')
on conflict (id) do update set
  linked_profile_id = excluded.linked_profile_id,
  display_name = excluded.display_name;

insert into public.care_notes (id, clinic_id, patient_id)
values
  ('50000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001'),
  ('50000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000002'),
  ('50000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000002', '40000000-0000-0000-0000-000000000003'),
  ('50000000-0000-0000-0000-000000000004', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000004'),
  ('50000000-0000-0000-0000-000000000005', '10000000-0000-0000-0000-000000000002', '40000000-0000-0000-0000-000000000005')
on conflict (id) do nothing;

insert into public.source_records (id, clinic_id, patient_id, source_type, external_reference, occurred_at, created_by, metadata)
values
  ('60000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', 'manual', 'staff-note-001', '2026-08-24T09:00:00+08:00', '20000000-0000-0000-0000-000000000002', '{"synthetic":true}'),
  ('60000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', 'manual', 'clinician-note-001', '2026-08-24T09:30:00+08:00', '20000000-0000-0000-0000-000000000003', '{"synthetic":true}'),
  ('60000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', 'doctor_consult', 'doctor-consult-001', '2026-08-24T09:30:00+08:00', null, '{"synthetic":true,"session_id":"doctor-consult-001"}'),
  ('60000000-0000-0000-0000-000000000004', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', 'nurse_consult', 'nurse-consult-001', '2026-08-25T10:00:00+08:00', null, '{"synthetic":true,"session_id":"nurse-consult-001"}'),
  ('60000000-0000-0000-0000-000000000005', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', 'ai_patient_session', 'ai-session-001', '2026-08-26T08:00:00+08:00', null, '{"synthetic":true,"session_id":"ai-session-001"}'),
  ('60000000-0000-0000-0000-000000000006', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', 'manual', 'patient-instruction-001', '2026-08-24T09:40:00+08:00', '20000000-0000-0000-0000-000000000003', '{"synthetic":true}'),
  ('60000000-0000-0000-0000-000000000007', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', 'manual', 'patient-insight-001', '2026-08-26T07:50:00+08:00', '20000000-0000-0000-0000-000000000004', '{"synthetic":true}'),
  ('60000000-0000-0000-0000-000000000008', '10000000-0000-0000-0000-000000000002', '40000000-0000-0000-0000-000000000003', 'manual', 'clinic-b-note-001', '2026-08-25T11:00:00+08:00', '20000000-0000-0000-0000-000000000005', '{"synthetic":true}'),
  ('60000000-0000-0000-0000-000000000009', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', 'manual', 'staff-note-002', '2026-08-25T16:00:00+08:00', '20000000-0000-0000-0000-000000000002', '{"synthetic":true,"concern_rank":2}')
on conflict (id) do nothing;

insert into public.entries (
  id, clinic_id, patient_id, care_note_id, author_id, author_role, entry_type,
  visibility, content, content_plaintext, source_record_id, occurred_at
)
values
  ('70000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000002', 'staff', 'staff_note', 'internal', 'Patient called to report that the cough is more frequent at night.', 'Patient called to report that the cough is more frequent at night.', '60000000-0000-0000-0000-000000000001', '2026-08-24T09:00:00+08:00'),
  ('70000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000003', 'clinician', 'clinician_note', 'internal', 'Assessment: persistent nocturnal cough; review inhaler technique and follow up after peak-flow diary.', 'Assessment: persistent nocturnal cough; review inhaler technique and follow up after peak-flow diary.', '60000000-0000-0000-0000-000000000002', '2026-08-24T09:30:00+08:00'),
  ('70000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000001', null, 'system', 'ai_doctor_consult_summary', 'internal', 'Doctor consult summary: nocturnal cough persists; inhaler technique review and a seven-day peak-flow diary were agreed.', 'Doctor consult summary: nocturnal cough persists; inhaler technique review and a seven-day peak-flow diary were agreed.', '60000000-0000-0000-0000-000000000003', '2026-08-24T09:30:00+08:00'),
  ('70000000-0000-0000-0000-000000000004', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000001', null, 'system', 'ai_nurse_consult_summary', 'internal', 'Nurse consult summary: technique coaching completed; patient demonstrated correct inhaler use.', 'Nurse consult summary: technique coaching completed; patient demonstrated correct inhaler use.', '60000000-0000-0000-0000-000000000004', '2026-08-25T10:00:00+08:00'),
  ('70000000-0000-0000-0000-000000000005', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000001', null, 'system', 'ai_patient_session_summary', 'internal', 'AI-patient session: patient asks whether the new nighttime symptoms require an earlier review.', 'AI-patient session: patient asks whether the new nighttime symptoms require an earlier review.', '60000000-0000-0000-0000-000000000005', '2026-08-26T08:00:00+08:00'),
  ('70000000-0000-0000-0000-000000000006', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000003', 'clinician', 'patient_instruction', 'patient_facing', 'Record peak-flow readings each morning and evening for seven days. Contact the clinic sooner if breathing worsens.', 'Record peak-flow readings each morning and evening for seven days. Contact the clinic sooner if breathing worsens.', '60000000-0000-0000-0000-000000000006', '2026-08-24T09:40:00+08:00'),
  ('70000000-0000-0000-0000-000000000007', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000004', 'patient', 'patient_insight', 'internal', 'The cough woke me twice last night and seems worse when the room is cold.', 'The cough woke me twice last night and seems worse when the room is cold.', '60000000-0000-0000-0000-000000000007', '2026-08-26T07:50:00+08:00'),
  ('70000000-0000-0000-0000-000000000008', '10000000-0000-0000-0000-000000000002', '40000000-0000-0000-0000-000000000003', '50000000-0000-0000-0000-000000000003', '20000000-0000-0000-0000-000000000005', 'staff', 'staff_note', 'internal', 'Synthetic Clinic B note used to prove tenant isolation.', 'Synthetic Clinic B note used to prove tenant isolation.', '60000000-0000-0000-0000-000000000008', '2026-08-25T11:00:00+08:00'),
  ('70000000-0000-0000-0000-000000000009', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000002', 'staff', 'staff_note', 'internal', 'Secondary concern: sleep disruption is affecting daytime concentration, but there are no synthetic red-flag symptoms.', 'Secondary concern: sleep disruption is affecting daytime concentration, but there are no synthetic red-flag symptoms.', '60000000-0000-0000-0000-000000000009', '2026-08-25T16:00:00+08:00')
on conflict (id) do nothing;

insert into public.entry_versions (
  id, clinic_id, patient_id, entry_id, version_number, content_snapshot,
  changed_by, changed_by_role, change_reason
)
select
  ('c' || substring(id::text from 2))::uuid,
  clinic_id,
  patient_id,
  id,
  1,
  content,
  author_id,
  author_role,
  'Initial synthetic version'
from public.entries
on conflict (entry_id, version_number) do nothing;

insert into public.note_sections (
  id, clinic_id, patient_id, care_note_id, section_type, owner_role, created_by, visibility, content
)
values
  ('80000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000001', 'staff_note', 'staff', '20000000-0000-0000-0000-000000000002', 'internal', 'Awaiting confirmation that the peak-flow diary has started.'),
  ('80000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000001', 'assessment', 'clinician', '20000000-0000-0000-0000-000000000003', 'internal', 'Persistent nocturnal cough; no synthetic emergency features documented.'),
  ('80000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000001', 'plan', 'clinician', '20000000-0000-0000-0000-000000000003', 'internal', 'Review diary in seven days and reassess symptom pattern.'),
  ('80000000-0000-0000-0000-000000000004', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000001', 'patient_instruction', 'clinician', '20000000-0000-0000-0000-000000000003', 'patient_facing', 'Record morning and evening peak flow for seven days.')
on conflict (id) do nothing;

insert into public.section_versions (
  clinic_id, patient_id, section_id, version_number, content_snapshot, changed_by, changed_by_role, change_reason
)
select
  clinic_id,
  patient_id,
  id,
  1,
  content,
  created_by,
  owner_role,
  'Initial synthetic version'
from public.note_sections
on conflict (section_id, version_number) do nothing;

insert into public.comments (
  id, clinic_id, patient_id, entry_id, parent_comment_id, author_id, body,
  status, assigned_to, resolved_at
)
values
  (
    '90000000-0000-0000-0000-000000000001',
    '10000000-0000-0000-0000-000000000001',
    '40000000-0000-0000-0000-000000000001',
    '70000000-0000-0000-0000-000000000003',
    null,
    '20000000-0000-0000-0000-000000000002',
    'Internal synthetic comment: please confirm the follow-up interval.',
    'open',
    '20000000-0000-0000-0000-000000000003',
    null
  ),
  (
    '90000000-0000-0000-0000-000000000002',
    '10000000-0000-0000-0000-000000000001',
    '40000000-0000-0000-0000-000000000001',
    '70000000-0000-0000-0000-000000000003',
    '90000000-0000-0000-0000-000000000001',
    '20000000-0000-0000-0000-000000000003',
    'Synthetic reply: review after the seven-day diary unless symptoms worsen.',
    'open',
    null,
    null
  ),
  (
    '90000000-0000-0000-0000-000000000003',
    '10000000-0000-0000-0000-000000000001',
    '40000000-0000-0000-0000-000000000001',
    '70000000-0000-0000-0000-000000000004',
    null,
    '20000000-0000-0000-0000-000000000002',
    'Synthetic resolved comment: inhaler-technique coaching confirmed.',
    'resolved',
    null,
    '2026-08-25T10:20:00+08:00'
  )
on conflict (id) do update set
  body = excluded.body,
  status = excluded.status,
  assigned_to = excluded.assigned_to,
  resolved_at = excluded.resolved_at;

insert into public.mentions (
  id, clinic_id, patient_id, comment_id, mentioned_profile_id, created_by
)
values (
  '91000000-0000-0000-0000-000000000001',
  '10000000-0000-0000-0000-000000000001',
  '40000000-0000-0000-0000-000000000001',
  '90000000-0000-0000-0000-000000000001',
  '20000000-0000-0000-0000-000000000003',
  '20000000-0000-0000-0000-000000000002'
)
on conflict (comment_id, mentioned_profile_id) do nothing;

with highlight_fixtures (
  id, entry_id, quoted_text, normalized_claim, risk_level, risk_reason,
  score, status, generated_by
) as (
  values
    (
      'd0000000-0000-0000-0000-000000000001'::uuid,
      '70000000-0000-0000-0000-000000000003'::uuid,
      'nocturnal cough persists',
      'Persistent nocturnal cough requires planned follow-up',
      'attention'::public.highlight_risk_level,
      'Persistent night symptoms and an unresolved monitoring plan',
      82.000,
      'accepted'::public.highlight_status,
      'ai'::public.highlight_generator
    ),
    (
      'd0000000-0000-0000-0000-000000000002'::uuid,
      '70000000-0000-0000-0000-000000000007'::uuid,
      'worse when the room is cold',
      'Cold-room association may be relevant',
      'information'::public.highlight_risk_level,
      'Patient-reported context with limited independent clinical significance',
      42.000,
      'rejected'::public.highlight_status,
      'rule'::public.highlight_generator
    )
)
insert into public.highlights (
  id, clinic_id, patient_id, source_entry_id, source_version_id,
  source_start_offset, source_end_offset, quoted_text, normalized_claim,
  risk_level, risk_reason, score, status, generated_by, reviewed_by, reviewed_at
)
select
  fixture.id,
  version.clinic_id,
  version.patient_id,
  version.entry_id,
  version.id,
  strpos(version.content_snapshot, fixture.quoted_text) - 1,
  strpos(version.content_snapshot, fixture.quoted_text) - 1 + char_length(fixture.quoted_text),
  fixture.quoted_text,
  fixture.normalized_claim,
  fixture.risk_level,
  fixture.risk_reason,
  fixture.score,
  fixture.status,
  fixture.generated_by,
  '20000000-0000-0000-0000-000000000003',
  '2026-08-26T09:00:00+08:00'
from highlight_fixtures fixture
join public.entry_versions version
  on version.entry_id = fixture.entry_id
 and version.version_number = 1
where strpos(version.content_snapshot, fixture.quoted_text) > 0
on conflict (id) do nothing;

insert into public.audit_events (
  id, clinic_id, patient_id, actor_id, actor_role, action, resource_type, resource_id, metadata
)
values
  ('a0000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000002', 'staff', 'created', 'entry', '70000000-0000-0000-0000-000000000001', '{"version":1,"synthetic":true}'),
  ('a0000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000003', 'clinician', 'created', 'entry', '70000000-0000-0000-0000-000000000002', '{"version":1,"synthetic":true}')
on conflict (id) do nothing;

insert into public.care_tasks (
  id, clinic_id, patient_id, source_entry_id, title, assigned_to, created_by,
  status, priority, category, patient_visible, due_at, completed_at
)
values
  (
    'b0000000-0000-0000-0000-000000000001',
    '10000000-0000-0000-0000-000000000001',
    '40000000-0000-0000-0000-000000000001',
    '70000000-0000-0000-0000-000000000002',
    'Review seven-day peak-flow diary and reassess nocturnal cough',
    '20000000-0000-0000-0000-000000000003',
    '20000000-0000-0000-0000-000000000002',
    'open',
    'high',
    'monitoring',
    true,
    '2026-08-31T17:00:00+08:00',
    null
  ),
  (
    'b0000000-0000-0000-0000-000000000002',
    '10000000-0000-0000-0000-000000000001',
    '40000000-0000-0000-0000-000000000001',
    '70000000-0000-0000-0000-000000000004',
    'Confirm inhaler-technique coaching was completed',
    '20000000-0000-0000-0000-000000000002',
    '20000000-0000-0000-0000-000000000003',
    'completed',
    'normal',
    'clinical_review',
    false,
    '2026-08-25T17:00:00+08:00',
    '2026-08-25T10:15:00+08:00'
  )
on conflict (id) do update set
  title = excluded.title,
  assigned_to = excluded.assigned_to,
  status = excluded.status,
  priority = excluded.priority,
  category = excluded.category,
  patient_visible = excluded.patient_visible,
  due_at = excluded.due_at,
  completed_at = excluded.completed_at;

-- Rich, coherent synthetic longitudinal stories for every secondary demo patient.
-- These fixtures deliberately include restricted internal material and separate
-- patient-facing artifacts so patient-boundary tests have meaningful data.
update public.entries
set
  content = 'Assessment: persistent nocturnal cough; review inhaler technique, complete the peak-flow diary, and follow up in seven days.',
  content_plaintext = 'Assessment: persistent nocturnal cough; review inhaler technique, complete the peak-flow diary, and follow up in seven days.',
  current_version = 2
where id = '70000000-0000-0000-0000-000000000002';

insert into public.entry_versions (
  id, clinic_id, patient_id, entry_id, version_number, content_snapshot,
  changed_by, changed_by_role, change_reason, created_at
)
values (
  'c2000000-0000-0000-0000-000000000002',
  '10000000-0000-0000-0000-000000000001',
  '40000000-0000-0000-0000-000000000001',
  '70000000-0000-0000-0000-000000000002',
  2,
  'Assessment: persistent nocturnal cough; review inhaler technique, complete the peak-flow diary, and follow up in seven days.',
  '20000000-0000-0000-0000-000000000003',
  'clinician',
  'Synthetic revision: clarified monitoring interval',
  '2026-08-24T09:35:00+08:00'
)
on conflict (entry_id, version_number) do nothing;

create temporary table rich_demo_patients (
  patient_id uuid primary key,
  clinic_id uuid not null,
  care_note_id uuid not null,
  patient_profile_id uuid not null,
  staff_id uuid not null,
  clinician_id uuid not null,
  story_key text not null,
  patient_update text not null,
  staff_note text not null,
  clinician_note_v1 text not null,
  clinician_note_v2 text not null,
  doctor_summary text not null,
  nurse_summary text not null,
  ai_patient_summary text not null,
  patient_instruction text not null,
  patient_summary text not null,
  risk_quote text not null,
  risk_reason text not null,
  task_title text not null
) on commit drop;

insert into rich_demo_patients values
  (
    '40000000-0000-0000-0000-000000000002',
    '10000000-0000-0000-0000-000000000001',
    '50000000-0000-0000-0000-000000000002',
    '20000000-0000-0000-0000-000000000007',
    '20000000-0000-0000-0000-000000000002',
    '20000000-0000-0000-0000-000000000003',
    'morgan',
    'Synthetic patient update: morning headaches have occurred on three days this week and improve after breakfast.',
    'Synthetic staff note: home blood-pressure diary was received and the follow-up request remains open.',
    'Synthetic clinician draft: review variable morning readings and hydration pattern.',
    'Synthetic clinician note: review variable morning readings, hydration pattern, and repeat the diary with the validated cuff.',
    'Doctor consult summary: several elevated morning readings require timely review; no synthetic emergency symptoms were reported.',
    'Nurse consult summary: cuff positioning was corrected and a repeat seven-day diary was demonstrated.',
    'AI-patient session summary: patient asked how to record readings consistently before the follow-up.',
    'Use the validated cuff after five minutes seated rest and record morning readings for seven days.',
    'Your care team is reviewing your home readings. Continue the agreed diary and follow the released instructions.',
    'elevated morning readings require timely review',
    'Repeated elevated synthetic readings are unresolved and need clinician confirmation.',
    'Review repeat home blood-pressure diary'
  ),
  (
    '40000000-0000-0000-0000-000000000003',
    '10000000-0000-0000-0000-000000000002',
    '50000000-0000-0000-0000-000000000003',
    '20000000-0000-0000-0000-000000000008',
    '20000000-0000-0000-0000-000000000005',
    '20000000-0000-0000-0000-000000000006',
    'riley',
    'Synthetic patient update: knee stiffness is most noticeable after sitting and settles after gentle movement.',
    'Synthetic staff note: physiotherapy availability was checked and the patient requested an afternoon appointment.',
    'Synthetic clinician draft: mechanical knee symptoms without reported acute injury.',
    'Synthetic clinician note: mechanical knee symptoms without reported acute injury; assess function after the activity trial.',
    'Doctor consult summary: increasing difficulty on stairs needs planned functional review; no synthetic acute swelling was reported.',
    'Nurse consult summary: safe pacing and the agreed symptom-score diary were reviewed.',
    'AI-patient session summary: patient asked which daily activities should be included in the symptom diary.',
    'Use gentle movement within comfort and record a daily symptom score; contact the clinic if symptoms suddenly worsen.',
    'Your care team has recommended a short activity and symptom diary before the next review.',
    'increasing difficulty on stairs needs planned functional review',
    'Functional change is unresolved and is relevant to the upcoming review.',
    'Review knee symptom and activity diary'
  ),
  (
    '40000000-0000-0000-0000-000000000004',
    '10000000-0000-0000-0000-000000000001',
    '50000000-0000-0000-0000-000000000004',
    '20000000-0000-0000-0000-000000000009',
    '20000000-0000-0000-0000-000000000002',
    '20000000-0000-0000-0000-000000000003',
    'jamie',
    'Synthetic patient update: sleep has averaged about five hours during a busy study week.',
    'Synthetic staff note: a non-urgent wellbeing check was requested and preferred contact times were confirmed.',
    'Synthetic clinician draft: short sleep duration associated with temporary schedule disruption.',
    'Synthetic clinician note: short sleep duration associated with temporary schedule disruption; review trend and daytime impact.',
    'Doctor consult summary: persistent five-hour sleep pattern with daytime fatigue should be reassessed after the sleep log.',
    'Nurse consult summary: sleep-log instructions and routine sleep-hygiene measures were discussed.',
    'AI-patient session summary: patient asked for a simple way to track sleep and daytime energy.',
    'Keep a seven-night sleep and daytime-energy log and follow the released routine guidance.',
    'Your care team is reviewing a temporary change in sleep. Complete the short log before follow-up.',
    'daytime fatigue should be reassessed',
    'The synthetic fatigue trend remains unconfirmed until the follow-up log is reviewed.',
    'Review seven-night sleep and energy log'
  ),
  (
    '40000000-0000-0000-0000-000000000005',
    '10000000-0000-0000-0000-000000000002',
    '50000000-0000-0000-0000-000000000005',
    '20000000-0000-0000-0000-000000000010',
    '20000000-0000-0000-0000-000000000005',
    '20000000-0000-0000-0000-000000000006',
    'quinn',
    'Synthetic patient update: seasonal nasal symptoms are worse outdoors in the early morning.',
    'Synthetic staff note: the current over-the-counter product list was collected for clinician review.',
    'Synthetic clinician draft: seasonal pattern reported without synthetic breathing difficulty.',
    'Synthetic clinician note: seasonal pattern reported without synthetic breathing difficulty; review response to the agreed measures.',
    'Doctor consult summary: symptoms are disrupting sleep twice weekly and response to the plan needs follow-up.',
    'Nurse consult summary: trigger diary and the released self-care instructions were reviewed.',
    'AI-patient session summary: patient asked how to distinguish routine symptoms from reasons to contact the clinic.',
    'Follow the released seasonal-symptom plan and record triggers; contact the clinic if breathing symptoms occur.',
    'Your care team has released a seasonal-symptom plan and will review your trigger diary.',
    'symptoms are disrupting sleep twice weekly',
    'Sleep disruption is unresolved and should be checked at follow-up.',
    'Review seasonal symptom and trigger diary'
  );

update public.profiles
set birth_date = case id
  when '20000000-0000-0000-0000-000000000004'::uuid then date '1991-04-12'
  when '20000000-0000-0000-0000-000000000007'::uuid then date '1986-09-03'
  when '20000000-0000-0000-0000-000000000008'::uuid then date '1978-01-21'
  when '20000000-0000-0000-0000-000000000009'::uuid then date '2001-06-17'
  when '20000000-0000-0000-0000-000000000010'::uuid then date '1994-11-28'
end
where id in (
  '20000000-0000-0000-0000-000000000004',
  '20000000-0000-0000-0000-000000000007',
  '20000000-0000-0000-0000-000000000008',
  '20000000-0000-0000-0000-000000000009',
  '20000000-0000-0000-0000-000000000010'
);

insert into public.source_records (
  id, clinic_id, patient_id, source_type, external_reference, occurred_at, created_by, metadata
)
select
  md5(f.patient_id::text || ':source:' || k.kind)::uuid,
  f.clinic_id,
  f.patient_id,
  k.source_type,
  'synthetic-' || f.story_key || '-' || k.kind,
  k.occurred_at,
  case k.author_kind
    when 'patient' then f.patient_profile_id
    when 'staff' then f.staff_id
    when 'clinician' then f.clinician_id
    else null
  end,
  jsonb_build_object('synthetic', true, 'demo_story', f.story_key, 'session_kind', k.kind)
from rich_demo_patients f
cross join (values
  ('patient_update', 'manual'::public.source_type, 'patient', '2026-08-18T08:10:00+08:00'::timestamptz),
  ('staff_note', 'manual'::public.source_type, 'staff', '2026-08-19T10:20:00+08:00'::timestamptz),
  ('clinician_note', 'manual'::public.source_type, 'clinician', '2026-08-20T14:00:00+08:00'::timestamptz),
  ('doctor_session', 'doctor_consult'::public.source_type, 'system', '2026-08-20T14:05:00+08:00'::timestamptz),
  ('nurse_session', 'nurse_consult'::public.source_type, 'system', '2026-08-21T11:15:00+08:00'::timestamptz),
  ('ai_patient_session', 'ai_patient_session'::public.source_type, 'system', '2026-08-22T19:30:00+08:00'::timestamptz),
  ('patient_instruction', 'manual'::public.source_type, 'clinician', '2026-08-20T14:15:00+08:00'::timestamptz),
  ('patient_summary', 'manual'::public.source_type, 'clinician', '2026-08-23T09:00:00+08:00'::timestamptz)
) as k(kind, source_type, author_kind, occurred_at)
on conflict (id) do nothing;

insert into public.entries (
  id, clinic_id, patient_id, care_note_id, author_id, author_role, entry_type,
  visibility, content, content_plaintext, source_record_id, current_version, occurred_at
)
select
  md5(f.patient_id::text || ':entry:' || k.kind)::uuid,
  f.clinic_id,
  f.patient_id,
  f.care_note_id,
  case k.author_kind
    when 'patient' then f.patient_profile_id
    when 'staff' then f.staff_id
    when 'clinician' then f.clinician_id
    else null
  end,
  k.author_role,
  k.entry_type,
  k.visibility,
  case k.kind
    when 'patient_update' then f.patient_update
    when 'staff_note' then f.staff_note
    when 'clinician_note' then f.clinician_note_v2
    when 'doctor_session' then f.doctor_summary
    when 'nurse_session' then f.nurse_summary
    when 'ai_patient_session' then f.ai_patient_summary
    when 'patient_instruction' then f.patient_instruction
    else f.patient_summary
  end,
  case k.kind
    when 'patient_update' then f.patient_update
    when 'staff_note' then f.staff_note
    when 'clinician_note' then f.clinician_note_v2
    when 'doctor_session' then f.doctor_summary
    when 'nurse_session' then f.nurse_summary
    when 'ai_patient_session' then f.ai_patient_summary
    when 'patient_instruction' then f.patient_instruction
    else f.patient_summary
  end,
  md5(f.patient_id::text || ':source:' || k.kind)::uuid,
  case when k.kind = 'clinician_note' then 2 else 1 end,
  k.occurred_at
from rich_demo_patients f
cross join (values
  ('patient_update', 'patient', 'patient'::public.author_role, 'patient_insight'::public.entry_type, 'internal'::public.entry_visibility, '2026-08-18T08:10:00+08:00'::timestamptz),
  ('staff_note', 'staff', 'staff'::public.author_role, 'staff_note'::public.entry_type, 'internal'::public.entry_visibility, '2026-08-19T10:20:00+08:00'::timestamptz),
  ('clinician_note', 'clinician', 'clinician'::public.author_role, 'clinician_note'::public.entry_type, 'internal'::public.entry_visibility, '2026-08-20T14:00:00+08:00'::timestamptz),
  ('doctor_session', 'system', 'system'::public.author_role, 'ai_doctor_consult_summary'::public.entry_type, 'internal'::public.entry_visibility, '2026-08-20T14:05:00+08:00'::timestamptz),
  ('nurse_session', 'system', 'system'::public.author_role, 'ai_nurse_consult_summary'::public.entry_type, 'internal'::public.entry_visibility, '2026-08-21T11:15:00+08:00'::timestamptz),
  ('ai_patient_session', 'system', 'system'::public.author_role, 'ai_patient_session_summary'::public.entry_type, 'internal'::public.entry_visibility, '2026-08-22T19:30:00+08:00'::timestamptz),
  ('patient_instruction', 'clinician', 'clinician'::public.author_role, 'patient_instruction'::public.entry_type, 'patient_facing'::public.entry_visibility, '2026-08-20T14:15:00+08:00'::timestamptz),
  ('patient_summary', 'clinician', 'clinician'::public.author_role, 'patient_summary'::public.entry_type, 'patient_facing'::public.entry_visibility, '2026-08-23T09:00:00+08:00'::timestamptz)
) as k(kind, author_kind, author_role, entry_type, visibility, occurred_at)
on conflict (id) do update set
  content = excluded.content,
  content_plaintext = excluded.content_plaintext,
  current_version = excluded.current_version;

insert into public.entry_versions (
  id, clinic_id, patient_id, entry_id, version_number, content_snapshot,
  changed_by, changed_by_role, change_reason, created_at
)
select
  md5(f.patient_id::text || ':entry-version:' || k.kind || ':1')::uuid,
  f.clinic_id,
  f.patient_id,
  md5(f.patient_id::text || ':entry:' || k.kind)::uuid,
  1,
  case k.kind
    when 'patient_update' then f.patient_update
    when 'staff_note' then f.staff_note
    when 'clinician_note' then f.clinician_note_v1
    when 'doctor_session' then f.doctor_summary
    when 'nurse_session' then f.nurse_summary
    when 'ai_patient_session' then f.ai_patient_summary
    when 'patient_instruction' then f.patient_instruction
    else f.patient_summary
  end,
  case k.author_kind
    when 'patient' then f.patient_profile_id
    when 'staff' then f.staff_id
    when 'clinician' then f.clinician_id
    else null
  end,
  k.author_role,
  'Initial synthetic version',
  k.created_at
from rich_demo_patients f
cross join (values
  ('patient_update', 'patient', 'patient'::public.author_role, '2026-08-18T08:10:00+08:00'::timestamptz),
  ('staff_note', 'staff', 'staff'::public.author_role, '2026-08-19T10:20:00+08:00'::timestamptz),
  ('clinician_note', 'clinician', 'clinician'::public.author_role, '2026-08-20T13:50:00+08:00'::timestamptz),
  ('doctor_session', 'system', 'system'::public.author_role, '2026-08-20T14:05:00+08:00'::timestamptz),
  ('nurse_session', 'system', 'system'::public.author_role, '2026-08-21T11:15:00+08:00'::timestamptz),
  ('ai_patient_session', 'system', 'system'::public.author_role, '2026-08-22T19:30:00+08:00'::timestamptz),
  ('patient_instruction', 'clinician', 'clinician'::public.author_role, '2026-08-20T14:15:00+08:00'::timestamptz),
  ('patient_summary', 'clinician', 'clinician'::public.author_role, '2026-08-23T09:00:00+08:00'::timestamptz)
) as k(kind, author_kind, author_role, created_at)
on conflict (entry_id, version_number) do nothing;

insert into public.entry_versions (
  id, clinic_id, patient_id, entry_id, version_number, content_snapshot,
  changed_by, changed_by_role, change_reason, created_at
)
select
  md5(f.patient_id::text || ':entry-version:clinician_note:2')::uuid,
  f.clinic_id,
  f.patient_id,
  md5(f.patient_id::text || ':entry:clinician_note')::uuid,
  2,
  f.clinician_note_v2,
  f.clinician_id,
  'clinician',
  'Synthetic revision: added explicit follow-up detail',
  '2026-08-20T14:00:00+08:00'
from rich_demo_patients f
on conflict (entry_id, version_number) do nothing;

insert into public.note_sections (
  id, clinic_id, patient_id, care_note_id, section_type, owner_role,
  created_by, visibility, content
)
select
  md5(f.patient_id::text || ':section:' || k.section_type::text)::uuid,
  f.clinic_id,
  f.patient_id,
  f.care_note_id,
  k.section_type,
  k.owner_role,
  case when k.owner_role = 'staff' then f.staff_id else f.clinician_id end,
  k.visibility,
  case k.section_type
    when 'staff_note' then 'Synthetic coordination status: follow-up workflow is open.'
    when 'assessment' then f.clinician_note_v2
    when 'plan' then f.task_title || '; confirm at the next review.'
    else f.patient_instruction
  end
from rich_demo_patients f
cross join (values
  ('staff_note'::public.section_type, 'staff'::public.author_role, 'internal'::public.entry_visibility),
  ('assessment'::public.section_type, 'clinician'::public.author_role, 'internal'::public.entry_visibility),
  ('plan'::public.section_type, 'clinician'::public.author_role, 'internal'::public.entry_visibility),
  ('patient_instruction'::public.section_type, 'clinician'::public.author_role, 'patient_facing'::public.entry_visibility)
) as k(section_type, owner_role, visibility)
on conflict (id) do nothing;

insert into public.section_versions (
  clinic_id, patient_id, section_id, version_number, content_snapshot,
  changed_by, changed_by_role, change_reason
)
select
  section.clinic_id,
  section.patient_id,
  section.id,
  1,
  section.content,
  section.created_by,
  section.owner_role,
  'Initial synthetic version'
from public.note_sections section
join rich_demo_patients f on f.patient_id = section.patient_id
on conflict (section_id, version_number) do nothing;

insert into public.comments (
  id, clinic_id, patient_id, entry_id, author_id, body, status, assigned_to, resolved_at
)
select
  md5(f.patient_id::text || ':comment:open')::uuid,
  f.clinic_id,
  f.patient_id,
  md5(f.patient_id::text || ':entry:doctor_session')::uuid,
  f.staff_id,
  'Internal synthetic comment: please confirm the review timing after the diary is complete.',
  'open',
  f.clinician_id,
  null
from rich_demo_patients f
union all
select
  md5(f.patient_id::text || ':comment:resolved')::uuid,
  f.clinic_id,
  f.patient_id,
  md5(f.patient_id::text || ':entry:nurse_session')::uuid,
  f.clinician_id,
  'Internal synthetic comment: education step confirmed.',
  'resolved',
  null,
  '2026-08-21T12:00:00+08:00'
from rich_demo_patients f
on conflict (id) do update set
  body = excluded.body,
  status = excluded.status,
  assigned_to = excluded.assigned_to,
  resolved_at = excluded.resolved_at;

insert into public.highlights (
  id, clinic_id, patient_id, source_entry_id, source_version_id,
  source_start_offset, source_end_offset, quoted_text, normalized_claim,
  risk_level, risk_reason, score, status, generated_by, reviewed_by, reviewed_at,
  category
)
select
  md5(f.patient_id::text || ':highlight:attention')::uuid,
  f.clinic_id,
  f.patient_id,
  entry.id,
  version.id,
  strpos(version.content_snapshot, f.risk_quote) - 1,
  strpos(version.content_snapshot, f.risk_quote) - 1 + char_length(f.risk_quote),
  f.risk_quote,
  f.risk_reason,
  'attention',
  f.risk_reason,
  78.0,
  'accepted',
  'ai',
  f.clinician_id,
  '2026-08-23T10:00:00+08:00',
  'risk'
from rich_demo_patients f
join public.entries entry
  on entry.id = md5(f.patient_id::text || ':entry:doctor_session')::uuid
join public.entry_versions version
  on version.entry_id = entry.id and version.version_number = 1
where strpos(version.content_snapshot, f.risk_quote) > 0
on conflict (id) do nothing;

insert into public.care_tasks (
  id, clinic_id, patient_id, source_entry_id, title, assigned_to, created_by,
  status, priority, category, patient_visible, due_at, completed_at
)
select
  md5(f.patient_id::text || ':task:open')::uuid,
  f.clinic_id,
  f.patient_id,
  md5(f.patient_id::text || ':entry:clinician_note')::uuid,
  f.task_title,
  f.clinician_id,
  f.staff_id,
  'open',
  'high',
  'monitoring',
  true,
  '2026-09-04T17:00:00+08:00',
  null
from rich_demo_patients f
union all
select
  md5(f.patient_id::text || ':task:complete')::uuid,
  f.clinic_id,
  f.patient_id,
  md5(f.patient_id::text || ':entry:nurse_session')::uuid,
  'Confirm synthetic coaching step',
  f.staff_id,
  f.clinician_id,
  'completed',
  'normal',
  'clinical_review',
  false,
  '2026-08-22T17:00:00+08:00',
  '2026-08-21T12:00:00+08:00'
from rich_demo_patients f
on conflict (id) do update set
  title = excluded.title,
  assigned_to = excluded.assigned_to,
  status = excluded.status,
  priority = excluded.priority,
  category = excluded.category,
  patient_visible = excluded.patient_visible,
  due_at = excluded.due_at,
  completed_at = excluded.completed_at;

insert into public.notification_outbox (
  id, clinic_id, patient_id, recipient_id, event_type, resource_type,
  resource_id, status, delivered_at, read_at, created_at
)
select
  md5(f.patient_id::text || ':notification:staff')::uuid,
  f.clinic_id,
  f.patient_id,
  f.staff_id,
  'care_update',
  'patient',
  f.patient_id,
  'delivered',
  '2026-08-23T09:05:00+08:00',
  null,
  '2026-08-23T09:05:00+08:00'
from rich_demo_patients f
union all
select
  md5(f.patient_id::text || ':notification:clinician')::uuid,
  f.clinic_id,
  f.patient_id,
  f.clinician_id,
  'assignment',
  'care_task',
  md5(f.patient_id::text || ':task:open')::uuid,
  'delivered',
  '2026-08-23T09:06:00+08:00',
  null,
  '2026-08-23T09:06:00+08:00'
from rich_demo_patients f
union all
select
  md5(f.patient_id::text || ':notification:patient')::uuid,
  f.clinic_id,
  f.patient_id,
  f.patient_profile_id,
  'care_update',
  'patient_summary',
  md5(f.patient_id::text || ':entry:patient_summary')::uuid,
  'delivered',
  '2026-08-23T09:07:00+08:00',
  null,
  '2026-08-23T09:07:00+08:00'
from rich_demo_patients f
on conflict (recipient_id, event_type, resource_id) do nothing;

insert into public.appointment_requests (
  id, clinic_id, patient_id, requested_by, preferred_date,
  time_preference, reason_category, note, status, created_at
)
select
  md5(f.patient_id::text || ':appointment')::uuid,
  f.clinic_id,
  f.patient_id,
  f.patient_profile_id,
  current_date + 7,
  case when f.story_key in ('riley', 'quinn') then 'afternoon' else 'morning' end,
  'follow_up',
  'Synthetic demo appointment request; contains no real health information.',
  'requested',
  '2026-08-24T09:00:00+08:00'
from rich_demo_patients f
on conflict (id) do nothing;

insert into public.patient_reports (
  id, clinic_id, patient_id, title, report_type, status,
  released_at, released_by, patient_safe_summary, created_at
)
select
  md5(f.patient_id::text || ':report:available')::uuid,
  f.clinic_id,
  f.patient_id,
  'Synthetic care-plan summary',
  'care_plan',
  'available',
  '2026-08-23T09:00:00+08:00',
  f.clinician_id,
  'Released synthetic report: ' || f.patient_summary,
  '2026-08-23T08:50:00+08:00'
from rich_demo_patients f
union all
select
  md5(f.patient_id::text || ':report:preparing')::uuid,
  f.clinic_id,
  f.patient_id,
  'Synthetic follow-up report',
  'other',
  'preparing',
  null,
  null,
  null,
  '2026-08-24T08:00:00+08:00'
from rich_demo_patients f
on conflict (id) do nothing;

insert into public.patient_observations (
  id, clinic_id, patient_id, recorded_by, observation_type, value, unit, observed_at
)
select
  md5(f.patient_id::text || ':observation:' || observation.day_offset::text)::uuid,
  f.clinic_id,
  f.patient_id,
  f.patient_profile_id,
  observation.observation_type,
  observation.value,
  observation.unit,
  ('2026-08-20T08:00:00+08:00'::timestamptz + make_interval(days => observation.day_offset))
from rich_demo_patients f
cross join (values
  (0, 'symptom_score', 6.0, 'score/10'),
  (1, 'symptom_score', 5.0, 'score/10'),
  (2, 'symptom_score', 4.0, 'score/10')
) as observation(day_offset, observation_type, value, unit)
on conflict (id) do nothing;

-- Complete the primary Parker story with a released summary and portal fixtures.
insert into public.source_records (
  id, clinic_id, patient_id, source_type, external_reference, occurred_at, created_by, metadata
)
values (
  '60000000-0000-0000-0000-000000000010',
  '10000000-0000-0000-0000-000000000001',
  '40000000-0000-0000-0000-000000000001',
  'manual', 'patient-summary-001', '2026-08-26T09:30:00+08:00',
  '20000000-0000-0000-0000-000000000003',
  '{"synthetic":true,"released_artifact":true}'
)
on conflict (id) do nothing;

insert into public.entries (
  id, clinic_id, patient_id, care_note_id, author_id, author_role, entry_type,
  visibility, content, content_plaintext, source_record_id, occurred_at
)
values (
  '70000000-0000-0000-0000-000000000010',
  '10000000-0000-0000-0000-000000000001',
  '40000000-0000-0000-0000-000000000001',
  '50000000-0000-0000-0000-000000000001',
  '20000000-0000-0000-0000-000000000003',
  'clinician', 'patient_summary', 'patient_facing',
  'Your care team is reviewing the synthetic nighttime cough pattern. Continue the peak-flow diary and follow the released instructions.',
  'Your care team is reviewing the synthetic nighttime cough pattern. Continue the peak-flow diary and follow the released instructions.',
  '60000000-0000-0000-0000-000000000010',
  '2026-08-26T09:30:00+08:00'
)
on conflict (id) do nothing;

insert into public.entry_versions (
  id, clinic_id, patient_id, entry_id, version_number, content_snapshot,
  changed_by, changed_by_role, change_reason
)
values (
  'c0000000-0000-0000-0000-000000000010',
  '10000000-0000-0000-0000-000000000001',
  '40000000-0000-0000-0000-000000000001',
  '70000000-0000-0000-0000-000000000010',
  1,
  'Your care team is reviewing the synthetic nighttime cough pattern. Continue the peak-flow diary and follow the released instructions.',
  '20000000-0000-0000-0000-000000000003',
  'clinician',
  'Initial synthetic released summary'
)
on conflict (entry_id, version_number) do nothing;

insert into public.appointment_requests (
  id, clinic_id, patient_id, requested_by, preferred_date,
  time_preference, reason_category, note, status
)
values (
  'e1000000-0000-0000-0000-000000000001',
  '10000000-0000-0000-0000-000000000001',
  '40000000-0000-0000-0000-000000000001',
  '20000000-0000-0000-0000-000000000004',
  current_date + 6, 'morning', 'follow_up',
  'Synthetic appointment request for the diary review.', 'requested'
)
on conflict (id) do nothing;

insert into public.patient_reports (
  id, clinic_id, patient_id, title, report_type, status,
  released_at, released_by, patient_safe_summary
)
values
  (
    'e2000000-0000-0000-0000-000000000001',
    '10000000-0000-0000-0000-000000000001',
    '40000000-0000-0000-0000-000000000001',
    'Synthetic respiratory care-plan summary', 'care_plan', 'available',
    '2026-08-26T09:30:00+08:00',
    '20000000-0000-0000-0000-000000000003',
    'Released synthetic report: complete the seven-day diary and follow the patient-facing contact instructions.'
  ),
  (
    'e2000000-0000-0000-0000-000000000002',
    '10000000-0000-0000-0000-000000000001',
    '40000000-0000-0000-0000-000000000001',
    'Synthetic diary review report', 'other', 'preparing',
    null, null, null
  )
on conflict (id) do nothing;

insert into public.patient_observations (
  id, clinic_id, patient_id, recorded_by, observation_type, value, unit, observed_at
)
values
  ('e3000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000004', 'peak_flow', 385, 'L/min', '2026-08-24T08:00:00+08:00'),
  ('e3000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000004', 'peak_flow', 398, 'L/min', '2026-08-25T08:00:00+08:00'),
  ('e3000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000004', 'peak_flow', 410, 'L/min', '2026-08-26T08:00:00+08:00')
on conflict (id) do nothing;

insert into public.notification_outbox (
  id, clinic_id, patient_id, recipient_id, event_type, resource_type,
  resource_id, status, delivered_at, read_at
)
values
  ('e4000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000004', 'care_update', 'patient_summary', '70000000-0000-0000-0000-000000000010', 'delivered', '2026-08-26T09:35:00+08:00', null),
  ('e4000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000002', 'care_update', 'patient', '40000000-0000-0000-0000-000000000001', 'delivered', '2026-08-26T09:36:00+08:00', null)
on conflict (recipient_id, event_type, resource_id) do nothing;

insert into storage.buckets (id, name, public, file_size_limit)
values ('consult-recordings', 'consult-recordings', false, 52428800)
on conflict (id) do update set public = false, file_size_limit = excluded.file_size_limit;
