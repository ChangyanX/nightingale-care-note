"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { PasswordField } from "@/components/password-field";
import { ThemeToggle } from "@/components/theme-toggle";
import { apiGet } from "@/lib/api/client";
import type { CurrentUser } from "@/lib/api/types";
import { createSupabaseBrowserClient } from "@/lib/supabase/browser";

const DEMO_PERSONAS = [
  { label: "Staff", description: "Coordinate actions and staff-authored updates", email: "staff.a@nightingale.local" },
  { label: "Clinician", description: "Review clinical context and AI suggestions", email: "clinician.a@nightingale.local" },
  { label: "Administrator", description: "View clinic-scoped oversight", email: "admin.a@nightingale.local" },
  { label: "Patient", description: "See the patient-safe portal experience", email: "patient.a@nightingale.local" },
] as const;

export function SignInExperience({ demo = false }: { demo?: boolean }) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (new URLSearchParams(window.location.search).get("password") === "changed") {
      queueMicrotask(() => setMessage("Password changed. Sign in again with your new password."));
    }
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    const supabase = createSupabaseBrowserClient();
    const { data, error: authError } = await supabase.auth.signInWithPassword({ email, password });
    if (authError) {
      setError(demo ? "Sign-in failed. Check the demo persona and password." : "Sign-in failed. Check your email and password.");
      setSubmitting(false);
      return;
    }
    const token = data.session?.access_token;
    if (!token) {
      setError("Sign-in completed without an application session.");
      setSubmitting(false);
      return;
    }
    try {
      const identity = await apiGet<CurrentUser>("/me", token);
      router.replace(identity.landing_path);
    } catch {
      await supabase.auth.signOut({ scope: "local" });
      setError("This account has no authorized Nightingale workspace.");
      setSubmitting(false);
    }
    router.refresh();
  }

  async function sendMagicLink() {
    if (!email) {
      setError("Enter your work email first.");
      return;
    }
    setSubmitting(true);
    setError(null);
    setMessage(null);
    const { error: authError } = await createSupabaseBrowserClient().auth.signInWithOtp({
      email,
      options: { emailRedirectTo: `${window.location.origin}/post-login` },
    });
    if (authError) setError("Email sign-in is unavailable for this environment.");
    else setMessage("If email sign-in is configured for this account, a link has been requested.");
    setSubmitting(false);
  }

  function selectPersona(personaEmail: string) {
    setEmail(personaEmail);
    setError(null);
    document.getElementById("demo-password")?.focus();
  }

  return (
    <main className={`auth-shell${demo ? " auth-shell-demo" : ""}`}>
      <header className="auth-header" aria-label="Nightingale Care Note">
        <Link className="auth-brand" href="/sign-in">
          <span className="brand-mark" aria-hidden="true">N</span>
          <span><strong>Nightingale</strong><small>Care Note</small></span>
        </Link>
        <div className="auth-header-actions">
          <span className="secure-access"><span aria-hidden="true">●</span> Secure clinic access</span>
          <ThemeToggle />
        </div>
      </header>

      {demo ? (
        <div className="environment-banner" role="status">
          <strong>Demo environment</strong>
          <span>Synthetic patient data only. Do not enter real patient information.</span>
        </div>
      ) : null}

      <section className="auth-content">
        <aside className="auth-trust-panel" aria-labelledby="auth-value-title">
          <p className="eyebrow">Nightingale Care Note</p>
          <h1 id="auth-value-title">One trusted patient story, across every care interaction.</h1>
          <p>A shared longitudinal record designed for rapid clinical understanding and accountable collaboration.</p>
          <ul className="trust-list">
            <li><span aria-hidden="true">✓</span> Longitudinal care context</li>
            <li><span aria-hidden="true">✓</span> Traceable clinical sources</li>
            <li><span aria-hidden="true">✓</span> Role-based collaboration</li>
          </ul>
        </aside>

        <section className="auth-card" aria-labelledby="sign-in-title">
          <p className="eyebrow">Welcome back</p>
          <h2 id="sign-in-title">Sign in to your clinic workspace</h2>
          <p className="lede">Your authenticated account determines your clinic and permissions.</p>

          <form onSubmit={submit} className="auth-form">
            <label>Work email<input type="email" autoComplete="username" required value={email} onChange={(event) => setEmail(event.target.value)} /></label>
            <PasswordField id={demo ? "demo-password" : undefined} label="Password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} />
            {error ? <p className="form-error" role="alert">{error}</p> : null}
            <button className="primary-button auth-submit" type="submit" disabled={submitting}>{submitting ? "Signing in…" : "Sign in"}</button>
            <div className="auth-secondary-actions">
              <button className="text-button" type="button" disabled={submitting} onClick={sendMagicLink}>Email me a sign-in link</button>
            </div>
            {message ? <p className="form-success" role="status">{message}</p> : null}
          </form>

          {demo ? (
            <section className="demo-access" aria-labelledby="demo-access-title">
              <div>
                <p className="eyebrow">Synthetic accounts</p>
                <h3 id="demo-access-title">Choose a demo persona</h3>
                <p>Each persona signs into a separate account whose role and clinic scope are enforced by the server.</p>
              </div>
              <div className="demo-personas">
                {DEMO_PERSONAS.map((persona) => (
                  <button key={persona.email} type="button" aria-pressed={email === persona.email} onClick={() => selectPersona(persona.email)}>
                    <strong>{persona.label}</strong>
                    <span>{persona.description}</span>
                  </button>
                ))}
              </div>
            </section>
          ) : null}

          <footer className="auth-footer">
            <span>Privacy-first access</span>
            <span aria-hidden="true">·</span>
            <span>Contact your clinic administrator for support</span>
          </footer>
        </section>
      </section>
    </main>
  );
}
