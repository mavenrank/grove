import { createContext, useContext, useMemo, type ReactNode } from "react";
import { TelemetryBuffer } from "./api";

/** Shared app context: one telemetry buffer per SPA session.
 *  Lives at the app root so the chrome-less test runner can use it too. */
interface TelemetryContextValue {
  buffer: TelemetryBuffer;
}

const TelemetryContext = createContext<TelemetryContextValue | null>(null);

export function TelemetryProvider({ children }: { children: ReactNode }) {
  const value = useMemo<TelemetryContextValue>(() => ({ buffer: new TelemetryBuffer() }), []);
  return <TelemetryContext.Provider value={value}>{children}</TelemetryContext.Provider>;
}

export function useTelemetry(): TelemetryContextValue {
  const ctx = useContext(TelemetryContext);
  if (!ctx) throw new Error("useTelemetry outside provider");
  return ctx;
}
