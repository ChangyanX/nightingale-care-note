export type PublicEnvironment = {
  supabaseUrl: string;
  supabasePublishableKey: string;
  apiUrl: string;
};

export function getPublicEnvironment(): PublicEnvironment {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabasePublishableKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  if (!supabaseUrl || !supabasePublishableKey) {
    throw new Error("Supabase public environment is not configured.");
  }

  return { supabaseUrl, supabasePublishableKey, apiUrl: apiUrl.replace(/\/$/, "") };
}
