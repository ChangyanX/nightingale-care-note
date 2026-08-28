"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";

import { AppHeader } from "@/components/app-header";
import { PasswordField } from "@/components/password-field";
import { apiGet, apiPatch, apiPost } from "@/lib/api/client";
import type { AccountProfile, CurrentUser } from "@/lib/api/types";
import { createSupabaseBrowserClient } from "@/lib/supabase/browser";

type AccountData = { user: CurrentUser; profile: AccountProfile; token: string };

export default function AccountPage() {
  const router = useRouter();
  const [data, setData] = useState<AccountData | null>(null);
  const [preferredName, setPreferredName] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    async function load() {
      const { data: session } = await createSupabaseBrowserClient().auth.getSession();
      const token = session.session?.access_token;
      if (!token) { router.replace("/sign-in"); return; }
      try {
        const [user, profile] = await Promise.all([apiGet<CurrentUser>("/me", token), apiGet<AccountProfile>("/me/profile", token)]);
        if (!active) return;
        setData({ user, profile, token });
        setPreferredName(profile.preferred_name);
        setBirthDate(profile.birth_date ?? "");
      } catch { if (active) setError("Account settings are unavailable."); }
    }
    void load();
    return () => { active = false; };
  }, [router]);

  async function saveProfile(event: FormEvent) {
    event.preventDefault();
    if (!data) return;
    setBusy(true); setError(null); setMessage(null);
    try {
      const profile = await apiPatch<AccountProfile>("/me/profile", data.token, { preferred_name: preferredName, birth_date: birthDate || null });
      setData({ ...data, profile, user: { ...data.user, display_name: profile.display_name, preferred_name: profile.preferred_name } });
      setMessage("Account information updated.");
    } catch { setError("Account information could not be updated."); }
    finally { setBusy(false); }
  }

  async function uploadAvatar(file: File | undefined) {
    if (!data || !file) return;
    setError(null); setMessage(null);
    if (!["image/png", "image/jpeg", "image/webp"].includes(file.type)) { setError("Use a PNG, JPEG, or WebP avatar."); return; }
    if (file.size > 1_048_576) { setError("Avatar must be no larger than 1 MB."); return; }
    setBusy(true);
    try {
      const encoded = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result).split(",", 2)[1] ?? "");
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });
      const avatar = await apiPost<{ avatar_path: string; avatar_url: string }>("/me/avatar", data.token, { filename: file.name, content_type: file.type, data_base64: encoded });
      setData({ ...data, profile: { ...data.profile, avatar_path: avatar.avatar_path, avatar_url: avatar.avatar_url } });
      setMessage("Avatar updated.");
    } catch { setError("Avatar could not be uploaded."); }
    finally { setBusy(false); }
  }

  async function changePassword(event: FormEvent) {
    event.preventDefault();
    if (!data?.profile.email) return;
    setError(null); setMessage(null);
    if (newPassword !== confirmPassword) { setError("New passwords do not match."); return; }
    if (newPassword.length < 12 || !/[A-Z]/.test(newPassword) || !/[a-z]/.test(newPassword) || !/\d/.test(newPassword) || !/[^A-Za-z0-9]/.test(newPassword)) { setError("Use at least 12 characters with upper/lowercase, a number, and a symbol."); return; }
    if (newPassword === currentPassword) { setError("Choose a password different from the current password."); return; }
    setBusy(true);
    const supabase = createSupabaseBrowserClient();
    const reauthenticated = await supabase.auth.signInWithPassword({ email: data.profile.email, password: currentPassword });
    if (reauthenticated.error) { setError("Current password is incorrect."); setBusy(false); return; }
    const changed = await supabase.auth.updateUser({ password: newPassword });
    if (changed.error) { setError("Password could not be changed."); setBusy(false); return; }
    await supabase.auth.signOut({ scope: "global" });
    router.replace("/sign-in?password=changed");
    router.refresh();
  }

  async function logout() {
    await createSupabaseBrowserClient().auth.signOut({ scope: "global" });
    router.replace("/sign-in");
    router.refresh();
  }

  if (!data) return <main className="state-page" aria-busy="true"><p>{error ?? "Loading account settings…"}</p></main>;
  const role = data.user.memberships[0]?.role ?? "patient";
  return <div className="app-shell"><AppHeader user={data.user} /><main className="workspace account-workspace"><header className="page-heading"><div><p className="eyebrow">Signed-in identity</p><h1>Account Settings</h1></div><p>Only your permitted synthetic profile fields can be changed here.</p></header>{message ? <p className="form-success" role="status">{message}</p> : null}{error ? <p className="form-error" role="alert">{error}</p> : null}<div className="settings-grid"><section className="settings-card"><h2>Profile</h2><div className="avatar-editor">{data.profile.avatar_url ? <Image unoptimized width={72} height={72} src={data.profile.avatar_url} alt="Current profile avatar" /> : <span aria-hidden="true">{data.profile.preferred_name.charAt(0)}</span>}<label>Change avatar<input type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => void uploadAvatar(event.target.files?.[0])} /></label><small>PNG, JPEG, or WebP; maximum 1 MB.</small></div><form className="settings-form" onSubmit={saveProfile}><label>Preferred name<input required maxLength={80} value={preferredName} onChange={(event) => setPreferredName(event.target.value)} /></label><label>Birth date <small>Optional</small><input type="date" value={birthDate} onChange={(event) => setBirthDate(event.target.value)} /></label><label>Account email<input value={data.profile.email ?? "Unavailable"} readOnly /></label><label>Role<input value={role} readOnly /></label><label>Clinic/account context<input value={data.user.memberships.map((item) => `${item.role} · ${item.clinic_id.slice(0, 8)}`).join(", ") || `patient · ${data.profile.linked_patient_id?.slice(0, 8)}`} readOnly /></label><button className="primary-button" disabled={busy} type="submit">Save profile</button></form></section><section className="settings-card"><h2>Security</h2><p className="revision-note">Changing your password requires the current password and signs out all sessions.</p><form className="settings-form" onSubmit={changePassword}><PasswordField label="Current password" required autoComplete="current-password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} /><PasswordField label="New password" required autoComplete="new-password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} /><PasswordField label="Confirm new password" required autoComplete="new-password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} /><button className="primary-button" disabled={busy} type="submit">Change password</button></form><button className="secondary-button settings-logout" type="button" onClick={() => void logout()}>Log out</button></section></div></main></div>;
}
