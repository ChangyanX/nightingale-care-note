"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { apiPost } from "@/lib/api/client";
import type { Highlight } from "@/lib/api/types";

export function HighlightReviewPanel({
  accessToken,
  highlights,
  canReview,
  onReviewed,
}: {
  accessToken: string;
  highlights: Highlight[];
  canReview: boolean;
  onReviewed: (ids: string[], status: "accepted" | "rejected") => void;
}) {
  const pending = useMemo(
    () => highlights.filter((item) => item.status === "suggested"),
    [highlights],
  );
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const groups = useMemo(() => {
    const counts = new Map<string, number>();
    for (const item of highlights) {
      const key = item.normalized_claim.trim().toLocaleLowerCase();
      counts.set(key, (counts.get(key) ?? 0) + 1);
    }
    return counts;
  }, [highlights]);

  const review = useCallback(async (ids: string[], status: "accepted" | "rejected") => {
    if (!ids.length || !canReview) return;
    setBusy(true);
    setError(null);
    onReviewed(ids, status);
    try {
      await apiPost<Highlight[]>("/highlights/bulk-review", accessToken, {
        highlight_ids: ids,
        status,
      });
    } catch {
      setError("The review could not be saved. Refresh to restore server state.");
    } finally {
      setBusy(false);
    }
  }, [accessToken, canReview, onReviewed]);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (!canReview || !pending.length || event.metaKey || event.ctrlKey || event.altKey) return;
      const target = event.target as HTMLElement | null;
      if (target?.matches("input, textarea, select")) return;
      const current = pending[selectedIndex];
      if (!current) return;
      if (event.key.toLocaleLowerCase() === "a") void review([current.id], "accepted");
      if (event.key.toLocaleLowerCase() === "r") void review([current.id], "rejected");
      if (event.key === "ArrowDown") setSelectedIndex((value) => Math.min(pending.length - 1, value + 1));
      if (event.key === "ArrowUp") setSelectedIndex((value) => Math.max(0, value - 1));
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [canReview, pending, review, selectedIndex]);

  return (
    <section className="review-panel" aria-labelledby="review-title">
      <div className="section-heading compact"><div><p className="eyebrow">Explainable review</p><h2 id="review-title">Highlights</h2></div><span>{pending.length} pending</span></div>
      {canReview && pending.length > 1 ? <button className="secondary-button" type="button" disabled={busy} onClick={() => review(pending.map((item) => item.id), "rejected")}>Reject all pending</button> : null}
      {error ? <p className="form-error" role="alert">{error}</p> : null}
      <div className="review-list">{highlights.map((highlight, index) => {
        const duplicateCount = groups.get(highlight.normalized_claim.trim().toLocaleLowerCase()) ?? 1;
        return <article className={index === selectedIndex ? "review-card selected" : "review-card"} key={highlight.id}>
          <div className="review-meta"><span className={`risk risk-${highlight.risk_level}`}>{highlight.risk_level}</span><span>{highlight.category.replaceAll("_", " ")}</span><span>{highlight.status}</span></div>
          <h3>{highlight.normalized_claim}</h3><p>{highlight.risk_reason}</p>
          <blockquote>“{highlight.quoted_text}”</blockquote>
          {duplicateCount > 1 ? <small>{duplicateCount} related suggestions grouped</small> : null}
          <a href={`#entry-${highlight.source_entry_id}`}>Open exact source</a>
          {canReview && highlight.status === "suggested" ? <div className="review-actions"><button type="button" disabled={busy} onClick={() => review([highlight.id], "accepted")}>Accept <kbd>A</kbd></button><button type="button" disabled={busy} onClick={() => review([highlight.id], "rejected")}>Reject <kbd>R</kbd></button></div> : null}
        </article>;
      })}</div>
    </section>
  );
}
