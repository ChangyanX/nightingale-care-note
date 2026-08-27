export type PublicEnvironment = {
  supabaseUrl: string;
  supabasePublishableKey: string;
};

export function getPublicEnvironment(): PublicEnvironment {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabasePublishableKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

  if (!supabaseUrl || !supabasePublishableKey) {
    throw new Error("Supabase public environment is not configured.");
  }

  return { supabaseUrl, supabasePublishableKey };
}
