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

export async function apiPost<T>(
  path: string,
  accessToken: string,
  body: unknown,
): Promise<T> {
  const { apiUrl } = getPublicEnvironment();
  const response = await fetch(`${apiUrl}${path}`, {
    method: "POST",
    headers: {
      authorization: `Bearer ${accessToken}`,
      "content-type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    let detail = "The request could not be completed.";
    try {
      const responseBody = (await response.json()) as { detail?: unknown };
      if (typeof responseBody.detail === "string") detail = responseBody.detail;
    } catch {
      // Keep the sanitized default; never expose an upstream response body.
    }
    throw new ApiError(response.status, detail);
  }
  return (await response.json()) as T;
}

export async function apiPatch<T>(
  path: string,
  accessToken: string,
  body: unknown,
): Promise<T> {
  const { apiUrl } = getPublicEnvironment();
  const response = await fetch(`${apiUrl}${path}`, {
    method: "PATCH",
    headers: {
      authorization: `Bearer ${accessToken}`,
      "content-type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new ApiError(response.status, "The update could not be completed.");
  return (await response.json()) as T;
}
