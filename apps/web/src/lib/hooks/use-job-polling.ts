"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getJobStatus } from "@/lib/api";
import type { JobStatusResponse } from "@/lib/types";

export function useJobPolling(jobId: string | null, intervalMs = 2000) {
  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stop = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!jobId) return;

    let active = true;

    const poll = async () => {
      try {
        const data = await getJobStatus(jobId);
        if (!active) return;
        setJob(data);
        if (data.status === "completed" || data.status === "failed") {
          stop();
        }
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Polling failed");
        stop();
      }
    };

    poll();
    timerRef.current = setInterval(poll, intervalMs);

    return () => {
      active = false;
      stop();
    };
  }, [jobId, intervalMs, stop]);

  return { job, error, stop };
}
