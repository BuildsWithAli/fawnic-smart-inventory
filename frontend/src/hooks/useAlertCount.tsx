import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { alertService } from "../services";

interface AlertCountContextValue {
  /** Number of unresolved AI stock alerts — drives the Topbar bell badge. */
  count: number;
  /** Re-fetch the count now. Call after any action that can create or resolve an alert. */
  refresh: () => void;
}

const AlertCountContext = createContext<AlertCountContextValue | undefined>(undefined);

const POLL_INTERVAL_MS = 60_000;

export function AlertCountProvider({ children }: { children: ReactNode }) {
  const [count, setCount] = useState(0);

  const refresh = useCallback(async () => {
    try {
      const data = await alertService.list({ resolved: "false" });
      setCount(data.count);
    } catch {
      /* non-critical widget — leave the last known count in place */
    }
  }, []);

  useEffect(() => {
    void refresh();
    const interval = setInterval(() => void refresh(), POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [refresh]);

  return (
    <AlertCountContext.Provider value={{ count, refresh: () => void refresh() }}>
      {children}
    </AlertCountContext.Provider>
  );
}

export function useAlertCount(): AlertCountContextValue {
  const ctx = useContext(AlertCountContext);
  if (!ctx) throw new Error("useAlertCount must be used within an AlertCountProvider");
  return ctx;
}
