"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="min-h-screen flex items-center justify-center px-6">
      <div className="max-w-md text-center">
        <h2 className="font-display text-3xl text-parchment mb-4">
          Something went wrong
        </h2>
        <p className="text-slate-text mb-6">
          {error.message || "An unexpected error occurred."}
        </p>
        <button
          onClick={reset}
          className="bg-amber text-ink font-semibold px-6 py-2.5 rounded-xl hover:bg-amber-bright transition-colors"
        >
          Try again
        </button>
      </div>
    </main>
  );
}
