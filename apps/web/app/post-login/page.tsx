"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { apiGet } from "@/lib/api/client";
import type { CurrentUser } from "@/lib/api/types";
import { createSupabaseBrowserClient } from "@/lib/supabase/browser";

export default function PostLoginPage() {
  const router = useRouter();
  useEffect(() => {
    async function routeAccount() {
      const { data } = await createSupabaseBrowserClient().auth.getSession();
      const token = data.session?.access_token;
      if (!token) { router.replace("/sign-in"); return; }
      try {
        const identity = await apiGet<CurrentUser>("/me", token);
        router.replace(identity.landing_path);
      } catch { router.replace("/sign-in"); }
    }
    void routeAccount();
  }, [router]);
  return <main className="state-page" aria-busy="true"><p>Opening your role-appropriate workspace…</p></main>;
}
