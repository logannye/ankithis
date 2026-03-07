"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "motion/react";
import { useAuth } from "@/lib/hooks/use-auth";

export default function LoginPage() {
  const router = useRouter();
  const { login, register, isAuthenticated } = useAuth();

  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // If already logged in, redirect
  if (isAuthenticated) {
    router.replace("/upload");
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(email, password, displayName || undefined);
      }
      router.push("/upload");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-6 py-16 relative overflow-hidden">
      {/* Ambient glow */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full bg-amber/5 blur-[120px] pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="w-full max-w-sm relative"
      >
        {/* Logo */}
        <Link href="/" className="block text-center mb-10">
          <span className="font-display text-3xl text-parchment">AnkiThis</span>
        </Link>

        {/* Mode toggle */}
        <div className="flex rounded-xl bg-ink-light border border-ink-lighter p-1 mb-8">
          <button
            type="button"
            onClick={() => {
              setMode("login");
              setError(null);
            }}
            className={`flex-1 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 ${
              mode === "login"
                ? "bg-ink-lighter text-parchment"
                : "text-slate-text hover:text-slate-text-bright"
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setMode("register");
              setError(null);
            }}
            className={`flex-1 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 ${
              mode === "register"
                ? "bg-ink-lighter text-parchment"
                : "text-slate-text hover:text-slate-text-bright"
            }`}
          >
            Create Account
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <AnimatePresence mode="wait">
            {mode === "register" && (
              <motion.div
                key="display-name"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <label className="block text-sm text-slate-text-bright mb-1.5 font-medium">
                  Display Name
                  <span className="text-slate-text ml-1 font-normal">(optional)</span>
                </label>
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="How should we call you?"
                  className="w-full bg-ink-light border border-ink-lighter rounded-xl px-4 py-3 text-parchment placeholder:text-ink-muted focus:outline-none focus:border-amber/50 transition-colors mb-4"
                />
              </motion.div>
            )}
          </AnimatePresence>

          <div>
            <label className="block text-sm text-slate-text-bright mb-1.5 font-medium">
              Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              autoComplete="email"
              className="w-full bg-ink-light border border-ink-lighter rounded-xl px-4 py-3 text-parchment placeholder:text-ink-muted focus:outline-none focus:border-amber/50 transition-colors"
            />
          </div>

          <div>
            <label className="block text-sm text-slate-text-bright mb-1.5 font-medium">
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={mode === "register" ? "At least 8 characters" : "Your password"}
              minLength={mode === "register" ? 8 : undefined}
              autoComplete={mode === "register" ? "new-password" : "current-password"}
              className="w-full bg-ink-light border border-ink-lighter rounded-xl px-4 py-3 text-parchment placeholder:text-ink-muted focus:outline-none focus:border-amber/50 transition-colors"
            />
          </div>

          {/* Error */}
          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                className="p-3 rounded-xl bg-coral/10 border border-coral/20 text-coral text-sm"
              >
                {error}
              </motion.div>
            )}
          </AnimatePresence>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-amber text-ink font-semibold py-3.5 rounded-xl text-base hover:bg-amber-bright transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 mt-2"
          >
            {loading ? (
              <>
                <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="3"
                    strokeDasharray="31.4 31.4"
                    strokeLinecap="round"
                  />
                </svg>
                {mode === "login" ? "Signing in..." : "Creating account..."}
              </>
            ) : mode === "login" ? (
              "Sign In"
            ) : (
              "Create Account"
            )}
          </button>
        </form>

        <p className="text-center text-slate-text text-sm mt-8">
          {mode === "login"
            ? "Free to use. Create an account to get started."
            : "Already have an account? Sign in above."}
        </p>
      </motion.div>
    </main>
  );
}
