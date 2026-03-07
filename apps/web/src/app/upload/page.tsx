"use client";

import { useCallback, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "motion/react";
import { uploadDocument, generateCards } from "@/lib/api";
import { useRequireAuth } from "@/lib/hooks/use-auth";
import type { CardStyle, DeckSize } from "@/lib/types";

const ACCEPTED_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "text/plain",
  "text/markdown",
];
const ACCEPTED_EXT = [".pdf", ".docx", ".txt", ".md"];
const MAX_SIZE = 50 * 1024 * 1024;

export default function UploadPage() {
  const { loading: authLoading } = useRequireAuth();
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [studyGoal, setStudyGoal] = useState("");
  const [cardStyle, setCardStyle] = useState<CardStyle>("cloze_heavy");
  const [deckSize, setDeckSize] = useState<DeckSize>("medium");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isValidFile = useCallback((f: File) => {
    if (f.size > MAX_SIZE) return "File must be under 50 MB";
    const ext = "." + f.name.split(".").pop()?.toLowerCase();
    if (!ACCEPTED_EXT.includes(ext)) return "Unsupported file type";
    return null;
  }, []);

  const handleFile = useCallback(
    (f: File) => {
      const err = isValidFile(f);
      if (err) {
        setError(err);
        return;
      }
      setError(null);
      setFile(f);
    },
    [isValidFile],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const f = e.dataTransfer.files[0];
      if (f) handleFile(f);
    },
    [handleFile],
  );

  const handleSubmit = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const doc = await uploadDocument(file, {
        study_goal: studyGoal || undefined,
        card_style: cardStyle,
        deck_size: deckSize,
      });
      const gen = await generateCards(doc.document_id);
      router.push(`/processing/${gen.job_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setLoading(false);
    }
  };

  if (authLoading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="text-slate-text">Loading...</div>
      </main>
    );
  }

  return (
    <main className="min-h-screen flex flex-col items-center px-6 py-16">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-xl"
      >
        <h1 className="font-display text-4xl md:text-5xl mb-2">
          Upload your document
        </h1>
        <p className="text-slate-text mb-10">
          Drop a file and configure how you want your flashcard deck built.
        </p>

        {/* Dropzone */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={`relative rounded-2xl border-2 border-dashed p-12 text-center cursor-pointer transition-all duration-300 ${
            dragOver
              ? "border-amber bg-amber/5 scale-[1.01]"
              : file
                ? "border-sage/50 bg-sage/5"
                : "border-ink-muted hover:border-slate-text"
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED_EXT.join(",")}
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleFile(f);
            }}
          />

          {file ? (
            <div className="flex flex-col items-center gap-2">
              <div className="w-12 h-12 rounded-xl bg-sage/10 flex items-center justify-center mb-2">
                <svg className="w-6 h-6 text-sage" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <span className="text-parchment font-medium">{file.name}</span>
              <span className="text-slate-text text-sm">
                {(file.size / 1024).toFixed(0)} KB
              </span>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setFile(null);
                }}
                className="text-coral text-sm mt-1 hover:underline"
              >
                Remove
              </button>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              <div className="w-14 h-14 rounded-2xl bg-ink-lighter flex items-center justify-center">
                <svg className="w-7 h-7 text-slate-text" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                </svg>
              </div>
              <p className="text-slate-text-bright">
                Drop your file here or{" "}
                <span className="text-amber">browse</span>
              </p>
              <p className="text-slate-text text-sm">
                PDF, DOCX, TXT, or Markdown — up to 50 MB
              </p>
            </div>
          )}
        </div>

        {/* Options */}
        <AnimatePresence>
          {file && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden"
            >
              <div className="mt-8 space-y-6">
                {/* Study Goal */}
                <div>
                  <label className="block text-sm text-slate-text-bright mb-2 font-medium">
                    Study Goal
                    <span className="text-slate-text ml-1 font-normal">(optional)</span>
                  </label>
                  <input
                    type="text"
                    value={studyGoal}
                    onChange={(e) => setStudyGoal(e.target.value)}
                    placeholder="e.g. Prepare for organic chemistry midterm"
                    className="w-full bg-ink-light border border-ink-lighter rounded-xl px-4 py-3 text-parchment placeholder:text-ink-muted focus:outline-none focus:border-amber/50 transition-colors"
                  />
                </div>

                {/* Card Style */}
                <div>
                  <label className="block text-sm text-slate-text-bright mb-3 font-medium">
                    Card Style
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {(
                      [
                        ["cloze_heavy", "Cloze Heavy", "Fill-in-the-blank focused"],
                        ["qa_heavy", "Q&A Heavy", "Question & answer focused"],
                        ["balanced", "Balanced", "Mix of both styles"],
                      ] as const
                    ).map(([value, label, desc]) => (
                      <button
                        key={value}
                        type="button"
                        onClick={() => setCardStyle(value)}
                        className={`rounded-xl border p-3 text-left transition-all duration-200 ${
                          cardStyle === value
                            ? "border-amber bg-amber/5"
                            : "border-ink-lighter hover:border-slate-text"
                        }`}
                      >
                        <span className={`block text-sm font-medium ${cardStyle === value ? "text-amber" : "text-parchment"}`}>
                          {label}
                        </span>
                        <span className="block text-xs text-slate-text mt-0.5">
                          {desc}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Deck Size */}
                <div>
                  <label className="block text-sm text-slate-text-bright mb-3 font-medium">
                    Deck Size
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {(
                      [
                        ["small", "Fewer", "Key concepts only"],
                        ["medium", "Balanced", "Solid coverage"],
                        ["large", "More", "Deep, thorough coverage"],
                      ] as const
                    ).map(([value, label, desc]) => (
                      <button
                        key={value}
                        type="button"
                        onClick={() => setDeckSize(value)}
                        className={`rounded-xl border p-3 text-left transition-all duration-200 ${
                          deckSize === value
                            ? "border-amber bg-amber/5"
                            : "border-ink-lighter hover:border-slate-text"
                        }`}
                      >
                        <span className={`block text-sm font-medium ${deckSize === value ? "text-amber" : "text-parchment"}`}>
                          {label}
                        </span>
                        <span className="block text-xs text-slate-text mt-0.5">
                          {desc}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Submit */}
              <button
                type="button"
                onClick={handleSubmit}
                disabled={loading}
                className="mt-8 w-full bg-amber text-ink font-semibold py-4 rounded-xl text-lg hover:bg-amber-bright transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3"
              >
                {loading ? (
                  <>
                    <svg className="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="31.4 31.4" strokeLinecap="round" />
                    </svg>
                    Uploading & Starting...
                  </>
                ) : (
                  <>
                    Generate Flashcards
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                    </svg>
                  </>
                )}
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="mt-4 p-4 rounded-xl bg-coral/10 border border-coral/20 text-coral text-sm"
            >
              {error}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </main>
  );
}
