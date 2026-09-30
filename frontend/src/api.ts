/**
 * Typed API client for the Grove backend.
 *
 * Facade over the decomposed modules in `src/api/`:
 *   client    — fetch wrapper + ApiError
 *   cache     — stale-while-revalidate read cache + useApiVersion
 *   types     — mirrors of backend response models (handoff §8.6)
 *   endpoints — endpoint functions (the `api` object)
 *   telemetry — TestEvent types + TelemetryBuffer
 *
 * The Question type intentionally has NO answer fields: the backend never
 * sends them. New code can import from `./api` exactly as before — this
 * facade keeps every existing import path working.
 */

export { ApiError } from "./api/client";
export * from "./api/types";
export { sourceCaption } from "./api/types";
export { useApiVersion } from "./api/cache";
export { useApiData } from "./api/hooks";
export { api } from "./api/endpoints";
export { TelemetryBuffer } from "./api/telemetry";
export type { TestEvent, TestEventType } from "./api/telemetry";
