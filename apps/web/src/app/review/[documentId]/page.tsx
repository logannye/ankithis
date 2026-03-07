"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "motion/react";
import {
  getReview,
  removeCard,
  removeSectionFromDeck,
  regenerateCards,
  getExportUrl,
} from "@/lib/api";
import { useRequireAuth } from "@/lib/hooks/use-auth";
import type { ReviewResponse, CardOut, SectionCards } from "@/lib/types";

function renderCloze(text: string): React.ReactNode {
  const parts = text.split(/({{c\d+::.*?}})/g);
  return parts.map((part, i) => {
    const match = part.match(/{{c\d+::(.*?)}}/);
    if (match) {
      return (
        <span key={i} className="cloze-blank">
          {match[1]}
        </span>
      );
    }
    return part;
  });
}

function CardItem({
  card,
  onRemove,
}: {
  card: CardOut;
  onRemove: (id: string) => void;
}) {
  const [removing, setRemoving] = useState(false);

  if (card.suppressed) return null;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -20, height: 0 }}
      className="group border border-ink-lighter rounded-xl p-4 hover:border-ink-muted transition-colors"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <span
              className={`text-xs font-mono px-2 py-0.5 rounded-md ${
                card.card_type === "cloze"
                  ? "bg-lavender/10 text-lavender"
                  : "bg-amber/10 text-amber"
              }`}
            >
              {card.card_type}
            </span>
            {card.tags && (
              <span className="text-xs text-slate-text truncate">
                {card.tags}
              </span>
            )}
          </div>
          <p className="text-parchment text-sm leading-relaxed">
            {card.card_type === "cloze" ? renderCloze(card.front) : card.front}
          </p>
          {card.card_type === "basic" && card.back && (
            <p className="text-slate-text text-sm mt-2 pl-3 border-l-2 border-ink-lighter">
              {card.back}
            </p>
          )}
        </div>
        <button
          onClick={() => {
            setRemoving(true);
            onRemove(card.id);
          }}
          disabled={removing}
          className="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-lg hover:bg-coral/10 text-slate-text hover:text-coral flex-shrink-0"
          title="Remove card"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </motion.div>
  );
}

function SectionGroup({
  section,
  onRemoveCard,
  onRemoveSection,
}: {
  section: SectionCards;
  onRemoveCard: (id: string) => void;
  onRemoveSection: (id: string) => void;
}) {
  const activeCards = section.cards.filter((c) => !c.suppressed);
  if (activeCards.length === 0) return null;

  return (
    <div className="mb-10">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-display text-xl text-parchment">
          {section.section_title || "Untitled Section"}
        </h3>
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-slate-text">
            {activeCards.length} card{activeCards.length !== 1 ? "s" : ""}
          </span>
          <button
            onClick={() => onRemoveSection(section.section_id)}
            className="text-xs text-slate-text hover:text-coral transition-colors"
          >
            Remove section
          </button>
        </div>
      </div>
      <div className="space-y-3">
        <AnimatePresence>
          {activeCards.map((card) => (
            <CardItem key={card.id} card={card} onRemove={onRemoveCard} />
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}

export default function ReviewPage() {
  const { loading: authLoading } = useRequireAuth();
  const params = useParams<{ documentId: string }>();
  const router = useRouter();
  const [data, setData] = useState<ReviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [regenerating, setRegenerating] = useState(false);

  const load = useCallback(async () => {
    try {
      const review = await getReview(params.documentId);
      setData(review);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load review");
    } finally {
      setLoading(false);
    }
  }, [params.documentId]);

  useEffect(() => {
    load();
  }, [load]);

  const handleRemoveCard = useCallback(
    async (cardId: string) => {
      try {
        await removeCard(cardId);
        setData((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            active_cards: prev.active_cards - 1,
            suppressed_cards: prev.suppressed_cards + 1,
            sections: prev.sections.map((s) => ({
              ...s,
              cards: s.cards.map((c) =>
                c.id === cardId ? { ...c, suppressed: true } : c,
              ),
            })),
          };
        });
      } catch {
        // Silently fail — card still visible
      }
    },
    [],
  );

  const handleRemoveSection = useCallback(
    async (sectionId: string) => {
      try {
        await removeSectionFromDeck(sectionId);
        setData((prev) => {
          if (!prev) return prev;
          const section = prev.sections.find((s) => s.section_id === sectionId);
          const removedCount = section?.cards.filter((c) => !c.suppressed).length || 0;
          return {
            ...prev,
            active_cards: prev.active_cards - removedCount,
            suppressed_cards: prev.suppressed_cards + removedCount,
            sections: prev.sections.map((s) =>
              s.section_id === sectionId
                ? { ...s, cards: s.cards.map((c) => ({ ...c, suppressed: true })) }
                : s,
            ),
          };
        });
      } catch {
        // Silently fail
      }
    },
    [],
  );

  const handleRegenerate = useCallback(async () => {
    setRegenerating(true);
    try {
      const gen = await regenerateCards(params.documentId);
      router.push(`/processing/${gen.job_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Regeneration failed");
      setRegenerating(false);
    }
  }, [params.documentId, router]);

  if (authLoading || loading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="text-slate-text">Loading...</div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen flex items-center justify-center px-6">
        <div className="p-6 rounded-xl bg-coral/10 border border-coral/20 text-coral max-w-md">
          {error}
        </div>
      </main>
    );
  }

  if (!data) return null;

  return (
    <main className="min-h-screen px-6 py-16">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-10"
        >
          <h1 className="font-display text-4xl md:text-5xl mb-2">
            {data.title || "Your Deck"}
          </h1>
          <div className="flex items-center gap-4 text-sm text-slate-text mt-3">
            <span className="font-mono text-sage">
              {data.active_cards} active
            </span>
            {data.suppressed_cards > 0 && (
              <span className="font-mono text-slate-text">
                {data.suppressed_cards} removed
              </span>
            )}
            <span className="font-mono">
              {data.total_cards} total
            </span>
          </div>
        </motion.div>

        {/* Actions */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="flex flex-wrap gap-3 mb-10"
        >
          <a
            href={getExportUrl(data.document_id, "apkg")}
            className="inline-flex items-center gap-2 bg-amber text-ink font-semibold px-5 py-2.5 rounded-xl hover:bg-amber-bright transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
            </svg>
            Download APKG
          </a>
          <a
            href={getExportUrl(data.document_id, "csv")}
            className="inline-flex items-center gap-2 border border-ink-lighter text-parchment font-medium px-5 py-2.5 rounded-xl hover:border-slate-text transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
            </svg>
            Download CSV
          </a>
          <button
            onClick={handleRegenerate}
            disabled={regenerating}
            className="inline-flex items-center gap-2 border border-ink-lighter text-slate-text-bright font-medium px-5 py-2.5 rounded-xl hover:border-amber hover:text-amber transition-colors disabled:opacity-50"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182M21.015 4.356v4.992" />
            </svg>
            {regenerating ? "Starting..." : "Regenerate"}
          </button>
        </motion.div>

        {/* Sections */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4, delay: 0.2 }}
        >
          {data.sections.map((section) => (
            <SectionGroup
              key={section.section_id}
              section={section}
              onRemoveCard={handleRemoveCard}
              onRemoveSection={handleRemoveSection}
            />
          ))}
        </motion.div>
      </div>
    </main>
  );
}
