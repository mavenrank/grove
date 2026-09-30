/** Low-level HTTP layer: fetch wrapper, error mapping, cache invalidation hook. */

export const BASE = "";

export class ApiError extends Error {
  status: number;
  code?: string;
  constructor(status: number, message: string, code?: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

/** Registered by the cache module; called for every non-GET so mutations
 *  can drop affected reads. Telemetry/view/source-open POSTs change no
 *  read data and must not nuke the cache. */
export type InvalidateFn = (path: string) => void;

let onMutate: InvalidateFn | null = null;

export function setInvalidationHook(fn: InvalidateFn): void {
  onMutate = fn;
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let resp: Response;
  const method = (init?.method ?? "GET").toUpperCase();
  try {
    resp = await fetch(`${BASE}${path}`, {
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
      ...init,
    });
    if (method !== "GET") onMutate?.(path);
  } catch {
    throw new ApiError(0, "Cannot reach the Grove backend. Is it running on port 8001?");
  }
  if (!resp.ok) {
    let detail = `Request failed (${resp.status})`;
    let code: string | undefined;
    try {
      const body = (await resp.json()) as { detail?: unknown };
      if (typeof body.detail === "string") {
        code = body.detail;
        detail = code.replace(/_/g, " ");
      }
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(resp.status, detail, code);
  }
  return (await resp.json()) as T;
}
