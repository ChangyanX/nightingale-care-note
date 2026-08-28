"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { ThemeToggle } from "@/components/theme-toggle";
import { apiGet, apiPost } from "@/lib/api/client";
import type { CurrentUser, Notification } from "@/lib/api/types";
import { createSupabaseBrowserClient } from "@/lib/supabase/browser";

const NOTIFICATION_LABELS: Record<Notification["event_type"], string> = {
  mention: "You were mentioned in a Care Note conversation.",
  assignment: "A clinic-scoped action was assigned to you.",
  ai_job_completed: "An AI-scribe job is ready for authorized review.",
  care_update: "A patient-facing care update is available.",
  appointment_update: "An appointment request status changed.",
  report_released: "A patient-released report is available.",
};

export function AppHeader({ user }: { user: CurrentUser }) {
  const router = useRouter();
  const membership = user.memberships[0];
  const home = user.account_kind === "patient" ? "/patient" : "/patients";
  const [menuOpen, setMenuOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);
  const [notificationOpen, setNotificationOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const unread = useMemo(() => notifications.filter((item) => !item.read_at && item.status !== "dismissed").length, [notifications]);

  useEffect(() => {
    let active = true;
    async function loadNotifications() {
      const { data } = await createSupabaseBrowserClient().auth.getSession();
      const token = data.session?.access_token;
      if (!token) return;
      try {
        const rows = await apiGet<Notification[]>("/notifications", token);
        if (active) setNotifications(rows.filter((item) => item.status !== "dismissed"));
      } catch { /* Header remains usable if notification delivery is unavailable. */ }
    }
    void loadNotifications();
    return () => { active = false; };
  }, []);

  async function signOut() {
    await createSupabaseBrowserClient().auth.signOut({ scope: "global" });
    router.replace("/sign-in");
    router.refresh();
  }

  async function openNotifications() {
    const opening = !notificationOpen;
    setNotificationOpen(opening);
    setAccountOpen(false);
    if (!opening) return;
    const { data } = await createSupabaseBrowserClient().auth.getSession();
    const token = data.session?.access_token;
    if (!token) return;
    const unreadItems = notifications.filter((item) => !item.read_at);
    const marked = await Promise.all(unreadItems.map(async (item) => {
      try { return await apiPost<Notification>(`/notifications/${item.id}/read`, token, {}); }
      catch { return item; }
    }));
    const markedById = new Map(marked.map((item) => [item.id, item]));
    setNotifications((items) => items.map((item) => markedById.get(item.id) ?? item));
  }

  return (
    <header className="app-header">
      <Link className="brand" href={home}><span className="brand-mark" aria-hidden="true">N</span><span>Nightingale Care Note</span></Link>
      <button className="menu-button" type="button" aria-expanded={menuOpen} aria-controls="mobile-navigation" onClick={() => setMenuOpen((value) => !value)}>Menu</button>
      <nav className={menuOpen ? "mobile-navigation open" : "mobile-navigation"} id="mobile-navigation" aria-label="Workspace"><Link href={home} onClick={() => setMenuOpen(false)}>{user.account_kind === "patient" ? "My dashboard" : "Patients"}</Link>{user.account_kind === "clinic_user" ? <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">API docs</a> : null}</nav>
      <div className="header-actions">
        <div className="header-popover-wrap"><button className="icon-button" type="button" aria-label={`Notification Centre${unread ? `, ${unread} unread` : ""}`} aria-expanded={notificationOpen} onClick={() => void openNotifications()}><span aria-hidden="true">♢</span>{unread ? <span className="notification-count">{unread}</span> : null}</button>{notificationOpen ? <section className="header-popover notification-centre" aria-label="Notification Centre"><div><strong>Notification Centre</strong><small>Clinic-scoped, content-safe previews</small></div>{notifications.length ? <ul>{notifications.slice(0, 8).map((item) => <li key={item.id} className={item.read_at ? "" : "unread"}><span>{NOTIFICATION_LABELS[item.event_type]}</span><time dateTime={item.created_at}>{new Date(item.created_at).toLocaleDateString("en-SG")}</time></li>)}</ul> : <p>No notifications.</p>}</section> : null}</div>
        <ThemeToggle />
        <div className="header-popover-wrap"><button className="avatar-button" type="button" aria-label="Open account menu" aria-expanded={accountOpen} onClick={() => { setAccountOpen((value) => !value); setNotificationOpen(false); }}><span aria-hidden="true">{user.preferred_name.charAt(0).toUpperCase()}</span></button>{accountOpen ? <section className="header-popover account-menu"><strong>{user.preferred_name}</strong><small>{membership ? `${membership.role}${membership.role === "admin" ? " · read only" : ""}` : "patient account"}</small><Link href="/account">Account Settings</Link><button type="button" onClick={() => void signOut()}>Log out</button></section> : null}</div>
      </div>
    </header>
  );
}
