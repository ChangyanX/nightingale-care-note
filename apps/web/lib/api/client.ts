import { getPublicEnvironment } from "@/lib/env";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

export async function apiGet<T>(path: string, accessToken: string): Promise<T> {
  const { apiUrl } = getPublicEnvironment();
  const response = await fetch(`${apiUrl}${path}`, {
    headers: { authorization: `Bearer ${accessToken}` },
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = "The request could not be completed.";
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // Keep the sanitized default; never expose an upstream response body.
    }
    throw new ApiError(response.status, detail);
  }
  return (await response.json()) as T;
}
