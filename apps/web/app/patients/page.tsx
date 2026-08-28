"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { AppHeader } from "@/components/app-header";
import { ApiError, apiGet } from "@/lib/api/client";
import type { CurrentUser, Patient } from "@/lib/api/types";
import { createSupabaseBrowserClient } from "@/lib/supabase/browser";

export default function PatientsPage() {
  const router = useRouter();
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [patients, setPatients] = useState<Patient[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [recentIds, setRecentIds] = useState<string[]>([]);

  useEffect(() => {
    let active = true;
    try {
      const stored = JSON.parse(localStorage.getItem("nightingale-recent-patients") ?? "[]") as unknown;
      if (Array.isArray(stored)) {
        const next = stored.filter((item): item is string => typeof item === "string").slice(0, 5);
        queueMicrotask(() => { if (active) setRecentIds(next); });
      }
    } catch {
      localStorage.removeItem("nightingale-recent-patients");
    }
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    async function load() {
      const { data } = await createSupabaseBrowserClient().auth.getSession();
      const token = data.session?.access_token;
      if (!token) { router.replace("/sign-in"); return; }
      try {
        const nextUser = await apiGet<CurrentUser>("/me", token);
        if (nextUser.account_kind === "patient") { router.replace("/patient"); return; }
        const nextPatients = await apiGet<Patient[]>("/patients", token);
        if (!active) return;
        if (!nextUser.memberships.length) { setError("This account has no active clinic membership."); return; }
        setUser(nextUser);
        setPatients(nextPatients);
      } catch (requestError) {
        if (!active) return;
        if (requestError instanceof ApiError && requestError.status === 401) { router.replace("/sign-in"); return; }
        setError("Patient access is temporarily unavailable. Please retry.");
      }
    }
    void load();
    return () => { active = false; };
  }, [router]);

  const visiblePatients = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase();
    return (patients ?? [])
      .filter((patient) => !normalized || `${patient.display_name} ${patient.synthetic_identifier}`.toLocaleLowerCase().includes(normalized))
      .sort((left, right) => {
        const leftRecent = recentIds.indexOf(left.id);
        const rightRecent = recentIds.indexOf(right.id);
        if (leftRecent === -1 && rightRecent === -1) return left.display_name.localeCompare(right.display_name);
        if (leftRecent === -1) return 1;
        if (rightRecent === -1) return -1;
        return leftRecent - rightRecent;
      });
  }, [patients, query, recentIds]);

  function remember(patientId: string) {
    const next = [patientId, ...recentIds.filter((item) => item !== patientId)].slice(0, 5);
    setRecentIds(next);
    localStorage.setItem("nightingale-recent-patients", JSON.stringify(next));
  }

  if (error) return <main className="state-page"><h1>Patient list unavailable</h1><p>{error}</p></main>;
  if (!user || !patients) return <main className="state-page skeleton-page" aria-busy="true"><span className="skeleton-line wide" /><span className="skeleton-line" /><p>Loading your clinic workspace…</p></main>;

  return (
    <div className="app-shell">
      <AppHeader user={user} />
      <main className="workspace patient-index">
        <div className="page-heading"><div><p className="eyebrow">Clinic workspace</p><h1>Select a patient</h1></div><p>Only records available to your authenticated clinic role appear here.</p></div>
        <label className="patient-search">Search patients<input type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Name or synthetic ID" /></label>
        {visiblePatients.length ? <div className="patient-grid">{visiblePatients.map((patient) => (
          <Link className="patient-card" href={`/patients/${patient.id}`} key={patient.id} onClick={() => remember(patient.id)}>
            <span className="patient-initial" aria-hidden="true">{patient.display_name.charAt(0)}</span>
            <span><strong>{patient.display_name}</strong><small>{patient.synthetic_identifier}{recentIds.includes(patient.id) ? " · Recently viewed" : ""}</small></span>
            <span aria-hidden="true">→</span>
          </Link>
        ))}</div> : <section className="empty-state"><h2>No matching patients</h2><p>Clear the search or confirm your clinic scope.</p></section>}
      </main>
    </div>
  );
}
