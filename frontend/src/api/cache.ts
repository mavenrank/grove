/** Read cache: stale-while-revalidate + hover prefetch — revisits render
 *  instantly (no spinner) and refresh in the background. */
import { useEffect, useState } from "react";
import { request, setInvalidationHook } from "./client";

interface CacheEntry {
  data: unknown;
  fetchedAt: number; // 0 = first fetch still in flight
  refreshing?: Promise<unknown>;
}

const DEFAULT_TTL_MS = 10_000;
const getCache = new Map<string, CacheEntry>();
const versionListeners = new Set<() => void>();
let apiVersion = 0;

// Mutations flow through client.request; this module owns what they invalidate.
setInvalidationHook(invalidateFor);

function notifyDataRefreshed(): void {
  apiVersion += 1;
  for (const cb of versionListeners) cb();
}

export async function getCached<T>(path: string, ttlMs = DEFAULT_TTL_MS): Promise<T> {
  const entry = getCache.get(path);
  if (entry) {
    if (entry.fetchedAt > 0) {
      const stale = Date.now() - entry.fetchedAt > ttlMs;
      if (stale && !entry.refreshing) {
        entry.refreshing = request<T>(path)
          .then((data) => {
            getCache.set(path, { data, fetchedAt: Date.now() });
            notifyDataRefreshed();
          })
          .catch(() => {
            /* stale data survives a background refresh failure */
          })
          .finally(() => {
            const e = getCache.get(path);
            if (e) e.refreshing = undefined;
          });
      }
      return entry.data as T;
    }
    // first fetch still in flight — everyone awaits the same promise
    return (entry.refreshing ?? Promise.resolve(entry.data)) as Promise<T>;
  }
  const inflight = request<T>(path).then((data) => {
    getCache.set(path, { data, fetchedAt: Date.now() });
    return data;
  }) as Promise<T>;
  getCache.set(path, { data: null, fetchedAt: 0, refreshing: inflight });
  return inflight;
}

/** Drop cached reads affected by a mutation path. */
export function invalidateFor(path: string): void {
  const drop = (prefixes: string[]) => {
    for (const key of [...getCache.keys()]) {
      if (prefixes.some((p) => key.startsWith(p))) getCache.delete(key);
    }
  };
  if (path.startsWith("/api/test-sessions")) {
    drop(["/api/history", "/api/insights"]);
  } else if (path.startsWith("/api/flashcard-reviews")) {
    drop(["/api/flashcards"]);
  } else if (path.startsWith("/api/flashcard-views")) {
    drop(["/api/flashcards/stats"]);
  } else {
    return;
  }
  notifyDataRefreshed();
}

/** React version counter: pages depend on it so a background revalidate
 *  (or post-mutation invalidation) re-renders with fresh data. */
export function useApiVersion(): number {
  const [v, setV] = useState(apiVersion);
  useEffect(() => {
    const cb = () => setV(apiVersion);
    versionListeners.add(cb);
    return () => {
      versionListeners.delete(cb);
    };
  }, []);
  return v;
}

if (import.meta.env.DEV) {
  // cache introspection for debugging navigation behaviour in devtools
  Object.assign(window, {
    __groveCache: {
      keys: () => [...getCache.keys()],
      state: () =>
        [...getCache.entries()].map(([k, e]) => ({
          key: k,
          ageMs: e.fetchedAt ? Date.now() - e.fetchedAt : "in-flight",
          refreshing: Boolean(e.refreshing),
        })),
    },
  });
}
