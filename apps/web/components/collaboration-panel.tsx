"use client";

import { FormEvent, useState } from "react";

import { apiDelete, apiPost } from "@/lib/api/client";
import type { Comment, TimelineEntry } from "@/lib/api/types";

type Reaction = "acknowledged" | "agree" | "question";

const REACTION_LABELS: Record<Reaction, string> = {
  acknowledged: "Acknowledge",
  agree: "Agree",
  question: "Question",
};

export function CollaborationPanel({
  accessToken,
  currentUserId,
  entries,
  comments,
  canWrite,
  onCreated,
  onUpdated,
  onDeleted,
}: {
  accessToken: string;
  currentUserId: string;
  entries: TimelineEntry[];
  comments: Comment[];
  canWrite: boolean;
  onCreated: (comment: Comment) => void;
  onUpdated: (comment: Comment) => void;
  onDeleted: (commentId: string) => void;
}) {
  const [entryId, setEntryId] = useState(entries[0]?.id ?? "");
  const [body, setBody] = useState("");
  const [format, setFormat] = useState<"plain" | "markdown">("plain");
  const [assignSelf, setAssignSelf] = useState(false);
  const [busy, setBusy] = useState(false);
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!entryId || !body.trim()) return;
    setBusy(true);
    setError(null);
    setMessage(null);
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
      setMessage("Comment added.");
    } catch {
      setError("The comment could not be saved.");
    } finally {
      setBusy(false);
    }
  }

  async function react(comment: Comment, reaction: Reaction) {
    const selected = comment.my_reactions.includes(reaction);
    const actionKey = `${comment.id}:${reaction}`;
    setPendingAction(actionKey);
    setError(null);
    setMessage(null);
    try {
      if (selected) {
        await apiDelete(`/comments/${comment.id}/reactions/${reaction}`, accessToken);
      } else {
        await apiPost(`/comments/${comment.id}/reactions`, accessToken, { reaction });
      }
      onUpdated({
        ...comment,
        reaction_counts: {
          ...comment.reaction_counts,
          [reaction]: Math.max(0, comment.reaction_counts[reaction] + (selected ? -1 : 1)),
        },
        my_reactions: selected
          ? comment.my_reactions.filter((item) => item !== reaction)
          : [...comment.my_reactions, reaction],
      });
      setMessage(`${REACTION_LABELS[reaction]} ${selected ? "removed" : "recorded"}.`);
    } catch {
      setError("The reaction could not be saved.");
    } finally {
      setPendingAction(null);
    }
  }

  async function deleteComment(commentId: string) {
    setPendingAction(`${commentId}:delete`);
    setError(null);
    setMessage(null);
    try {
      await apiDelete(`/comments/${commentId}`, accessToken);
      onDeleted(commentId);
      setDeleteConfirmId(null);
      setMessage("Comment deleted.");
    } catch {
      setError("The comment could not be deleted. Only its author may delete it.");
    } finally {
      setPendingAction(null);
    }
  }

  return (
    <section className="collaboration-panel" aria-labelledby="collaboration-title">
      <div className="section-heading compact"><div><p className="eyebrow">Team context</p><h2 id="collaboration-title">Comments</h2></div><span>{comments.length}</span></div>
      {message ? <p className="form-success collaboration-message" role="status">{message}</p> : null}
      {error ? <p className="form-error collaboration-message" role="alert">{error}</p> : null}
      <div className="comment-list">{comments.map((comment) => <article className="comment-card" key={comment.id}>
        <div><strong>{comment.author_id === currentUserId ? "You" : "Collaborator"}</strong><span>{comment.status}</span></div>
        <p>{comment.body}</p>
        {comment.quoted_text ? <blockquote>“{comment.quoted_text}”</blockquote> : null}
        {canWrite ? <div className="reaction-actions">{(Object.keys(REACTION_LABELS) as Reaction[]).map((reaction) => {
          const selected = comment.my_reactions.includes(reaction);
          return <button
            aria-pressed={selected}
            className={selected ? "selected" : undefined}
            disabled={pendingAction === `${comment.id}:${reaction}`}
            key={reaction}
            type="button"
            onClick={() => void react(comment, reaction)}
          >{REACTION_LABELS[reaction]} <span aria-label={`${comment.reaction_counts[reaction]} reactions`}>{comment.reaction_counts[reaction]}</span></button>;
        })}</div> : null}
        {canWrite && comment.author_id === currentUserId ? <div className="comment-delete-actions">
          {deleteConfirmId === comment.id ? <>
            <span>Delete this comment?</span>
            <button className="danger-button" disabled={pendingAction === `${comment.id}:delete`} type="button" onClick={() => void deleteComment(comment.id)}>{pendingAction === `${comment.id}:delete` ? "Deleting…" : "Confirm delete"}</button>
            <button type="button" onClick={() => setDeleteConfirmId(null)}>Cancel</button>
          </> : <button className="text-button danger-text" type="button" onClick={() => setDeleteConfirmId(comment.id)}>Delete comment</button>}
        </div> : null}
      </article>)}</div>
      {canWrite ? <form className="comment-form" onSubmit={submit}>
        <label>Comment target<select value={entryId} onChange={(event) => setEntryId(event.target.value)}>{entries.map((entry) => <option value={entry.id} key={entry.id}>{entry.entry_type.replaceAll("_", " ")} · {entry.id.slice(0, 8)}</option>)}</select></label>
        <label>Format<select value={format} onChange={(event) => setFormat(event.target.value as "plain" | "markdown")}><option value="plain">Plain text</option><option value="markdown">Markdown</option></select></label>
        <label>Comment<textarea required maxLength={5000} value={body} onChange={(event) => setBody(event.target.value)} /></label>
        <label className="checkbox-label"><input type="checkbox" checked={assignSelf} onChange={(event) => setAssignSelf(event.target.checked)} /> Assign this thread to me</label>
        <button className="primary-button" disabled={busy} type="submit">{busy ? "Saving…" : "Add comment"}</button>
      </form> : <p className="revision-note">Read-only oversight: comment controls are unavailable.</p>}
    </section>
  );
}
