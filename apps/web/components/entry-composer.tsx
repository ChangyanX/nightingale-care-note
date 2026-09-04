"use client";

import { FormEvent, useState } from "react";

import { ApiError, apiPost } from "@/lib/api/client";
import type { ClinicRole, TimelineEntry } from "@/lib/api/types";

type ManualEntryType = "staff_note" | "clinician_note" | "patient_summary" | "patient_instruction";

const CLINICIAN_OPTIONS: { value: ManualEntryType; label: string; description: string }[] = [
  { value: "clinician_note", label: "Clinician note", description: "Internal clinical record" },
  { value: "patient_summary", label: "Patient care summary", description: "Published to the patient" },
  { value: "patient_instruction", label: "Patient instruction", description: "Published to the patient" },
];

function localDateTimeValue(date: Date) {
  const offset = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}

export function EntryComposer({
  accessToken,
  patientId,
  role,
  onCreated,
}: {
  accessToken: string;
  patientId: string;
  role: ClinicRole;
  onCreated: (entry: TimelineEntry) => void;
}) {
  const options = role === "staff"
    ? [{ value: "staff_note" as const, label: "Staff note", description: "Internal care-team context" }]
    : role === "clinician" ? CLINICIAN_OPTIONS : [];
  const [open, setOpen] = useState(false);
  const [entryType, setEntryType] = useState<ManualEntryType>(options[0]?.value ?? "clinician_note");
  const [content, setContent] = useState("");
  const [occurredAt, setOccurredAt] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!options.length) return null;

  function showComposer() {
    setOccurredAt((current) => current || localDateTimeValue(new Date()));
    setOpen(true);
  }

  function closeComposer() {
    if (saving) return;
    setOpen(false);
    setError(null);
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!content.trim()) return;
    setSaving(true);
    setError(null);
    const visibility = entryType === "patient_summary" || entryType === "patient_instruction"
      ? "patient_facing"
      : "internal";
    try {
      const entry = await apiPost<TimelineEntry>("/entries", accessToken, {
        patient_id: patientId,
        entry_type: entryType,
        visibility,
        content,
        occurred_at: occurredAt ? new Date(occurredAt).toISOString() : null,
      });
      onCreated(entry);
      setContent("");
      setOpen(false);
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 403) {
        setError("Your role cannot create this type of update.");
      } else {
        setError("The update could not be saved. Your text remains here so you can retry.");
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="entry-composer">
      {!open ? <button className="primary-button" type="button" onClick={showComposer}>Add update</button> : (
        <form onSubmit={submit}>
          <div className="entry-composer-heading">
            <div><p className="eyebrow">Authenticated as {role}</p><h3>Add to the timeline</h3></div>
            <button className="text-button" type="button" onClick={closeComposer}>Cancel</button>
          </div>
          <div className="entry-composer-fields">
            <label>Update type
              <select value={entryType} onChange={(event) => setEntryType(event.target.value as ManualEntryType)}>
                {options.map((option) => <option value={option.value} key={option.value}>{option.label} · {option.description}</option>)}
              </select>
            </label>
            <label>Clinical event time
              <input required type="datetime-local" value={occurredAt} onChange={(event) => setOccurredAt(event.target.value)} />
            </label>
            <label className="entry-composer-content">Note
              <textarea required maxLength={20_000} value={content} onChange={(event) => setContent(event.target.value)} placeholder="Record the clinically relevant update and follow-through." />
            </label>
          </div>
          <div className="entry-composer-footer">
            <p>{entryType === "patient_summary" || entryType === "patient_instruction" ? "This will be released to the patient." : "Internal care-team content. Patients cannot access it."}</p>
            {error ? <p className="form-error" role="alert">{error}</p> : null}
            <button className="primary-button" disabled={saving || !content.trim()} type="submit">{saving ? "Saving…" : "Save update"}</button>
          </div>
        </form>
      )}
    </div>
  );
}
