"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppHeader } from "@/components/app-header";
import { RevisionViewer } from "@/components/revision-viewer";
import { ApiError, apiGet } from "@/lib/api/client";
import type { CareTask, CurrentUser, Glance, Patient, TimelineEntry } from "@/lib/api/types";
import { createSupabaseBrowserClient } from "@/lib/supabase/browser";

type PatientPageData = { user: CurrentUser; patient: Patient; glance: Glance; timeline: TimelineEntry[]; tasks: CareTask[]; accessToken: string };

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
  const [data, setData] = useState<PatientPageData | null>(null);
  const [error, setError] = useState<{ title: string; message: string } | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      const { data: sessionData } = await createSupabaseBrowserClient().auth.getSession();
      const token = sessionData.session?.access_token;
      if (!token) { router.replace("/sign-in"); return; }
      try {
        const [user, patient, glance, timeline, tasks] = await Promise.all([
          apiGet<CurrentUser>("/me", token), apiGet<Patient>(`/patients/${patientId}`, token),
          apiGet<Glance>(`/patients/${patientId}/glance`, token),
          apiGet<TimelineEntry[]>(`/patients/${patientId}/timeline`, token),
          apiGet<CareTask[]>(`/patients/${patientId}/tasks`, token),
        ]);
        if (active) setData({ user, patient, glance, timeline, tasks, accessToken: token });
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
  }, [patientId, router]);

  if (error) return <main className="state-page"><h1>{error.title}</h1><p>{error.message}</p><Link href="/patients">Return to patients</Link></main>;
  if (!data) return <main className="state-page" aria-busy="true"><p>Assembling the Care Note…</p></main>;

  const openTasks = data.tasks.filter((task) => task.status === "open" || task.status === "in_progress");

  return (
    <div className="app-shell">
      <AppHeader user={data.user} />
      <main className="workspace patient-workspace">
        <Link className="back-link" href="/patients">← All patients</Link>
        <header className="patient-header">
          <div><p className="eyebrow">Longitudinal Care Note</p><h1>{data.patient.display_name}</h1><p>{data.patient.synthetic_identifier} · Synthetic record</p></div>
          <div className="record-state"><span className="status-dot" />Shared record active<small>Updated from authorized sources</small></div>
        </header>

        <section className="glance-section" aria-labelledby="glance-title">
          <div className="section-heading"><div><p className="eyebrow">Ten-second orientation</p><h2 id="glance-title">What matters now</h2></div><span>{data.glance.items.length} source-linked items</span></div>
          {data.glance.items.length ? <div className="glance-grid">{data.glance.items.map((item) => (
            <article className={`glance-card glance-${item.kind}`} key={`${item.kind}-${item.source_entry_id}`}>
              <div className="glance-meta"><span>{KIND_LABELS[item.kind]}</span><span>{readable(item.status)}</span></div>
              <h3>{item.claim}</h3><p>{item.importance_reason}</p>
              <a href={`#entry-${item.source_entry_id}`}>View source · {formatDate(item.occurred_at)}</a>
            </article>
          ))}</div> : <div className="empty-state"><h3>No Glance items yet</h3><p>The timeline is available, but no bounded priority items were selected.</p></div>}
        </section>

        <div className="patient-columns">
          <section className="timeline-section" aria-labelledby="timeline-title">
            <div className="section-heading"><div><p className="eyebrow">Across visits and voices</p><h2 id="timeline-title">Timeline</h2></div><span>{data.timeline.length} entries</span></div>
            {data.timeline.length ? <div className="timeline-list">{data.timeline.map((entry, index) => {
              const date = formatDate(entry.occurred_at);
              const previousDate = index > 0 ? formatDate(data.timeline[index - 1].occurred_at) : null;
              const showDate = date !== previousDate;
              const isAi = entry.author_role === "system";
              return <div key={entry.id}>{showDate ? <h3 className="timeline-date">{date}</h3> : null}<article className={`timeline-entry role-${entry.author_role}`} id={`entry-${entry.id}`} tabIndex={-1}>
                <div className="entry-rail"><span /></div><div className="entry-body">
                  <div className="entry-meta"><span className="role-label">{isAi ? "AI generated" : readable(entry.author_role)}</span><span>{readable(entry.entry_type)}</span><time dateTime={entry.occurred_at}>{formatDate(entry.occurred_at, true)}</time></div>
                  <p>{entry.content}</p><footer><span>Source: {entry.source ? readable(entry.source.source_type) : "Unavailable"}</span>{entry.source?.external_reference ? <span>{entry.source.external_reference}</span> : null}<span>Version {entry.current_version}</span></footer>
                  {data.user.memberships.length ? <RevisionViewer accessToken={data.accessToken} entry={entry} canRevert={entry.author_id === data.user.id && (entry.author_role === "staff" || entry.author_role === "clinician")} /> : null}
                </div>
              </article></div>;
            })}</div> : <div className="empty-state"><h3>No timeline entries</h3><p>Permitted manual and AI-scribed entries will appear here.</p></div>}
          </section>

          <aside className="task-panel" aria-labelledby="task-title">
            <div className="section-heading compact"><div><p className="eyebrow">Follow-through</p><h2 id="task-title">Open actions</h2></div><span>{openTasks.length}</span></div>
            {openTasks.length ? <div className="task-list">{openTasks.map((task) => (
              <article className="task-card" key={task.id}><div><span className={`priority priority-${task.priority}`}>{task.priority}</span><span>{readable(task.status)}</span></div>
                <h3>{task.title}</h3><p>{task.due_at ? `Due ${formatDate(task.due_at)}` : "No due date"}</p>{task.source_entry_id ? <a href={`#entry-${task.source_entry_id}`}>View source</a> : null}
              </article>
            ))}</div> : <div className="empty-state small"><h3>No open actions</h3><p>Completed work remains in the task history.</p></div>}
          </aside>
        </div>
      </main>
    </div>
  );
}
