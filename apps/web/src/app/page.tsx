"use client";

import Link from "next/link";
import { motion } from "motion/react";

const STEPS = [
  {
    num: "01",
    title: "Upload",
    desc: "Drop your PDF, DOCX, TXT, or Markdown file.",
  },
  {
    num: "02",
    title: "Configure",
    desc: "Choose your study goal, card style, and deck size.",
  },
  {
    num: "03",
    title: "Generate",
    desc: "Our 7-stage AI pipeline extracts, critiques, and refines cards.",
  },
  {
    num: "04",
    title: "Export",
    desc: "Download your deck as CSV or APKG — ready for Anki.",
  },
];

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col">
      {/* Hero */}
      <section className="flex-1 flex flex-col items-center justify-center px-6 py-24 relative overflow-hidden">
        {/* Ambient glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-amber/5 blur-[120px] pointer-events-none" />

        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-amber font-mono text-sm tracking-[0.2em] uppercase mb-6"
        >
          Document → Flashcards
        </motion.p>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.2 }}
          className="font-display text-6xl sm:text-7xl md:text-8xl text-center leading-[0.95] tracking-tight max-w-4xl"
        >
          Turn any document
          <br />
          <span className="text-amber italic">into mastery</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="mt-8 text-slate-text-bright text-lg md:text-xl text-center max-w-xl leading-relaxed"
        >
          Upload your study material. Get a polished, ready-to-import Anki deck
          — powered by a multi-pass AI pipeline that extracts, critiques, and
          deduplicates every card.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.6 }}
          className="mt-10"
        >
          <Link
            href="/upload"
            className="group inline-flex items-center gap-3 bg-amber text-ink font-semibold px-8 py-4 rounded-full text-lg hover:bg-amber-bright transition-colors duration-200"
          >
            Get Started
            <svg
              className="w-5 h-5 transition-transform duration-200 group-hover:translate-x-1"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M13 7l5 5m0 0l-5 5m5-5H6"
              />
            </svg>
          </Link>
        </motion.div>
      </section>

      {/* Steps */}
      <section className="border-t border-ink-lighter px-6 py-20">
        <div className="max-w-5xl mx-auto">
          <h2 className="font-display text-3xl md:text-4xl mb-14 text-center">
            How it works
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {STEPS.map((step, i) => (
              <motion.div
                key={step.num}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
                className="group"
              >
                <span className="font-mono text-amber text-sm tracking-wider">
                  {step.num}
                </span>
                <h3 className="font-display text-2xl mt-2 mb-3 group-hover:text-amber transition-colors duration-300">
                  {step.title}
                </h3>
                <p className="text-slate-text leading-relaxed text-sm">
                  {step.desc}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-ink-lighter px-6 py-8">
        <div className="max-w-5xl mx-auto flex items-center justify-between text-slate-text text-sm">
          <span className="font-display text-lg text-parchment">AnkiThis</span>
          <span>Supports PDF, DOCX, TXT, Markdown — up to 50 MB</span>
        </div>
      </footer>
    </main>
  );
}
