"use client";

import { FormEvent, useState } from "react";

import { apiPost } from "@/lib/api/client";
import type { Comment, TimelineEntry } from "@/lib/api/types";

export function CollaborationPanel({
  accessToken,
  currentUserId,
  entries,
  comments,
  canWrite,
  onCreated,
}: {
  accessToken: string;
  currentUserId: string;
  entries: TimelineEntry[];
  comments: Comment[];
  canWrite: boolean;
  onCreated: (comment: Comment) => void;
}) {
  const [entryId, setEntryId] = useState(entries[0]?.id ?? "");
  const [body, setBody] = useState("");
  const [format, setFormat] = useState<"plain" | "markdown">("plain");
  const [assignSelf, setAssignSelf] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!entryId || !body.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const created = await apiPost<Comment>(`/patients/${entries[0]?.patient_id}/comments`, accessToken, {
        entry_id: entryId,
        body,
        body_format: format,
        mention_ids: [],
        assignee_ids: assignSelf ? [currentUserId] : [],
      });
      onCreated(created);
      setBody("");
    } catch {
      setError("The comment could not be saved.");
    } finally {
      setBusy(false);
    }
  }

  async function react(commentId: string, reaction: "acknowledged" | "agree" | "question") {
    try { await apiPost(`/comments/${commentId}/reactions`, accessToken, { reaction }); }
    catch { setError("The reaction could not be saved."); }
  }

  return (
    <section className="collaboration-panel" aria-labelledby="collaboration-title">
      <div className="section-heading compact"><div><p className="eyebrow">Team context</p><h2 id="collaboration-title">Comments</h2></div><span>{comments.length}</span></div>
      <div className="comment-list">{comments.map((comment) => <article className="comment-card" key={comment.id}>
        <div><strong>{comment.author_id === currentUserId ? "You" : "Collaborator"}</strong><span>{comment.status}</span></div>
        <p>{comment.body}</p>
        {comment.quoted_text ? <blockquote>“{comment.quoted_text}”</blockquote> : null}
        <div className="reaction-actions"><button type="button" onClick={() => react(comment.id, "acknowledged")}>Acknowledge</button><button type="button" onClick={() => react(comment.id, "agree")}>Agree</button><button type="button" onClick={() => react(comment.id, "question")}>Question</button></div>
      </article>)}</div>
      {canWrite ? <form className="comment-form" onSubmit={submit}>
        <label>Comment target<select value={entryId} onChange={(event) => setEntryId(event.target.value)}>{entries.map((entry) => <option value={entry.id} key={entry.id}>{entry.entry_type.replaceAll("_", " ")} · {entry.id.slice(0, 8)}</option>)}</select></label>
        <label>Format<select value={format} onChange={(event) => setFormat(event.target.value as "plain" | "markdown")}><option value="plain">Plain text</option><option value="markdown">Markdown</option></select></label>
        <label>Comment<textarea required maxLength={5000} value={body} onChange={(event) => setBody(event.target.value)} /></label>
        <label className="checkbox-label"><input type="checkbox" checked={assignSelf} onChange={(event) => setAssignSelf(event.target.checked)} /> Assign this thread to me</label>
        {error ? <p className="form-error" role="alert">{error}</p> : null}
        <button className="primary-button" disabled={busy} type="submit">{busy ? "Saving…" : "Add comment"}</button>
      </form> : <p className="revision-note">Read-only oversight: comment controls are unavailable.</p>}
    </section>
  );
}
