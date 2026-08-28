"use client";

import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { AppHeader } from "@/components/app-header";
import { CollaborationPanel } from "@/components/collaboration-panel";
import { HighlightReviewPanel } from "@/components/highlight-review-panel";
import { RevisionViewer } from "@/components/revision-viewer";
import { ScribeJobStatus } from "@/components/scribe-job-status";
import { ApiError, apiGet, apiPatch, apiPost } from "@/lib/api/client";
import type { CareTask, Comment, CurrentUser, Glance, Highlight, ImportancePreference, Patient, ProviderUsage, ScribeJob, ScribeJobEvent, TimelineEntry } from "@/lib/api/types";
import { createSupabaseBrowserClient } from "@/lib/supabase/browser";

type PatientPageData = { user: CurrentUser; patient: Patient; glance: Glance; timeline: TimelineEntry[]; tasks: CareTask[]; highlights: Highlight[]; comments: Comment[]; jobs: ScribeJob[]; jobEvents: ScribeJobEvent[]; providerUsage: ProviderUsage[]; preferences: ImportancePreference[]; accessToken: string };

const KIND_LABELS = {
  current_concern: "Current concern",
  recent_change: "Recent change",
  open_action: "Open action",
  patient_question: "Patient question",
};

function readable(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatDate(value: string, withTime = false) {
  return new Intl.DateTimeFormat("en-SG", {
    day: "numeric", month: "short", year: "numeric",
    ...(withTime ? { hour: "2-digit", minute: "2-digit" } : {}),
  }).format(new Date(value));
}

export default function PatientPage() {
  const { patientId } = useParams<{ patientId: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [data, setData] = useState<PatientPageData | null>(null);
  const [error, setError] = useState<{ title: string; message: string } | null>(null);
  const [reloadVersion, setReloadVersion] = useState(0);
  const [liveStatus, setLiveStatus] = useState<"connecting" | "connected" | "disconnected">("connecting");
  const [activityToast, setActivityToast] = useState<string | null>(null);
  const [roleFilter, setRoleFilter] = useState(searchParams.get("role") ?? "");
  const [typeFilter, setTypeFilter] = useState(searchParams.get("type") ?? "");
  const [dateFilter, setDateFilter] = useState(searchParams.get("date") ?? "");

  useEffect(() => {
    let active = true;
    async function load() {
      const { data: sessionData } = await createSupabaseBrowserClient().auth.getSession();
      const token = sessionData.session?.access_token;
      if (!token) { router.replace("/sign-in"); return; }
      try {
        const user = await apiGet<CurrentUser>("/me", token);
        if (user.account_kind === "patient") { router.replace("/patient"); return; }
        const clinicId = user.memberships[0]?.clinic_id;
        const [patient, glance, timeline, tasks, highlights, comments, jobs, jobEvents, providerUsage, preferences] = await Promise.all([
          apiGet<Patient>(`/patients/${patientId}`, token),
          apiGet<Glance>(`/patients/${patientId}/glance`, token),
          apiGet<TimelineEntry[]>(`/patients/${patientId}/timeline`, token),
          apiGet<CareTask[]>(`/patients/${patientId}/tasks`, token),
          apiGet<Highlight[]>(`/patients/${patientId}/highlights`, token),
          apiGet<Comment[]>(`/patients/${patientId}/comments`, token),
          apiGet<ScribeJob[]>(`/patients/${patientId}/scribe-jobs`, token),
          apiGet<ScribeJobEvent[]>(`/patients/${patientId}/scribe-job-events`, token),
          apiGet<ProviderUsage[]>("/provider-usage", token),
          clinicId ? apiGet<ImportancePreference[]>(`/importance-preferences?clinic_id=${clinicId}`, token) : Promise.resolve([]),
        ]);
        if (active) setData({ user, patient, glance, timeline, tasks, highlights, comments, jobs, jobEvents, providerUsage, preferences, accessToken: token });
      } catch (requestError) {
        if (!active) return;
        if (requestError instanceof ApiError && requestError.status === 401) { router.replace("/sign-in"); return; }
        if (requestError instanceof ApiError && requestError.status === 404) {
          setError({ title: "Patient unavailable", message: "This record does not exist or is outside your clinic access." }); return;
        }
        setError({ title: "Care Note unavailable", message: "The patient story could not be loaded. Please retry." });
      }
    }
    void load();
    return () => { active = false; };
  }, [patientId, reloadVersion, router]);

  useEffect(() => {
    if (!data?.accessToken) return;
    const supabase = createSupabaseBrowserClient();
    const refresh = (resource: string) => {
      setActivityToast(`${resource} changed by an authorized collaborator.`);
      setReloadVersion((value) => value + 1);
      window.setTimeout(() => setActivityToast(null), 4000);
    };
    const channel = supabase.channel(`patient-${patientId}`);
    for (const table of ["entries", "care_tasks", "comments", "comment_reactions", "highlights", "ai_jobs"] as const) {
      channel.on("postgres_changes", { event: "*", schema: "public", table, filter: `patient_id=eq.${patientId}` }, () => refresh(readable(table)));
    }
    channel.subscribe((status) => setLiveStatus(status === "SUBSCRIBED" ? "connected" : status === "CHANNEL_ERROR" || status === "TIMED_OUT" ? "disconnected" : "connecting"));
    return () => { void supabase.removeChannel(channel); };
  }, [data?.accessToken, patientId]);

  const filteredTimeline = useMemo(() => (data?.timeline ?? []).filter((entry) => {
    if (roleFilter && entry.author_role !== roleFilter) return false;
    if (typeFilter && entry.entry_type !== typeFilter) return false;
    if (dateFilter && entry.occurred_at.slice(0, 10) !== dateFilter) return false;
    return true;
  }), [data?.timeline, roleFilter, typeFilter, dateFilter]);

  function updateFilter(name: "role" | "type" | "date", value: string) {
    if (name === "role") setRoleFilter(value);
    if (name === "type") setTypeFilter(value);
    if (name === "date") setDateFilter(value);
    const next = new URLSearchParams(searchParams.toString());
    if (value) next.set(name, value); else next.delete(name);
    router.replace(`?${next.toString()}`, { scroll: false });
  }

  function contentWithHighlight(entry: TimelineEntry) {
    const highlight = data?.highlights.find((item) => item.source_entry_id === entry.id && item.status !== "rejected");
    if (!highlight || entry.content.slice(highlight.source_start_offset, highlight.source_end_offset) !== highlight.quoted_text) return entry.content;
    return <>{entry.content.slice(0, highlight.source_start_offset)}<mark>{entry.content.slice(highlight.source_start_offset, highlight.source_end_offset)}</mark>{entry.content.slice(highlight.source_end_offset)}</>;
  }

  async function updateTask(taskId: string, patch: Partial<CareTask>) {
    if (!data) return;
    const previous = data.tasks;
    setData({ ...data, tasks: data.tasks.map((task) => task.id === taskId ? { ...task, ...patch } : task) });
    try { await apiPatch<CareTask>(`/tasks/${taskId}`, data.accessToken, patch); }
    catch { setData((current) => current ? { ...current, tasks: previous } : current); setActivityToast("Task update failed and was restored."); }
  }

  async function recordPreference(topic: string, feedbackKind: "accept" | "reject") {
    if (!data) return;
    const clinicId = data.user.memberships[0]?.clinic_id;
    if (!clinicId) return;
    try {
      const preference = await apiPost<ImportancePreference>("/importance-feedback", data.accessToken, {
        event_id: crypto.randomUUID(), clinic_id: clinicId, topic, feedback_kind: feedbackKind,
      });
      setData((current) => current ? { ...current, preferences: [preference, ...current.preferences.filter((item) => item.id !== preference.id)] } : current);
      setActivityToast(`Your ${topic.replaceAll("_", " ")} preference was saved.`);
    } catch { setActivityToast("Preference feedback could not be saved."); }
  }

  if (error) return <main className="state-page"><h1>{error.title}</h1><p>{error.message}</p><Link href="/patients">Return to patients</Link></main>;
  if (!data) return <main className="state-page skeleton-page" aria-busy="true"><span className="skeleton-line wide" /><span className="skeleton-card" /><p>Assembling the Care Note…</p></main>;

  const openTasks = data.tasks.filter((task) => task.status === "open" || task.status === "in_progress");
  const primaryRole = data.user.memberships[0]?.role;
  const canWrite = primaryRole === "staff" || primaryRole === "clinician";
  const canReview = primaryRole === "clinician";

  return (
    <div className="app-shell">
      <AppHeader user={data.user} />
      <main className="workspace patient-workspace">
        <Link className="back-link" href="/patients">← All patients</Link>
        <header className="patient-header">
          <div><p className="eyebrow">Longitudinal Care Note</p><h1>{data.patient.display_name}</h1><p>{data.patient.synthetic_identifier} · Synthetic record</p></div>
          <div className={`record-state live-${liveStatus}`}><span className="status-dot" />{liveStatus === "connected" ? "Live updates connected" : liveStatus === "connecting" ? "Connecting live updates" : "Live updates offline"}<small>{liveStatus === "disconnected" ? "Manual refresh remains available" : "Updated from authorized sources"}</small><button className="text-button" type="button" onClick={() => setReloadVersion((value) => value + 1)}>Refresh</button></div>
        </header>
        {activityToast ? <div className="activity-toast" role="status">{activityToast}</div> : null}

        <section className="glance-section" aria-labelledby="glance-title">
          <div className="section-heading"><div><p className="eyebrow">Ten-second orientation</p><h2 id="glance-title">What matters now</h2></div><span>{data.glance.items.length} source-linked items</span></div>
          {data.glance.items.length ? <div className="glance-grid">{data.glance.items.map((item) => (
            <article className={`glance-card glance-${item.kind}`} key={`${item.kind}-${item.source_entry_id}`}>
              <div className="glance-meta"><span>{KIND_LABELS[item.kind]}</span><span>{readable(item.status)}</span></div>
              <h3>{item.claim}</h3><p>{item.importance_reason}</p>
              {canWrite ? <div className="preference-actions" aria-label={`Personal relevance feedback for ${item.claim}`}><button type="button" onClick={() => void recordPreference(item.kind, "accept")}>More relevant</button><button type="button" onClick={() => void recordPreference(item.kind, "reject")}>Less relevant</button><small>{data.preferences.find((preference) => preference.topic === item.kind)?.weight ? `Personal weight ${data.preferences.find((preference) => preference.topic === item.kind)?.weight}` : "Personal, bounded feedback"}</small></div> : null}
              <a href={`#entry-${item.source_entry_id}`}>View source · {formatDate(item.occurred_at)}</a>
            </article>
          ))}</div> : <div className="empty-state"><h3>No Glance items yet</h3><p>The timeline is available, but no bounded priority items were selected.</p></div>}
        </section>

        <ScribeJobStatus jobs={data.jobs} events={data.jobEvents} usage={data.providerUsage} />

        <HighlightReviewPanel accessToken={data.accessToken} highlights={data.highlights} canReview={canReview} onReviewed={(ids, status) => setData({ ...data, highlights: data.highlights.map((item) => ids.includes(item.id) ? { ...item, status } : item) })} />

        <div className="patient-columns">
          <section className="timeline-section" aria-labelledby="timeline-title">
            <div className="section-heading"><div><p className="eyebrow">Across visits and voices</p><h2 id="timeline-title">Timeline</h2></div><span>{filteredTimeline.length} entries</span></div>
            <div className="timeline-filters" aria-label="Timeline filters">
              <label>Role<select value={roleFilter} onChange={(event) => updateFilter("role", event.target.value)}><option value="">All roles</option><option value="patient">Patient</option><option value="staff">Staff</option><option value="clinician">Clinician</option><option value="system">AI</option></select></label>
              <label>Type<select value={typeFilter} onChange={(event) => updateFilter("type", event.target.value)}><option value="">All types</option>{Array.from(new Set(data.timeline.map((entry) => entry.entry_type))).map((type) => <option value={type} key={type}>{readable(type)}</option>)}</select></label>
              <label>Date<input type="date" value={dateFilter} onChange={(event) => updateFilter("date", event.target.value)} /></label>
              {(roleFilter || typeFilter || dateFilter) ? <button type="button" onClick={() => { setRoleFilter(""); setTypeFilter(""); setDateFilter(""); router.replace("?", { scroll: false }); }}>Clear</button> : null}
            </div>
            {filteredTimeline.length ? <div className="timeline-list">{filteredTimeline.map((entry, index) => {
              const date = formatDate(entry.occurred_at);
              const previousDate = index > 0 ? formatDate(filteredTimeline[index - 1].occurred_at) : null;
              const showDate = date !== previousDate;
              const isAi = entry.author_role === "system";
              return <div key={entry.id}>{showDate ? <h3 className="timeline-date">{date}</h3> : null}<article className={`timeline-entry role-${entry.author_role}`} id={`entry-${entry.id}`} tabIndex={-1}>
                <div className="entry-rail"><span /></div><div className="entry-body">
                  <div className="entry-meta"><span className="role-label">{isAi ? "AI generated" : readable(entry.author_role)}</span><span>{readable(entry.entry_type)}</span><time dateTime={entry.occurred_at}>{formatDate(entry.occurred_at, true)}</time></div>
                  <p>{contentWithHighlight(entry)}</p><footer><span>Source: {entry.source ? readable(entry.source.source_type) : "Unavailable"}</span>{entry.source?.external_reference ? <span>{entry.source.external_reference}</span> : null}<span>Version {entry.current_version}</span></footer>
                  {data.user.memberships.length ? <RevisionViewer accessToken={data.accessToken} entry={entry} canRevert={entry.author_id === data.user.id && (entry.author_role === "staff" || entry.author_role === "clinician")} /> : null}
                </div>
              </article></div>;
            })}</div> : <div className="empty-state"><h3>No timeline entries</h3><p>Permitted manual and AI-scribed entries will appear here.</p></div>}
          </section>

          <aside className="task-panel" aria-labelledby="task-title">
            <div className="section-heading compact"><div><p className="eyebrow">Follow-through</p><h2 id="task-title">Open actions</h2></div><span>{openTasks.length}</span></div>
            {openTasks.length ? <div className="task-list">{openTasks.map((task) => (
              <article className="task-card" key={task.id}><div><span className={`priority priority-${task.priority}`}>{task.priority}</span><span>{readable(task.status)}</span></div>
                <h3>{task.title}</h3><p>{readable(task.category ?? "follow_up")}</p>{canWrite ? <div className="task-controls"><label>Due<input type="date" value={task.due_at?.slice(0, 10) ?? ""} onChange={(event) => updateTask(task.id, { due_at: event.target.value ? `${event.target.value}T17:00:00+08:00` : null })} /></label><label>Status<select value={task.status} onChange={(event) => updateTask(task.id, { status: event.target.value as CareTask["status"] })}><option value="open">Open</option><option value="in_progress">In progress</option><option value="completed">Completed</option><option value="cancelled">Cancelled</option></select></label><label>Assignment<select value={task.assigned_to ?? ""} onChange={(event) => updateTask(task.id, { assigned_to: event.target.value || null })}><option value="">Unassigned</option><option value={data.user.id}>Assign to me</option></select></label></div> : <p>{task.due_at ? `Due ${formatDate(task.due_at)}` : "No due date"}</p>}{task.source_entry_id ? <a href={`#entry-${task.source_entry_id}`}>View source</a> : null}
              </article>
            ))}</div> : <div className="empty-state small"><h3>No open actions</h3><p>Completed work remains in the task history.</p></div>}
          </aside>
        </div>
        <CollaborationPanel
          accessToken={data.accessToken}
          currentUserId={data.user.id}
          entries={data.timeline}
          comments={data.comments}
          canWrite={canWrite}
          onCreated={(comment) => setData((current) => current ? { ...current, comments: [...current.comments, comment] } : current)}
          onUpdated={(comment) => setData((current) => current ? { ...current, comments: current.comments.map((item) => item.id === comment.id ? comment : item) } : current)}
          onDeleted={(commentId) => setData((current) => current ? { ...current, comments: current.comments.filter((item) => item.id !== commentId) } : current)}
        />
      </main>
    </div>
  );
}
