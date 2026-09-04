"use client";

import type { ProviderUsage, ScribeJob, ScribeJobEvent } from "@/lib/api/types";

export function ScribeJobStatus({ jobs, events, usage }: { jobs: ScribeJob[]; events: ScribeJobEvent[]; usage: ProviderUsage[] }) {
  if (!jobs.length && !usage.length) return null;
  const hasActiveJobs = jobs.some((job) => job.status === "queued" || job.status === "processing");
  return <section className="scribe-status" aria-labelledby="scribe-status-title">
    <div><p className="eyebrow">AI scribe activity</p><h2 id="scribe-status-title">Generation status</h2>{hasActiveJobs ? <small className="scribe-monitor">Monitoring active jobs every two seconds</small> : null}</div>
    <div className="scribe-job-list">{jobs.map((job) => <article className={`scribe-job status-${job.status}`} key={job.id}>
      <span className="scribe-progress" aria-hidden="true" />
      <div><strong>{job.interaction_type.replaceAll("_", " ")}</strong><small>{job.status.replaceAll("_", " ")}{job.queue_position ? ` · queue ${job.queue_position}` : ""}{job.model_name ? ` · ${job.model_name}` : ""}</small>{job.safe_error_code ? <small className="scribe-error">Stopped safely · {job.safe_error_code.replaceAll("_", " ")}</small> : null}<ol className="scribe-stages" aria-label="Generation stages">{events.filter((event) => event.job_id === job.id).map((event) => <li key={event.id}>{event.event_kind.replaceAll("_", " ")}</li>)}</ol></div>
      {job.output_entry_id ? <a href={`#entry-${job.output_entry_id}`}>View generated entry</a> : null}
    </article>)}</div>
    {usage.length ? <div className="provider-usage"><h3>Provider usage</h3><div className="usage-table" role="table" aria-label="Provider token, latency, and cost totals">{usage.map((row) => <div className="usage-row" role="row" key={`${row.provider}-${row.model}`}><strong>{row.provider} · {row.model}</strong><span>{row.calls} calls</span><span>{row.input_tokens + row.output_tokens} tokens</span><span>{Math.round(row.average_latency_ms)} ms avg</span><span>US${row.estimated_cost_usd.toFixed(4)}</span></div>)}</div></div> : null}
  </section>;
}
