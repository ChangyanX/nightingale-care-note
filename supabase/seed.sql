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
  ('00000000-0000-0000-0000-000000000000', '20000000-0000-0000-0000-000000000006', 'authenticated', 'authenticated', 'clinician.b@nightingale.local', extensions.crypt('NightingaleDemo2026!', extensions.gen_salt('bf')), now(), '{"provider":"email","providers":["email"]}', '{"display_name":"Dr. Jordan Clinician"}', now(), now(), '', '', '', '')
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
  ('30000000-0000-0000-0000-000000000006', '20000000-0000-0000-0000-000000000006', '20000000-0000-0000-0000-000000000006', '{"sub":"20000000-0000-0000-0000-000000000006","email":"clinician.b@nightingale.local"}', 'email', now(), now(), now())
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
  ('20000000-0000-0000-0000-000000000006', 'Dr. Jordan Clinician')
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
  ('40000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000001', null, 'SYN-A-002', 'Morgan Example'),
  ('40000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000002', null, 'SYN-B-001', 'Riley Example')
on conflict (id) do nothing;

insert into public.care_notes (id, clinic_id, patient_id)
values
  ('50000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001'),
  ('50000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000002'),
  ('50000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000002', '40000000-0000-0000-0000-000000000003')
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

insert into storage.buckets (id, name, public, file_size_limit)
values ('consult-recordings', 'consult-recordings', false, 52428800)
on conflict (id) do update set public = false, file_size_limit = excluded.file_size_limit;
