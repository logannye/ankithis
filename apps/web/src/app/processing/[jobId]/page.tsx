"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "motion/react";
import { useJobPolling } from "@/lib/hooks/use-job-polling";
import { useRequireAuth } from "@/lib/hooks/use-auth";
import { STAGE_LABELS, STAGE_ORDER } from "@/lib/types";
import type { JobStatus } from "@/lib/types";

function stageIndex(status: JobStatus): number {
  const idx = STAGE_ORDER.indexOf(status);
  return idx === -1 ? 0 : idx;
}

export default function ProcessingPage() {
  const { loading: authLoading } = useRequireAuth();
  const params = useParams<{ jobId: string }>();
  const router = useRouter();
  const { job, error } = useJobPolling(params.jobId);

  const currentIdx = job ? stageIndex(job.status) : 0;

  useEffect(() => {
    if (job?.status === "completed") {
      const timer = setTimeout(() => {
        router.push(`/review/${job.document_id}`);
      }, 1200);
      return () => clearTimeout(timer);
    }
  }, [job, router]);

  if (authLoading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="text-slate-text">Loading...</div>
      </main>
    );
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-6 py-16">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        <h1 className="font-display text-4xl mb-2">Generating your deck</h1>
        <p className="text-slate-text mb-12">
          This usually takes 2–5 minutes depending on document size.
        </p>

        {/* Stage stepper */}
        <div className="space-y-0">
          {STAGE_ORDER.slice(0, -1).map((stage, i) => {
            const isActive = i === currentIdx;
            const isDone = i < currentIdx;
            const isFailed = job?.status === "failed" && i === currentIdx;

            return (
              <div key={stage} className="flex gap-4">
                {/* Vertical line + dot */}
                <div className="flex flex-col items-center">
                  <div
                    className={`w-3.5 h-3.5 rounded-full border-2 transition-all duration-500 flex-shrink-0 ${
                      isFailed
                        ? "border-coral bg-coral"
                        : isDone
                          ? "border-sage bg-sage"
                          : isActive
                            ? "border-amber bg-amber"
                            : "border-ink-muted bg-ink-light"
                    }`}
                  >
                    {isActive && !isFailed && (
                      <motion.div
                        className="w-full h-full rounded-full bg-amber"
                        animate={{ scale: [1, 1.6, 1], opacity: [1, 0.4, 1] }}
                        transition={{ duration: 1.5, repeat: Infinity }}
                      />
                    )}
                  </div>
                  {i < STAGE_ORDER.length - 2 && (
                    <div
                      className={`w-0.5 h-8 transition-colors duration-500 ${
                        isDone ? "bg-sage/40" : "bg-ink-lighter"
                      }`}
                    />
                  )}
                </div>

                {/* Label */}
                <div className="pb-6 -mt-0.5">
                  <span
                    className={`text-sm font-medium transition-colors duration-300 ${
                      isFailed
                        ? "text-coral"
                        : isActive
                          ? "text-parchment"
                          : isDone
                            ? "text-sage"
                            : "text-ink-muted"
                    }`}
                  >
                    {STAGE_LABELS[stage]}
                  </span>
                  {isActive && !isFailed && (
                    <motion.span
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="ml-2 text-xs text-amber font-mono"
                    >
                      in progress
                    </motion.span>
                  )}
                  {isDone && (
                    <span className="ml-2 text-xs text-sage font-mono">
                      done
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Completed */}
        {job?.status === "completed" && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 p-5 rounded-xl bg-sage/10 border border-sage/20"
          >
            <p className="text-sage font-medium">
              Generation complete — {job.total_cards} cards created
            </p>
            <p className="text-slate-text text-sm mt-1">
              Redirecting to review...
            </p>
          </motion.div>
        )}

        {/* Failed */}
        {job?.status === "failed" && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 p-5 rounded-xl bg-coral/10 border border-coral/20"
          >
            <p className="text-coral font-medium">Generation failed</p>
            {job.error_message && (
              <p className="text-slate-text text-sm mt-1">{job.error_message}</p>
            )}
          </motion.div>
        )}

        {/* Polling error */}
        {error && (
          <div className="mt-6 p-4 rounded-xl bg-coral/10 border border-coral/20 text-coral text-sm">
            {error}
          </div>
        )}
      </motion.div>
    </main>
  );
}
