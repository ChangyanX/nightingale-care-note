"use client";

import { useState } from "react";

import { ApiError, apiGet, apiPost } from "@/lib/api/client";
import type { Revision, RevisionComparison, TimelineEntry } from "@/lib/api/types";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-SG", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function readable(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (character) => character.toUpperCase());
}

type RevisionViewerProps = {
  accessToken: string;
  entry: TimelineEntry;
  canRevert: boolean;
};

export function RevisionViewer({ accessToken, entry, canRevert }: RevisionViewerProps) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [reverting, setReverting] = useState(false);
  const [loadingOlder, setLoadingOlder] = useState(false);
  const [revisions, setRevisions] = useState<Revision[]>([]);
  const [comparison, setComparison] = useState<RevisionComparison | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function toggleHistory() {
    if (open) {
      setOpen(false);
      return;
    }
    setOpen(true);
    if (revisions.length) return;
    setLoading(true);
    setError(null);
    try {
      const history = await apiGet<Revision[]>(`/entries/${entry.id}/versions`, accessToken);
      setRevisions(history);
    } catch {
      setError("Revision history could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  async function compare(versionNumber: number) {
    setLoading(true);
    setError(null);
    try {
      const result = await apiGet<RevisionComparison>(
        `/entries/${entry.id}/versions/${versionNumber}/comparison`,
        accessToken,
      );
      setComparison(result);
    } catch {
      setError("That revision is unavailable.");
    } finally {
      setLoading(false);
    }
  }

  async function loadOlder() {
    const oldest = revisions.at(-1);
    if (!oldest) return;
    setLoadingOlder(true);
    try {
      const older = await apiGet<Revision[]>(`/entries/${entry.id}/versions?before_version=${oldest.version_number}&limit=50`, accessToken);
      setRevisions((current) => [...current, ...older]);
    } catch { setError("Older revisions could not be loaded."); }
    finally { setLoadingOlder(false); }
  }

  async function revert() {
    if (!comparison || comparison.selected_version === comparison.current_version) return;
    const confirmed = window.confirm(
      `Restore version ${comparison.selected_version}? This creates a new version; no history will be deleted.`,
    );
    if (!confirmed) return;

    setReverting(true);
    setError(null);
    try {
      await apiPost<TimelineEntry>(`/entries/${entry.id}/revert`, accessToken, {
        source_version: comparison.selected_version,
        expected_version: comparison.current_version,
        change_reason: `Restored from version ${comparison.selected_version}`,
      });
      window.location.reload();
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 409) {
        setError("A newer edit was saved first. Your comparison is preserved; reload before retrying.");
      } else {
        setError("This revision could not be restored.");
      }
      setReverting(false);
    }
  }

  return (
    <div className="revision-viewer">
      <button
        aria-expanded={open}
        className="revision-toggle"
        type="button"
        onClick={toggleHistory}
      >
        {open ? "Close history" : "View history"}
      </button>
      {open ? (
        <section className="revision-panel" aria-label={`Revision history for ${entry.entry_type}`}>
          <p className="revision-note">Restoring creates a new version. Existing history is preserved.</p>
          {loading && !revisions.length ? <p aria-live="polite">Loading history…</p> : null}
          {error ? <p className="form-error" role="alert">{error}</p> : null}
          {revisions.length ? (
            <div className="revision-layout">
              <ol className="revision-list">
                {revisions.map((revision) => (
                  <li key={revision.version_number}>
                    <button
                      className={comparison?.selected_version === revision.version_number ? "selected" : ""}
                      type="button"
                      onClick={() => compare(revision.version_number)}
                    >
                      <strong>Version {revision.version_number}</strong>
                      <span>{readable(revision.changed_by_role)} · {formatDate(revision.created_at)}</span>
                      <small>{revision.change_reason ?? "No change reason recorded"}</small>
                    </button>
                  </li>
                ))}
                {revisions.length >= 50 ? <li><button type="button" disabled={loadingOlder} onClick={loadOlder}>{loadingOlder ? "Loading…" : "Load older versions"}</button></li> : null}
              </ol>
              {comparison ? (
                <div className="revision-comparison">
                  <div>
                    <h4>Version {comparison.selected_version}</h4>
                    <p>{comparison.selected_content}</p>
                  </div>
                  <div>
                    <h4>Current · version {comparison.current_version}</h4>
                    <p>{comparison.current_content}</p>
                  </div>
                  {comparison.word_diff.length ? <div><h4>Word-level changes</h4><p>{comparison.word_diff.map((part, index) => <span className={`word-${part.kind}`} key={`${part.kind}-${index}`}>{part.text}</span>)}</p></div> : null}
                  {!comparison.has_changes ? <p className="revision-note">The selected text matches the current text.</p> : null}
                  {canRevert && comparison.selected_version !== comparison.current_version ? (
                    <button
                      className="primary-button"
                      disabled={reverting}
                      type="button"
                      onClick={revert}
                    >
                      {reverting ? "Restoring…" : `Restore version ${comparison.selected_version}`}
                    </button>
                  ) : null}
                </div>
              ) : <p className="revision-note">Choose a version to compare it with the current entry.</p>}
            </div>
          ) : !loading ? <p className="revision-note">No authorized history is available.</p> : null}
        </section>
      ) : null}
    </div>
  );
}
