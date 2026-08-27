export type ClinicRole = "staff" | "clinician" | "admin";

export type Membership = { clinic_id: string; role: ClinicRole };

export type CurrentUser = {
  id: string;
  email: string | null;
  display_name: string;
  memberships: Membership[];
};

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
};
