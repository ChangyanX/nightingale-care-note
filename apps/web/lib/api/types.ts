export type ClinicRole = "staff" | "clinician" | "admin";

export type Membership = { clinic_id: string; role: ClinicRole };

export type CurrentUser = {
  id: string;
  email: string | null;
  display_name: string;
  preferred_name: string;
  memberships: Membership[];
  linked_patient_id: string | null;
  account_kind: "clinic_user" | "patient";
  landing_path: "/patients" | "/patient";
};

export type AccountProfile = {
  id: string; email: string | null; display_name: string; preferred_name: string;
  birth_date: string | null; avatar_path: string | null; avatar_url: string | null;
  memberships: Membership[]; linked_patient_id: string | null;
};

export type Notification = {
  id: string; clinic_id: string; patient_id: string | null; recipient_id: string;
  event_type: "mention" | "assignment" | "ai_job_completed" | "care_update" | "appointment_update" | "report_released";
  resource_type: string; resource_id: string; status: "pending" | "delivered" | "failed" | "dismissed";
  read_at: string | null; created_at: string;
};

export type PatientSafeEntry = { id: string; entry_type: "patient_summary" | "patient_instruction" | "patient_insight"; content: string; occurred_at: string };
export type AppointmentRequest = { id: string; preferred_date: string; time_preference: "morning" | "afternoon" | "either"; reason_category: "follow_up" | "new_symptom" | "medication" | "other"; note: string | null; status: "requested" | "confirmed" | "declined" | "cancelled"; created_at: string };
export type PatientReport = { id: string; title: string; report_type: "lab" | "imaging" | "care_plan" | "other"; status: "preparing" | "available" | "withdrawn"; released_at: string | null; patient_safe_summary: string | null };
export type PatientObservation = { observation_type: "peak_flow" | "sleep_hours" | "symptom_score"; value: number; unit: string; observed_at: string };
export type PatientVisibleTask = { id: string; title: string; status: CareTask["status"]; due_at: string | null; patient_acknowledged_at: string | null };
export type PatientDashboard = { patient_id: string; display_name: string; synthetic_identifier: string; clinic_id: string; summaries: PatientSafeEntry[]; instructions: PatientSafeEntry[]; history: PatientSafeEntry[]; appointments: AppointmentRequest[]; reports: PatientReport[]; observations: PatientObservation[]; visible_tasks: PatientVisibleTask[] };

export type Patient = {
  id: string;
  clinic_id: string;
  synthetic_identifier: string;
  display_name: string;
};

export type SourceRecord = {
  id: string;
  source_type: string;
  external_reference: string | null;
  occurred_at: string;
};

export type TimelineEntry = {
  id: string;
  clinic_id: string;
  patient_id: string;
  author_id: string | null;
  author_role: "patient" | "staff" | "clinician" | "system";
  entry_type: string;
  visibility: "internal" | "patient_facing";
  content: string;
  source_record_id: string;
  current_version: number;
  occurred_at: string;
  source: SourceRecord | null;
};

export type CareTask = {
  id: string;
  clinic_id: string;
  patient_id: string;
  source_entry_id: string | null;
  title: string;
  assigned_to: string | null;
  created_by: string;
  status: "open" | "in_progress" | "completed" | "cancelled";
  priority: "low" | "normal" | "high" | "urgent";
  category: "clinical_review" | "medication" | "monitoring" | "administrative" | "follow_up";
  patient_visible: boolean;
  patient_acknowledged_at: string | null;
  due_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type GlanceItem = {
  kind: "current_concern" | "recent_change" | "open_action" | "patient_question";
  claim: string;
  importance_reason: string;
  status: string;
  occurred_at: string;
  source_entry_id: string;
  task_id: string | null;
  source: SourceRecord | null;
};

export type Glance = { patient_id: string; items: GlanceItem[] };

export type Revision = {
  resource_type: "entry" | "section";
  resource_id: string;
  version_number: number;
  content_snapshot: string;
  changed_by: string | null;
  changed_by_role: "patient" | "staff" | "clinician" | "system";
  change_reason: string | null;
  created_at: string;
};

export type RevisionComparison = {
  resource_type: "entry" | "section";
  resource_id: string;
  selected_version: number;
  current_version: number;
  selected_content: string;
  current_content: string;
  has_changes: boolean;
  unified_diff: string;
  word_diff: { kind: "unchanged" | "removed" | "added"; text: string }[];
};

export type Highlight = {
  id: string;
  clinic_id: string;
  patient_id: string;
  source_entry_id: string;
  source_version_id: string;
  source_start_offset: number;
  source_end_offset: number;
  quoted_text: string;
  normalized_claim: string;
  risk_level: "information" | "attention" | "critical";
  category: "risk" | "symptom" | "medication" | "care_gap" | "patient_context" | "follow_up";
  risk_reason: string;
  score: number;
  status: "suggested" | "accepted" | "rejected";
  generated_by: "rule" | "ai" | "clinician";
  duplicate_group_id: string | null;
  reviewed_by: string | null;
  reviewed_at: string | null;
  created_at: string;
};

export type Comment = {
  id: string;
  clinic_id: string;
  patient_id: string;
  entry_id: string | null;
  section_id: string | null;
  parent_comment_id: string | null;
  author_id: string;
  body: string;
  body_format: "plain" | "markdown";
  status: "open" | "resolved";
  assigned_to: string | null;
  source_version_id: string | null;
  source_start_offset: number | null;
  source_end_offset: number | null;
  quoted_text: string | null;
  created_at: string;
  resolved_at: string | null;
  reaction_counts: Record<"acknowledged" | "agree" | "question", number>;
  my_reactions: ("acknowledged" | "agree" | "question")[];
};

export type ScribeJob = {
  id: string;
  patient_id: string;
  interaction_type: "doctor_consult" | "nurse_consult" | "ai_patient_session";
  status: "queued" | "processing" | "succeeded" | "failed" | "dead_letter" | "cancelled";
  attempt_count: number;
  queue_position: number | null;
  output_entry_id: string | null;
  provider_name: string | null;
  model_name: string | null;
  created_at: string;
  updated_at: string;
};

export type ScribeJobEvent = {
  id: string;
  job_id: string;
  event_kind: "generating" | "validating" | "persisting" | "completed" | "retrying" | "cancelled";
  created_at: string;
};

export type ProviderUsage = {
  provider: string;
  model: string;
  calls: number;
  input_tokens: number;
  output_tokens: number;
  average_latency_ms: number;
  estimated_cost_usd: number;
};

export type ImportancePreference = {
  id: string;
  clinic_id: string;
  profile_id: string;
  topic: string;
  weight: number;
  updated_at: string;
};
