/** useApiData: one hook for every cached read.
 *
 * Pages previously repeated the same useState/useEffect/useApiVersion
 * boilerplate for each read. This hook centralizes it: data + error +
 * loading, re-running when the SWR cache signals a revalidate/invalidate.
 * Because api reads go through the cache, revisits render instantly from
 * cached data (the hook still returns the cached payload on first render
 * after a re-resolve) — the hook just re-executes the (cached) fetcher.
 */
import { useEffect, useState } from "react";
import { useApiVersion } from "./cache";

export function useApiData<T>(fetcher: () => Promise<T>): {
  data: T | null;
  error: string | null;
} {
  const version = useApiVersion();
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const d = await fetcher();
        if (alive) {
          setData(d);
          setError(null);
        }
      } catch {
        if (alive) {
          setError("Could not reach the backend. Start it with `grove-serve` (port 8001 — temporary).");
        }
      }
    })();
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [version]);

  return { data, error };
}
