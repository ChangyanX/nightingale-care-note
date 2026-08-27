"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppHeader } from "@/components/app-header";
import { ApiError, apiGet } from "@/lib/api/client";
import type { CurrentUser, Patient } from "@/lib/api/types";
import { createSupabaseBrowserClient } from "@/lib/supabase/browser";

export default function PatientsPage() {
  const router = useRouter();
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [patients, setPatients] = useState<Patient[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      const { data } = await createSupabaseBrowserClient().auth.getSession();
      const token = data.session?.access_token;
      if (!token) { router.replace("/sign-in"); return; }
      try {
        const [nextUser, nextPatients] = await Promise.all([
          apiGet<CurrentUser>("/me", token),
          apiGet<Patient[]>("/patients", token),
        ]);
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

  if (error) return <main className="state-page"><h1>Patient list unavailable</h1><p>{error}</p></main>;
  if (!user || !patients) return <main className="state-page" aria-busy="true"><p>Loading your clinic workspace…</p></main>;

  return (
    <div className="app-shell">
      <AppHeader user={user} />
      <main className="workspace patient-index">
        <div className="page-heading"><div><p className="eyebrow">Clinic workspace</p><h1>Select a patient</h1></div><p>Only records available to your authenticated clinic role appear here.</p></div>
        {patients.length ? <div className="patient-grid">{patients.map((patient) => (
          <Link className="patient-card" href={`/patients/${patient.id}`} key={patient.id}>
            <span className="patient-initial" aria-hidden="true">{patient.display_name.charAt(0)}</span>
            <span><strong>{patient.display_name}</strong><small>{patient.synthetic_identifier}</small></span>
            <span aria-hidden="true">→</span>
          </Link>
        ))}</div> : <section className="empty-state"><h2>No accessible patients</h2><p>Your account is active, but no patient records are assigned to this clinic scope.</p></section>}
      </main>
    </div>
  );
}
