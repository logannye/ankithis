"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getJobStatus } from "@/lib/api";
import type { JobStatusResponse } from "@/lib/types";

export function useJobPolling(jobId: string | null) {
  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const startRef = useRef<number>(0);

  const stop = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!jobId) return;

    let active = true;
    startRef.current = Date.now();

    const getInterval = (): number => {
      const elapsed = Date.now() - startRef.current;
      if (elapsed > 120_000) return 10_000; // after 2 min: 10s
      if (elapsed > 30_000) return 5_000;   // after 30s: 5s
      return 2_000;                          // initial: 2s
    };

    const poll = async () => {
      try {
        const data = await getJobStatus(jobId);
        if (!active) return;
        setJob(data);
        if (data.status === "completed" || data.status === "failed") {
          stop();
          return;
        }
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Polling failed");
        stop();
        return;
      }
      // Schedule next poll with backoff
      if (active) {
        timerRef.current = setTimeout(poll, getInterval());
      }
    };

    poll();

    return () => {
      active = false;
      stop();
    };
  }, [jobId, stop]);

  return { job, error, stop };
}
