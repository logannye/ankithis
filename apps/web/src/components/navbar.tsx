"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/hooks/use-auth";

export default function Navbar() {
  const pathname = usePathname();
  const { user, isAuthenticated, logout } = useAuth();

  // Don't show navbar on landing page
  if (pathname === "/") return null;

  return (
    <nav className="fixed top-0 inset-x-0 z-50 border-b border-ink-lighter bg-ink/80 backdrop-blur-md">
      <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
        <Link href="/" className="font-display text-xl text-parchment hover:text-amber transition-colors">
          AnkiThis
        </Link>

        <div className="flex items-center gap-4">
          {isAuthenticated ? (
            <>
              <span className="text-sm text-slate-text hidden sm:block">
                {user?.email}
              </span>
              <button
                onClick={logout}
                className="text-sm text-slate-text hover:text-coral transition-colors"
              >
                Sign Out
              </button>
            </>
          ) : (
            <Link
              href="/login"
              className="text-sm text-amber hover:text-amber-bright transition-colors font-medium"
            >
              Sign In
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}
