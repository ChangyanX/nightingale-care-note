"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { createSupabaseBrowserClient } from "@/lib/supabase/browser";

export default function SignInPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const developmentAccounts = [
    ["Staff", "staff.a@nightingale.local"],
    ["Clinician", "clinician.a@nightingale.local"],
    ["Read-only admin", "admin.a@nightingale.local"],
    ["Patient", "patient.a@nightingale.local"],
  ] as const;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    const { error: authError } = await createSupabaseBrowserClient().auth.signInWithPassword({ email, password });
    if (authError) {
      setError("Sign-in failed. Check the selected demo account and password.");
      setSubmitting(false);
      return;
    }
    router.replace("/patients");
    router.refresh();
  }

  async function sendMagicLink() {
    if (!email) { setError("Enter an email address first."); return; }
    setSubmitting(true);
    setError(null);
    setMessage(null);
    const { error: authError } = await createSupabaseBrowserClient().auth.signInWithOtp({
      email,
      options: { emailRedirectTo: `${window.location.origin}/patients` },
    });
    if (authError) setError("Passwordless sign-in is unavailable for this environment.");
    else setMessage("If passwordless delivery is configured, a sign-in link has been requested.");
    setSubmitting(false);
  }

  return (
    <main className="auth-shell">
      <section className="auth-card" aria-labelledby="sign-in-title">
        <p className="eyebrow">Synthetic demonstration environment</p>
        <h1 id="sign-in-title">Open the shared patient story.</h1>
        <p className="lede">Use one of the generated demo identities stored in your local <code>.env.hosted-demo</code> file.</p>
        {process.env.NODE_ENV === "development" ? (
          <div className="demo-accounts" aria-label="Development account shortcuts">
            {developmentAccounts.map(([label, accountEmail]) => (
              <button key={accountEmail} type="button" onClick={() => setEmail(accountEmail)}>
                {label}
              </button>
            ))}
          </div>
        ) : null}
        <form onSubmit={submit} className="auth-form">
          <label>Email<input type="email" autoComplete="username" required value={email} onChange={(event) => setEmail(event.target.value)} /></label>
          <label>Password<input type="password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} /></label>
          {error ? <p className="form-error" role="alert">{error}</p> : null}
          <button className="primary-button" type="submit" disabled={submitting}>{submitting ? "Signing in…" : "Sign in"}</button>
          <button className="secondary-button" type="button" disabled={submitting} onClick={sendMagicLink}>Request passwordless link</button>
          {message ? <p className="form-success" role="status">{message}</p> : null}
        </form>
        <p className="privacy-note">Synthetic data only. Credentials and access tokens are never displayed or logged.</p>
      </section>
    </main>
  );
}
