"use client";

import { FormEvent, useRef, useState } from "react";

import { ApiError, apiPost } from "@/lib/api/client";
import type { ScribeJob } from "@/lib/api/types";

type Props = {
  accessToken: string;
  patientId: string;
  role: "staff" | "clinician" | "admin";
  onQueued: (job: ScribeJob) => void;
};

const EXAMPLES = {
  clinician: "Synthetic consult: The patient reports fewer night-time cough episodes. Peak flow has improved from 380 to 410 L/min. Continue the prescribed inhaler and review the seven-day diary next week.",
  staff: "Synthetic nursing check-in: The patient demonstrated correct inhaler technique, reports no dizziness, and will complete morning and evening peak-flow readings for seven days.",
};

export function LiveScribeGenerator({ accessToken, patientId, role, onQueued }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [pending, setPending] = useState(false);
  const [feedback, setFeedback] = useState<{ kind: "success" | "error"; message: string } | null>(null);
  const pendingIdempotencyKey = useRef<string | null>(null);

  if (role === "admin") {
    return (
      <section className="live-scribe-panel read-only" aria-label="AI timeline generation">
        <div><p className="eyebrow">AI timeline generation</p><h2>Read-only oversight</h2></div>
        <p>Admins can monitor generated entries but cannot create clinical content.</p>
      </section>
    );
  }

  const interactionType = role === "clinician" ? "doctor_consult" : "nurse_consult";

  function requestKey() {
    if (pendingIdempotencyKey.current) return pendingIdempotencyKey.current;
    const entropy = new Uint32Array(4);
    window.crypto.getRandomValues(entropy);
    const randomPart = typeof window.crypto.randomUUID === "function"
      ? window.crypto.randomUUID()
      : Array.from(entropy, (value) => value.toString(16).padStart(8, "0")).join("");
    pendingIdempotencyKey.current = `live-${interactionType}-${randomPart}`;
    return pendingIdempotencyKey.current;
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setFeedback(null);
    try {
      const job = await apiPost<ScribeJob>(
        `/patients/${patientId}/scribe-sessions`,
        accessToken,
        {
          interaction_type: interactionType,
          transcript,
          idempotency_key: requestKey(),
        },
      );
      pendingIdempotencyKey.current = null;
      onQueued(job);
      setTranscript("");
      setExpanded(false);
      setFeedback({ kind: "success", message: "Generation queued. The timeline will update automatically when validation finishes." });
    } catch (error) {
      const reason = error instanceof ApiError
        ? error.message
        : "The API could not be reached. Confirm the API is running, then retry.";
      setFeedback({ kind: "error", message: `Generation was not queued. ${reason}` });
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="live-scribe-panel" aria-labelledby="live-scribe-title">
      <div className="live-scribe-heading">
        <div><p className="eyebrow">AI timeline generation</p><h2 id="live-scribe-title">Create from this interaction</h2></div>
        <button className="primary-button" type="button" onClick={() => setExpanded((value) => !value)} aria-expanded={expanded}>
          {expanded ? "Close generator" : "Generate AI summary"}
        </button>
      </div>
      <p>The source note is saved under your role, redacted before the LLM call, and linked to a separate system-authored summary for clinician review.</p>
      {feedback ? <p className={feedback.kind === "error" ? "form-error" : "form-success"} role={feedback.kind === "error" ? "alert" : "status"}>{feedback.message}</p> : null}
      {expanded ? <form className="live-scribe-form" onSubmit={submit}>
        <div className="generation-boundary"><strong>{role === "clinician" ? "Doctor consult" : "Nurse consult"}</strong><span>Internal · synthetic demo text only</span></div>
        <label htmlFor="scribe-transcript">Interaction notes or transcript</label>
        <textarea id="scribe-transcript" required minLength={20} maxLength={12000} rows={7} value={transcript} onChange={(event) => setTranscript(event.target.value)} />
        <div className="live-scribe-actions">
          <button className="text-button" type="button" onClick={() => setTranscript(EXAMPLES[role])}>Use synthetic example</button>
          <button className="primary-button" type="submit" disabled={pending}>{pending ? "Queueing…" : "Save source and generate"}</button>
        </div>
      </form> : null}
    </section>
  );
}
