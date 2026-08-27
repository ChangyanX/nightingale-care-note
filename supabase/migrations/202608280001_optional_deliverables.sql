-- Consolidated additive schema for Phase 1-4 optional capabilities.
-- No clinical text is copied into audit, notification, or provider-usage metadata.

alter type public.ai_job_status add value if not exists 'cancelled';

begin;

create extension if not exists vector with schema extensions;

create type public.care_task_category as enum (
  'clinical_review', 'medication', 'monitoring', 'administrative', 'follow_up'
);
create type public.highlight_category as enum (
  'risk', 'symptom', 'medication', 'care_gap', 'patient_context', 'follow_up'
);
create type public.notification_status as enum ('pending', 'delivered', 'failed', 'dismissed');
create type public.ai_job_event_kind as enum (
  'queued', 'claimed', 'generating', 'validating', 'persisting', 'completed', 'failed', 'cancelled'
);

alter table public.patients
add column search_document tsvector generated always as (
  to_tsvector('simple'::regconfig, coalesce(display_name, '') || ' ' || coalesce(synthetic_identifier, ''))
) stored;

alter table public.entries
add column search_document tsvector generated always as (
  to_tsvector('simple'::regconfig, coalesce(content_plaintext, ''))
) stored;

create index patients_search_idx on public.patients using gin(search_document);
create index entries_search_idx on public.entries using gin(search_document);

alter table public.care_tasks
add column category public.care_task_category not null default 'follow_up',
add column patient_visible boolean not null default false,
add column patient_acknowledged_at timestamptz,
add column patient_acknowledged_by uuid references public.profiles(id) on delete set null,
add constraint care_task_patient_ack_consistent check (
  (patient_acknowledged_at is null and patient_acknowledged_by is null)
  or (patient_visible and patient_acknowledged_at is not null and patient_acknowledged_by is not null)
);

create table public.care_task_events (
  id uuid primary key default gen_random_uuid(),
  clinic_id uuid not null,
  patient_id uuid not null,
  care_task_id uuid not null,
  actor_id uuid references public.profiles(id) on delete set null,
  event_type text not null check (event_type ~ '^[a-z_]{1,40}$'),
  from_status public.care_task_status,
  to_status public.care_task_status,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  foreign key (care_task_id, clinic_id, patient_id)
    references public.care_tasks(id, clinic_id, patient_id) on delete cascade
);
create index care_task_events_task_time_idx
on public.care_task_events(care_task_id, created_at desc);

create function public.capture_care_task_event()
returns trigger language plpgsql security definer set search_path = '' as $$
begin
  if tg_op = 'INSERT' then
    insert into public.care_task_events (
      clinic_id, patient_id, care_task_id, actor_id, event_type, to_status
    ) values (new.clinic_id, new.patient_id, new.id, auth.uid(), 'created', new.status);
  elsif row(new.status, new.assigned_to, new.due_at, new.patient_acknowledged_at)
        is distinct from row(old.status, old.assigned_to, old.due_at, old.patient_acknowledged_at) then
    insert into public.care_task_events (
      clinic_id, patient_id, care_task_id, actor_id, event_type, from_status, to_status,
      metadata
    ) values (
      new.clinic_id, new.patient_id, new.id, auth.uid(),
      case when new.patient_acknowledged_at is distinct from old.patient_acknowledged_at
        then 'patient_acknowledged' else 'updated' end,
      old.status, new.status,
      jsonb_build_object(
        'assignee_changed', new.assigned_to is distinct from old.assigned_to,
        'due_at_changed', new.due_at is distinct from old.due_at
      )
    );
  end if;
  return new;
end;
$$;
create trigger capture_care_task_event_after_write
after insert or update on public.care_tasks
for each row execute function public.capture_care_task_event();

alter table public.comments
add column source_version_id uuid,
add column source_start_offset integer,
add column source_end_offset integer,
add column quoted_text text,
add column body_format text not null default 'plain' check (body_format in ('plain', 'markdown')),
add column body_rich jsonb,
add constraint comments_inline_span_complete check (
  (source_version_id is null and source_start_offset is null and source_end_offset is null and quoted_text is null)
  or (entry_id is not null and source_version_id is not null and source_start_offset >= 0
      and source_end_offset > source_start_offset and char_length(quoted_text) > 0)
),
add constraint comments_inline_version_fkey
  foreign key (source_version_id, clinic_id, patient_id, entry_id)
  references public.entry_versions(id, clinic_id, patient_id, entry_id) on delete restrict;

create function public.validate_comment_source_span()
returns trigger language plpgsql set search_path = '' as $$
declare historical_content text;
begin
  if new.source_version_id is null then return new; end if;
  select content_snapshot into historical_content
  from public.entry_versions
  where id = new.source_version_id and entry_id = new.entry_id
    and clinic_id = new.clinic_id and patient_id = new.patient_id;
  if not found or new.source_end_offset > char_length(historical_content)
    or substring(historical_content from new.source_start_offset + 1
      for new.source_end_offset - new.source_start_offset) <> new.quoted_text then
    raise exception using errcode = '23514', message = 'Comment quote does not match source span';
  end if;
  return new;
end;
$$;
create trigger validate_comment_source_span_before_write
before insert or update on public.comments
for each row execute function public.validate_comment_source_span();

create table public.comment_reactions (
  comment_id uuid not null,
  clinic_id uuid not null,
  patient_id uuid not null,
  profile_id uuid not null references public.profiles(id) on delete cascade,
  reaction text not null check (reaction in ('acknowledged', 'agree', 'question')),
  created_at timestamptz not null default now(),
  primary key (comment_id, profile_id, reaction),
  foreign key (comment_id, clinic_id, patient_id)
    references public.comments(id, clinic_id, patient_id) on delete cascade
);

create table public.comment_assignees (
  comment_id uuid not null,
  clinic_id uuid not null,
  patient_id uuid not null,
  profile_id uuid not null references public.profiles(id) on delete cascade,
  assigned_by uuid not null references public.profiles(id) on delete restrict,
  created_at timestamptz not null default now(),
  primary key (comment_id, profile_id),
  foreign key (comment_id, clinic_id, patient_id)
    references public.comments(id, clinic_id, patient_id) on delete cascade
);

alter table public.highlights
add column category public.highlight_category not null default 'risk',
add column duplicate_group_id uuid;
create index highlights_duplicate_group_idx
on public.highlights(patient_id, duplicate_group_id)
where duplicate_group_id is not null;

create table public.notification_outbox (
  id uuid primary key default gen_random_uuid(),
  clinic_id uuid not null references public.clinics(id) on delete cascade,
  patient_id uuid,
  recipient_id uuid not null references public.profiles(id) on delete cascade,
  event_type text not null check (event_type in ('mention', 'assignment', 'ai_job_completed')),
  resource_type text not null,
  resource_id uuid not null,
  status public.notification_status not null default 'pending',
  attempt_count integer not null default 0 check (attempt_count between 0 and 10),
  available_at timestamptz not null default now(),
  delivered_at timestamptz,
  safe_error_code text,
  created_at timestamptz not null default now(),
  unique (recipient_id, event_type, resource_id),
  foreign key (patient_id, clinic_id) references public.patients(id, clinic_id) on delete cascade,
  check ((status = 'delivered' and delivered_at is not null) or status <> 'delivered')
);
create index notification_outbox_recipient_idx
on public.notification_outbox(recipient_id, status, created_at desc);

create function public.queue_mention_notification()
returns trigger language plpgsql security definer set search_path = '' as $$
begin
  insert into public.notification_outbox (
    clinic_id, patient_id, recipient_id, event_type, resource_type, resource_id
  ) values (
    new.clinic_id, new.patient_id, new.mentioned_profile_id, 'mention', 'comment', new.comment_id
  ) on conflict (recipient_id, event_type, resource_id) do nothing;
  return new;
end;
$$;
create trigger queue_mention_notification_after_insert
after insert on public.mentions for each row execute function public.queue_mention_notification();

create function public.create_comment_with_collaboration(
  p_patient_id uuid,
  p_entry_id uuid,
  p_section_id uuid,
  p_parent_comment_id uuid,
  p_body text,
  p_body_format text,
  p_mention_ids uuid[],
  p_assignee_ids uuid[],
  p_source_version_id uuid,
  p_source_start_offset integer,
  p_source_end_offset integer,
  p_quoted_text text
)
returns public.comments language plpgsql security invoker set search_path = '' as $$
declare patient_row public.patients;
declare created_comment public.comments;
declare profile_id uuid;
begin
  select * into patient_row from public.patients where id = p_patient_id;
  if not found or not public.has_clinic_role(
    patient_row.clinic_id, array['staff','clinician']::public.clinic_role[]
  ) then
    raise exception using errcode = '42501', message = 'Role cannot create comment';
  end if;
  if num_nonnulls(p_entry_id, p_section_id) <> 1 then
    raise exception using errcode = '22023', message = 'Exactly one comment target is required';
  end if;
  insert into public.comments (
    clinic_id, patient_id, entry_id, section_id, parent_comment_id, author_id,
    body, body_format, source_version_id, source_start_offset, source_end_offset, quoted_text
  ) values (
    patient_row.clinic_id, patient_row.id, p_entry_id, p_section_id, p_parent_comment_id,
    auth.uid(), trim(p_body), p_body_format, p_source_version_id, p_source_start_offset,
    p_source_end_offset, p_quoted_text
  ) returning * into created_comment;
  foreach profile_id in array coalesce(p_mention_ids, array[]::uuid[]) loop
    insert into public.mentions (
      clinic_id, patient_id, comment_id, mentioned_profile_id, created_by
    ) values (
      created_comment.clinic_id, created_comment.patient_id, created_comment.id, profile_id, auth.uid()
    ) on conflict (comment_id, mentioned_profile_id) do nothing;
  end loop;
  foreach profile_id in array coalesce(p_assignee_ids, array[]::uuid[]) loop
    if not public.is_profile_in_clinic(profile_id, created_comment.clinic_id) then
      raise exception using errcode = '23514', message = 'Assignee must belong to clinic';
    end if;
    insert into public.comment_assignees (
      comment_id, clinic_id, patient_id, profile_id, assigned_by
    ) values (
      created_comment.id, created_comment.clinic_id, created_comment.patient_id, profile_id, auth.uid()
    );
  end loop;
  return created_comment;
end;
$$;

create table public.ai_job_events (
  id uuid primary key default gen_random_uuid(),
  clinic_id uuid not null,
  patient_id uuid not null,
  job_id uuid not null,
  event_kind public.ai_job_event_kind not null,
  safe_metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  foreign key (job_id) references public.ai_jobs(id) on delete cascade,
  foreign key (patient_id, clinic_id) references public.patients(id, clinic_id) on delete cascade
);
create index ai_job_events_job_time_idx on public.ai_job_events(job_id, created_at);

alter table public.ai_jobs
add column provider_name text,
add column model_name text,
add column provider_request_id_ciphertext bytea,
add column input_tokens integer check (input_tokens is null or input_tokens >= 0),
add column output_tokens integer check (output_tokens is null or output_tokens >= 0),
add column estimated_cost_usd numeric(12, 6) check (
  estimated_cost_usd is null or estimated_cost_usd >= 0
);

do $$
declare constraint_name text;
begin
  select conname into constraint_name
  from pg_constraint
  where conrelid = 'public.ai_jobs'::regclass
    and contype = 'c'
    and pg_get_constraintdef(oid) like '%output_entry_id%status%';
  if constraint_name is not null then
    execute format('alter table public.ai_jobs drop constraint %I', constraint_name);
  end if;
end;
$$;
alter table public.ai_jobs add constraint ai_jobs_status_consistent check (
  (status = 'queued' and claimed_at is null and lease_expires_at is null
    and completed_at is null and output_entry_id is null)
  or (status = 'processing' and claimed_at is not null and lease_expires_at is not null
    and completed_at is null and output_entry_id is null)
  or (status = 'succeeded' and completed_at is not null and output_entry_id is not null
    and safe_error_code is null)
  or (status in ('failed', 'dead_letter', 'cancelled') and completed_at is not null
    and output_entry_id is null and safe_error_code is not null)
);

create function public.cancel_ai_scribe_job(p_job_id uuid)
returns public.ai_jobs language plpgsql security invoker set search_path = '' as $$
declare cancelled_job public.ai_jobs;
begin
  update public.ai_jobs
  set status = 'cancelled', completed_at = now(), safe_error_code = 'cancelled_by_user'
  where id = p_job_id and status = 'queued' and requested_by = auth.uid()
  returning * into cancelled_job;
  if cancelled_job.id is null then
    raise exception using errcode = 'P0002', message = 'Cancellable AI job not found';
  end if;
  insert into public.ai_job_events (clinic_id, patient_id, job_id, event_kind)
  values (cancelled_job.clinic_id, cancelled_job.patient_id, cancelled_job.id, 'cancelled');
  return cancelled_job;
end;
$$;

create function public.ai_job_queue_position(p_job_id uuid)
returns integer language sql stable security invoker set search_path = '' as $$
  select case when target.status <> 'queued' then null else 1 + count(earlier.id)::integer end
  from public.ai_jobs target
  left join public.ai_jobs earlier
    on earlier.status = 'queued'
   and row(earlier.available_at, earlier.created_at, earlier.id)
       < row(target.available_at, target.created_at, target.id)
  where target.id = p_job_id
  group by target.status;
$$;

create function public.acknowledge_care_task(p_task_id uuid)
returns public.care_tasks language plpgsql security definer set search_path = '' as $$
declare acknowledged public.care_tasks;
begin
  update public.care_tasks task
  set patient_acknowledged_at = now(), patient_acknowledged_by = auth.uid()
  where task.id = p_task_id
    and task.patient_visible
    and public.is_linked_patient(task.patient_id, task.clinic_id)
  returning task.* into acknowledged;
  if acknowledged.id is null then
    raise exception using errcode = 'P0002', message = 'Visible care task not found';
  end if;
  return acknowledged;
end;
$$;

create function public.review_highlights_bulk(p_highlight_ids uuid[], p_status public.highlight_status)
returns setof public.highlights language plpgsql security invoker set search_path = '' as $$
begin
  if p_status not in ('accepted', 'rejected') then
    raise exception using errcode = '22023', message = 'Invalid review status';
  end if;
  return query
    update public.highlights highlight
    set status = p_status, reviewed_by = auth.uid(), reviewed_at = now()
    where highlight.id = any(p_highlight_ids)
      and highlight.status = 'suggested'
      and public.has_clinic_role(highlight.clinic_id, array['clinician']::public.clinic_role[])
    returning highlight.*;
end;
$$;

create function public.batch_revert_entries(p_operations jsonb)
returns setof public.entries language plpgsql security invoker set search_path = '' as $$
declare operation jsonb;
declare reverted public.entries;
begin
  if jsonb_typeof(p_operations) <> 'array' or jsonb_array_length(p_operations) not between 1 and 20 then
    raise exception using errcode = '22023', message = 'Invalid batch operations';
  end if;
  for operation in select value from jsonb_array_elements(p_operations) loop
    select * into reverted from public.revert_entry(
      (operation->>'entry_id')::uuid,
      (operation->>'source_version')::integer,
      (operation->>'expected_version')::integer,
      left(coalesce(operation->>'change_reason', 'Batch revert'), 500)
    );
    return next reverted;
  end loop;
end;
$$;

create table public.patient_summary_reviews (
  id uuid primary key default gen_random_uuid(),
  clinic_id uuid not null,
  patient_id uuid not null,
  source_entry_id uuid not null,
  summary_entry_id uuid,
  proposed_content text not null check (char_length(proposed_content) between 1 and 4000),
  status public.highlight_status not null default 'suggested',
  reviewed_by uuid references public.profiles(id) on delete set null,
  reviewed_at timestamptz,
  created_at timestamptz not null default now(),
  foreign key (source_entry_id, clinic_id, patient_id)
    references public.entries(id, clinic_id, patient_id) on delete cascade,
  foreign key (summary_entry_id, clinic_id, patient_id)
    references public.entries(id, clinic_id, patient_id) on delete restrict
);

create function public.review_patient_summary(
  p_review_id uuid, p_status public.highlight_status
)
returns public.patient_summary_reviews language plpgsql security invoker set search_path = '' as $$
declare review_row public.patient_summary_reviews;
declare source_entry public.entries;
declare summary_entry public.entries;
begin
  if p_status not in ('accepted', 'rejected') then
    raise exception using errcode = '22023', message = 'Invalid summary review status';
  end if;
  select * into review_row from public.patient_summary_reviews
  where id = p_review_id and status = 'suggested' for update;
  if not found or not public.has_clinic_role(
    review_row.clinic_id, array['clinician']::public.clinic_role[]
  ) then
    raise exception using errcode = '42501', message = 'Summary review unavailable';
  end if;
  if p_status = 'accepted' then
    select * into source_entry from public.entries where id = review_row.source_entry_id;
    insert into public.entries (
      clinic_id, patient_id, care_note_id, author_id, author_role, entry_type,
      visibility, content, content_plaintext, source_record_id, occurred_at
    ) values (
      review_row.clinic_id, review_row.patient_id, source_entry.care_note_id, auth.uid(),
      'clinician', 'patient_summary', 'patient_facing', review_row.proposed_content,
      review_row.proposed_content, source_entry.source_record_id, now()
    ) returning * into summary_entry;
    insert into public.entry_versions (
      clinic_id, patient_id, entry_id, version_number, content_snapshot,
      changed_by, changed_by_role, change_reason
    ) values (
      summary_entry.clinic_id, summary_entry.patient_id, summary_entry.id, 1,
      summary_entry.content, auth.uid(), 'clinician', 'Accepted patient-facing AI summary draft'
    );
    review_row.summary_entry_id := summary_entry.id;
  end if;
  update public.patient_summary_reviews
  set status = p_status, summary_entry_id = review_row.summary_entry_id,
      reviewed_by = auth.uid(), reviewed_at = now()
  where id = review_row.id returning * into review_row;
  return review_row;
end;
$$;

create table public.pseudonym_mappings (
  id uuid primary key default gen_random_uuid(),
  clinic_id uuid not null references public.clinics(id) on delete cascade,
  job_id uuid references public.ai_jobs(id) on delete cascade,
  placeholder text not null check (placeholder ~ '^\[PSEUDONYM_[A-Z_]+_[0-9]+\]$'),
  ciphertext bytea not null,
  key_version integer not null check (key_version > 0),
  expires_at timestamptz not null,
  created_at timestamptz not null default now(),
  unique (job_id, placeholder)
);
comment on table public.pseudonym_mappings is
  'Encrypted reversible mappings. Worker service role only; never browser accessible.';

create table public.importance_preferences (
  id uuid primary key default gen_random_uuid(),
  clinic_id uuid not null references public.clinics(id) on delete cascade,
  profile_id uuid references public.profiles(id) on delete cascade,
  topic text not null,
  weight numeric(5, 2) not null default 0 check (weight between -10 and 10),
  embedding extensions.vector(16),
  updated_at timestamptz not null default now(),
  unique nulls not distinct (clinic_id, profile_id, topic)
);

create table public.importance_feedback_events (
  id uuid primary key,
  clinic_id uuid not null references public.clinics(id) on delete cascade,
  profile_id uuid references public.profiles(id) on delete cascade,
  topic text not null,
  feedback_kind text not null check (feedback_kind in ('accept', 'reject', 'pin', 'edit', 'comment')),
  delta numeric(5, 2) not null,
  created_at timestamptz not null default now()
);

create function public.decayed_preference_weight(
  p_weight numeric, p_updated_at timestamptz, p_half_life_days numeric default 90
)
returns numeric language sql stable set search_path = '' as $$
  select p_weight * power(0.5, greatest(0, extract(epoch from (now() - p_updated_at)) / 86400) / p_half_life_days);
$$;

create function public.record_importance_feedback(
  p_event_id uuid,
  p_clinic_id uuid,
  p_topic text,
  p_feedback_kind text,
  p_embedding real[]
)
returns public.importance_preferences
language plpgsql security definer set search_path = '' as $$
declare normalized_topic text := lower(regexp_replace(trim(p_topic), '\s+', ' ', 'g'));
declare feedback_delta numeric;
declare inserted_count integer;
declare preference public.importance_preferences;
begin
  if not public.has_clinic_role(
    p_clinic_id, array['staff','clinician']::public.clinic_role[]
  ) then
    raise exception using errcode = '42501', message = 'Feedback unavailable';
  end if;
  if char_length(normalized_topic) not between 1 and 120 or array_length(p_embedding, 1) <> 16 then
    raise exception using errcode = '22023', message = 'Invalid preference topic';
  end if;
  feedback_delta := case p_feedback_kind
    when 'accept' then 1.0
    when 'reject' then -1.0
    when 'pin' then 1.5
    when 'edit' then 0.5
    when 'comment' then 0.25
    else null
  end;
  if feedback_delta is null then
    raise exception using errcode = '22023', message = 'Invalid feedback kind';
  end if;

  insert into public.importance_feedback_events (
    id, clinic_id, profile_id, topic, feedback_kind, delta
  ) values (
    p_event_id, p_clinic_id, auth.uid(), normalized_topic, p_feedback_kind, feedback_delta
  ) on conflict (id) do nothing;
  get diagnostics inserted_count = row_count;

  if inserted_count = 1 then
    insert into public.importance_preferences (
      clinic_id, profile_id, topic, weight, embedding
    ) values (
      p_clinic_id, auth.uid(), normalized_topic, feedback_delta,
      p_embedding::extensions.vector
    )
    on conflict (clinic_id, profile_id, topic) do update set
      weight = least(10, greatest(-10,
        public.importance_preferences.weight + excluded.weight
      )),
      embedding = excluded.embedding,
      updated_at = now()
    returning * into preference;
  else
    select * into preference from public.importance_preferences
    where clinic_id = p_clinic_id
      and profile_id = auth.uid()
      and topic = normalized_topic;
  end if;
  if preference.id is null then
    raise exception using errcode = 'P0002', message = 'Preference unavailable';
  end if;
  return preference;
end;
$$;

create function public.reset_importance_preferences(p_clinic_id uuid)
returns integer language plpgsql security definer set search_path = '' as $$
declare deleted_count integer;
begin
  if not public.has_clinic_role(
    p_clinic_id, array['staff','clinician']::public.clinic_role[]
  ) then
    raise exception using errcode = '42501', message = 'Preferences unavailable';
  end if;
  delete from public.importance_feedback_events
  where clinic_id = p_clinic_id and profile_id = auth.uid();
  delete from public.importance_preferences
  where clinic_id = p_clinic_id and profile_id = auth.uid();
  get diagnostics deleted_count = row_count;
  return deleted_count;
end;
$$;

create function public.write_metadata_audit_event()
returns trigger language plpgsql security definer set search_path = '' as $$
declare actor public.author_role;
declare target_id uuid;
begin
  actor := case
    when auth.uid() is null then 'system'::public.author_role
    when public.has_clinic_role(new.clinic_id, array['clinician']::public.clinic_role[])
      then 'clinician'::public.author_role
    else 'staff'::public.author_role
  end;
  target_id := new.id;
  insert into public.audit_events (
    clinic_id, patient_id, actor_id, actor_role, action, resource_type, resource_id, metadata
  ) values (
    new.clinic_id, new.patient_id, auth.uid(), actor,
    lower(tg_op), tg_table_name, target_id, jsonb_build_object('automatic', true)
  );
  return new;
end;
$$;
create trigger care_tasks_metadata_audit
after insert or update on public.care_tasks
for each row execute function public.write_metadata_audit_event();
create trigger comments_metadata_audit
after insert or update on public.comments
for each row execute function public.write_metadata_audit_event();
create trigger highlights_metadata_audit
after insert or update on public.highlights
for each row execute function public.write_metadata_audit_event();

alter table public.care_task_events enable row level security;
alter table public.comment_reactions enable row level security;
alter table public.comment_assignees enable row level security;
alter table public.notification_outbox enable row level security;
alter table public.ai_job_events enable row level security;
alter table public.patient_summary_reviews enable row level security;
alter table public.pseudonym_mappings enable row level security;
alter table public.importance_preferences enable row level security;
alter table public.importance_feedback_events enable row level security;

revoke all on public.care_task_events, public.comment_reactions, public.comment_assignees,
  public.notification_outbox, public.ai_job_events, public.patient_summary_reviews,
  public.pseudonym_mappings, public.importance_preferences, public.importance_feedback_events
from anon, authenticated;
grant select on public.care_task_events, public.comment_reactions, public.comment_assignees,
  public.notification_outbox, public.ai_job_events, public.patient_summary_reviews,
  public.importance_preferences, public.importance_feedback_events to authenticated;
grant insert, delete on public.comment_reactions, public.comment_assignees to authenticated;
grant update on public.notification_outbox, public.patient_summary_reviews to authenticated;

create policy optional_clinical_reads_task_events on public.care_task_events
for select to authenticated using (public.has_clinic_role(clinic_id, array['staff','clinician','admin']::public.clinic_role[]));
create policy optional_clinical_reactions on public.comment_reactions
for all to authenticated using (public.has_clinic_role(clinic_id, array['staff','clinician']::public.clinic_role[]))
with check (profile_id = auth.uid() and public.has_clinic_role(clinic_id, array['staff','clinician']::public.clinic_role[]));
create policy optional_clinical_assignees on public.comment_assignees
for all to authenticated using (public.has_clinic_role(clinic_id, array['staff','clinician','admin']::public.clinic_role[]))
with check (assigned_by = auth.uid() and public.is_profile_in_clinic(profile_id, clinic_id));
create policy optional_own_notifications on public.notification_outbox
for select to authenticated using (recipient_id = auth.uid());
create policy optional_own_notification_update on public.notification_outbox
for update to authenticated using (recipient_id = auth.uid())
with check (recipient_id = auth.uid() and status = 'dismissed');
create policy optional_clinical_job_events on public.ai_job_events
for select to authenticated using (public.has_clinic_role(clinic_id, array['staff','clinician','admin']::public.clinic_role[]));
create policy optional_clinical_summary_reviews on public.patient_summary_reviews
for select to authenticated using (public.has_clinic_role(clinic_id, array['staff','clinician','admin']::public.clinic_role[]));
create policy optional_clinician_summary_review_update on public.patient_summary_reviews
for update to authenticated using (public.has_clinic_role(clinic_id, array['clinician']::public.clinic_role[]))
with check (reviewed_by = auth.uid() and public.has_clinic_role(clinic_id, array['clinician']::public.clinic_role[]));
create policy optional_preferences_read on public.importance_preferences
for select to authenticated using (public.has_clinic_role(clinic_id, array['staff','clinician','admin']::public.clinic_role[]));
create policy optional_feedback_read on public.importance_feedback_events
for select to authenticated using (public.has_clinic_role(clinic_id, array['staff','clinician','admin']::public.clinic_role[]));

revoke all on function public.cancel_ai_scribe_job(uuid) from public;
grant execute on function public.cancel_ai_scribe_job(uuid) to authenticated;
revoke all on function public.ai_job_queue_position(uuid) from public;
grant execute on function public.ai_job_queue_position(uuid) to authenticated;
revoke all on function public.acknowledge_care_task(uuid) from public;
grant execute on function public.acknowledge_care_task(uuid) to authenticated;
revoke all on function public.review_highlights_bulk(uuid[], public.highlight_status) from public;
grant execute on function public.review_highlights_bulk(uuid[], public.highlight_status) to authenticated;
revoke all on function public.create_comment_with_collaboration(
  uuid, uuid, uuid, uuid, text, text, uuid[], uuid[], uuid, integer, integer, text
) from public;
grant execute on function public.create_comment_with_collaboration(
  uuid, uuid, uuid, uuid, text, text, uuid[], uuid[], uuid, integer, integer, text
) to authenticated;
revoke all on function public.batch_revert_entries(jsonb) from public;
grant execute on function public.batch_revert_entries(jsonb) to authenticated;
revoke all on function public.review_patient_summary(uuid, public.highlight_status) from public;
grant execute on function public.review_patient_summary(uuid, public.highlight_status) to authenticated;
revoke all on function public.decayed_preference_weight(numeric, timestamptz, numeric) from public;
grant execute on function public.decayed_preference_weight(numeric, timestamptz, numeric) to authenticated;
revoke all on function public.record_importance_feedback(uuid, uuid, text, text, real[]) from public;
grant execute on function public.record_importance_feedback(uuid, uuid, text, text, real[]) to authenticated;
revoke all on function public.reset_importance_preferences(uuid) from public;
grant execute on function public.reset_importance_preferences(uuid) to authenticated;

alter table public.ai_jobs replica identity full;
alter table public.ai_job_events replica identity full;
alter table public.notification_outbox replica identity full;

do $$
declare realtime_table text;
begin
  if exists (select 1 from pg_publication where pubname = 'supabase_realtime') then
    foreach realtime_table in array array['ai_jobs', 'ai_job_events', 'notification_outbox'] loop
      if not exists (
        select 1 from pg_publication_tables
        where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = realtime_table
      ) then
        execute format('alter publication supabase_realtime add table public.%I', realtime_table);
      end if;
    end loop;
  end if;
end;
$$;

commit;
