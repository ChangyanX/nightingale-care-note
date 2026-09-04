"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { AppHeader } from "@/components/app-header";
import { apiGet, apiPost } from "@/lib/api/client";
import type { AppointmentRequest, CurrentUser, PatientAiSessionResponse, PatientDashboard, PatientSafeEntry, PatientScribeJob } from "@/lib/api/types";
import { createSupabaseBrowserClient } from "@/lib/supabase/browser";

type PortalData = { user: CurrentUser; dashboard: PatientDashboard; jobs: PatientScribeJob[]; token: string };

function displayDate(value: string) {
  return new Intl.DateTimeFormat("en-SG", { day: "numeric", month: "short", year: "numeric" }).format(new Date(value));
}

export default function PatientDashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<PortalData | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [appointmentDate, setAppointmentDate] = useState("");
  const [appointmentReason, setAppointmentReason] = useState<"follow_up" | "new_symptom" | "medication" | "other">("follow_up");
  const [symptom, setSymptom] = useState("");
  const [severity, setSeverity] = useState(5);
  const [symptomNotes, setSymptomNotes] = useState("");
  const [question, setQuestion] = useState("");

  useEffect(() => {
    let active = true;
    async function load() {
      const { data: session } = await createSupabaseBrowserClient().auth.getSession();
      const token = session.session?.access_token;
      if (!token) { router.replace("/sign-in"); return; }
      try {
        const user = await apiGet<CurrentUser>("/me", token);
        if (user.account_kind !== "patient") { router.replace("/patients"); return; }
        const [dashboard, jobs] = await Promise.all([
          apiGet<PatientDashboard>("/patient/dashboard", token),
          apiGet<PatientScribeJob[]>("/patient/ai-jobs", token),
        ]);
        if (active) setData({ user, dashboard, jobs, token });
      } catch { if (active) setError("Your patient dashboard is unavailable."); }
    }
    void load();
    return () => { active = false; };
  }, [router]);

  useEffect(() => {
    if (!data?.jobs.some((job) => job.status === "queued" || job.status === "processing")) return;
    let active = true;
    const timer = window.setInterval(() => {
      void apiGet<PatientScribeJob[]>("/patient/ai-jobs", data.token)
        .then((jobs) => { if (active) setData((current) => current ? { ...current, jobs } : current); })
        .catch(() => { if (active) setError("AI generation status could not be refreshed."); });
    }, 2000);
    return () => { active = false; window.clearInterval(timer); };
  }, [data?.jobs, data?.token]);

  async function bookAppointment(event: FormEvent) {
    event.preventDefault(); if (!data) return; setError(null); setMessage(null);
    try {
      const appointment = await apiPost<AppointmentRequest>("/patient/appointments", data.token, { preferred_date: appointmentDate, time_preference: "either", reason_category: appointmentReason, note: null });
      setData({ ...data, dashboard: { ...data.dashboard, appointments: [appointment, ...data.dashboard.appointments] } });
      setAppointmentDate(""); setMessage("Appointment request created.");
    } catch { setError("Appointment request could not be created."); }
  }

  async function logSymptom(event: FormEvent) {
    event.preventDefault(); if (!data) return; setError(null); setMessage(null);
    try {
      const result = await apiPost<{ entry: PatientSafeEntry; message: string }>("/patient/symptoms", data.token, { symptom, severity, started_at: new Date().toISOString(), notes: symptomNotes || null });
      setData({ ...data, dashboard: { ...data.dashboard, history: [result.entry, ...data.dashboard.history] } });
      setSymptom(""); setSymptomNotes(""); setMessage(result.message);
    } catch { setError("Symptom update could not be recorded."); }
  }

  async function askQuestion(event: FormEvent) {
    event.preventDefault(); if (!data) return; setError(null); setMessage(null);
    try {
      const result = await apiPost<PatientAiSessionResponse>("/patient/ai-question", data.token, { question, idempotency_key: `patient-session-${crypto.randomUUID()}` });
      setData({ ...data, jobs: [result.job, ...data.jobs], dashboard: { ...data.dashboard, history: [result.entry, ...data.dashboard.history] } });
      setQuestion(""); setMessage(result.message);
    } catch { setError("Your question could not be recorded."); }
  }

  if (!data) return <main className="state-page" aria-busy="true"><p>{error ?? "Loading your patient dashboard…"}</p></main>;
  const { dashboard } = data;
  return <div className="app-shell"><AppHeader user={data.user} /><main className="workspace portal-workspace"><header className="portal-hero"><div><p className="eyebrow">Synthetic patient account</p><h1>Hello, {data.user.preferred_name}</h1><p>{dashboard.synthetic_identifier} · Your released care information only</p></div><div className="privacy-boundary"><strong>Private by design</strong><span>Internal notes, comments, raw AI records, risk reasoning, and staff assignments are never available here.</span></div></header>{message ? <p className="form-success portal-message" role="status">{message}</p> : null}{error ? <p className="form-error portal-message" role="alert">{error}</p> : null}<section className="portal-section care-summary"><div className="section-heading"><div><p className="eyebrow">My Care Summary</p><h2>Approved for you</h2></div></div><div className="portal-cards">{[...dashboard.summaries, ...dashboard.instructions].map((entry) => <article className="portal-card" key={entry.id}><strong>{entry.entry_type === "patient_instruction" ? "Instruction" : "Care summary"}</strong><p>{entry.content}</p><time dateTime={entry.occurred_at}>{displayDate(entry.occurred_at)}</time></article>)}{!dashboard.summaries.length && !dashboard.instructions.length ? <p>No released care summaries yet.</p> : null}</div>{dashboard.visible_tasks.length ? <div className="patient-task-strip">{dashboard.visible_tasks.map((task) => <span key={task.id}><strong>{task.title}</strong>{task.due_at ? `Due ${displayDate(task.due_at)}` : "No due date"}</span>)}</div> : null}</section><div className="portal-grid"><section className="portal-module"><h2>Book Appointment</h2><p>Send a lightweight request; the clinic confirms separately.</p><form className="portal-form" onSubmit={bookAppointment}><label>Preferred date<input required type="date" min={new Date().toISOString().slice(0, 10)} value={appointmentDate} onChange={(event) => setAppointmentDate(event.target.value)} /></label><label>Reason<select value={appointmentReason} onChange={(event) => setAppointmentReason(event.target.value as typeof appointmentReason)}><option value="follow_up">Follow-up</option><option value="new_symptom">New symptom</option><option value="medication">Medication</option><option value="other">Other</option></select></label><button className="primary-button" type="submit">Request appointment</button></form><ul className="compact-list">{dashboard.appointments.map((item) => <li key={item.id}><strong>{displayDate(item.preferred_date)}</strong><span>{item.status.replaceAll("_", " ")}</span></li>)}</ul></section><section className="portal-module"><h2>Log Symptoms</h2><p>These patient-authored updates enter the longitudinal Care Note for your care team.</p><form className="portal-form" onSubmit={logSymptom}><label>Symptom<input required maxLength={120} value={symptom} onChange={(event) => setSymptom(event.target.value)} /></label><label>Severity: {severity}/10<input type="range" min="0" max="10" value={severity} onChange={(event) => setSeverity(Number(event.target.value))} /></label><label>Notes<textarea maxLength={1000} value={symptomNotes} onChange={(event) => setSymptomNotes(event.target.value)} /></label><button className="primary-button" type="submit">Save symptom update</button></form></section><section className="portal-module ai-prototype"><h2>Chat with AI</h2><p><strong>Non-emergency prototype.</strong> Your question triggers a redacted AI summary for your care team. It does not diagnose, triage, or replace medical advice, and the raw generated note is never shown here.</p><form className="portal-form" onSubmit={askQuestion}><label>Your question<textarea required maxLength={2000} value={question} onChange={(event) => setQuestion(event.target.value)} /></label><button className="primary-button" type="submit">Generate care-team summary</button></form>{data.jobs.length ? <div className="patient-generation-list" aria-label="AI generation status">{data.jobs.map((job) => <div key={job.id}><span className={`scribe-progress status-${job.status}`} aria-hidden="true" /><span><strong>{job.status.replaceAll("_", " ")}</strong><small>{job.status === "succeeded" ? "Summary delivered to your care team" : job.status === "failed" || job.status === "dead_letter" ? "Generation stopped safely" : "Processing securely"}</small></span></div>)}</div> : null}</section><section className="portal-module"><h2>Health Dashboard</h2><p>Patient-safe synthetic trends only.</p><div className="observation-grid">{dashboard.observations.map((item, index) => <article key={`${item.observation_type}-${item.observed_at}-${index}`}><strong>{item.value} {item.unit}</strong><span>{item.observation_type.replaceAll("_", " ")}</span><time dateTime={item.observed_at}>{displayDate(item.observed_at)}</time></article>)}</div></section><section className="portal-module"><h2>History</h2><p>Your submitted updates and questions.</p><ul className="history-list">{dashboard.history.map((entry) => <li key={entry.id}><span>{entry.content}</span><time dateTime={entry.occurred_at}>{displayDate(entry.occurred_at)}</time></li>)}</ul></section><section className="portal-module"><h2>Reports</h2><p>Only explicitly released reports appear here.</p>{dashboard.reports.length ? <ul className="history-list">{dashboard.reports.map((report) => <li key={report.id}><strong>{report.title}</strong><span>{report.patient_safe_summary}</span><small>{report.status} · {report.released_at ? displayDate(report.released_at) : "not released"}</small></li>)}</ul> : <p>No reports are currently released.</p>}</section></div></main></div>;
}
