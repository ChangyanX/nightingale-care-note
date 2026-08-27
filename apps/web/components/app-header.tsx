"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import type { CurrentUser } from "@/lib/api/types";
import { createSupabaseBrowserClient } from "@/lib/supabase/browser";

export function AppHeader({ user }: { user: CurrentUser }) {
  const router = useRouter();
  const membership = user.memberships[0];
  const [menuOpen, setMenuOpen] = useState(false);

  async function signOut() {
    await createSupabaseBrowserClient().auth.signOut();
    router.replace("/sign-in");
    router.refresh();
  }

  return (
    <header className="app-header">
      <Link className="brand" href="/patients">
        <span className="brand-mark" aria-hidden="true">N</span>
        <span>Nightingale Care Note</span>
      </Link>
      <button className="menu-button" type="button" aria-expanded={menuOpen} aria-controls="mobile-navigation" onClick={() => setMenuOpen((value) => !value)}>Menu</button>
      <nav className={menuOpen ? "mobile-navigation open" : "mobile-navigation"} id="mobile-navigation" aria-label="Workspace">
        <Link href="/patients" onClick={() => setMenuOpen(false)}>Patients</Link>
        <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">API docs</a>
      </nav>
      <div className="session-summary">
        <span>
          <strong>{user.display_name}</strong>
          {membership ? <small>{membership.role}{membership.role === "admin" ? " · read only" : ""}</small> : null}
        </span>
        <button className="text-button" type="button" onClick={signOut}>Sign out</button>
      </div>
    </header>
  );
}
