"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import type { CurrentUser } from "@/lib/api/types";
import { createSupabaseBrowserClient } from "@/lib/supabase/browser";

export function AppHeader({ user }: { user: CurrentUser }) {
  const router = useRouter();
  const membership = user.memberships[0];

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
