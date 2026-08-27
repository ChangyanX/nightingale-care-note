import { createBrowserClient } from "@supabase/ssr";

import { getPublicEnvironment } from "@/lib/env";

export function createSupabaseBrowserClient() {
  const { supabaseUrl, supabasePublishableKey } = getPublicEnvironment();

  return createBrowserClient(supabaseUrl, supabasePublishableKey);
}
