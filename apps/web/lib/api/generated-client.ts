import createClient from "openapi-fetch";

import { getPublicEnvironment } from "@/lib/env";
import type { paths } from "./openapi.generated";

export function createGeneratedApiClient(accessToken: string) {
  return createClient<paths>({
    baseUrl: getPublicEnvironment().apiUrl,
    headers: { authorization: `Bearer ${accessToken}` },
  });
}
