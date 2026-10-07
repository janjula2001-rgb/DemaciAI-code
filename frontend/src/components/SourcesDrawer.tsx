import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import type { SourceRef } from "../data/types";
import { dur, ease } from "../theme/motion";

const TYPE_LABEL: Record<string, string> = {
  otp_guide: "Garen one-trick guide",
  otp_video: "Garen one-trick video",
  onetricks_data: "One-trick build data",
  stats: "Rank-filtered stats",
  reddit_garenmains: "r/Garenmains",
  reddit_other: "Reddit",
  other_guide: "Other guide",
};
const FRESH_LABEL: Record<string, string> = { valid: "Current", aging: "Aging", possibly_outdated: "Possibly outdated", invalid: "Outdated" };
const SCOPE_LABEL: Record<string, string> = { matchup: "", top_lane: "From top-lane games" };

interface Open {
  title: string;
  sources: SourceRef[];
}
const Ctx = createContext<(o: Open) => void>(() => {});
export const useSources = () => useContext(Ctx);

// Slide-in drawer from the right listing the sources behind a piece of advice. Esc or the backdrop closes it.
export function SourcesProvider({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState<Open | null>(null);
  const close = useCallback(() => setOpen(null), []);
  const closeBtn = useRef<HTMLButtonElement>(null);
  const opener = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!open) {
      opener.current?.focus(); // keyboard users land back on the button that opened the drawer
      opener.current = null;
      return;
    }
    opener.current ??= document.activeElement as HTMLElement | null;
    closeBtn.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      e.preventDefault();
      e.stopImmediatePropagation(); // don't also leave the page
      close();
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [open, close]);

  return (
    <Ctx.Provider value={setOpen}>
      {children}
      <AnimatePresence>
        {open && (
          <>
            <motion.div
              key="backdrop"
              className="fixed inset-0 z-[65] bg-black/50"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: dur.quick }}
              onClick={close}
            />
            <motion.aside
              key="drawer"
              role="dialog"
              aria-modal="true"
              aria-label={`Sources: ${open.title}`}
              className="fixed inset-y-0 right-0 z-[66] flex w-[min(480px,92vw)] flex-col border-l border-[var(--gold-line)] bg-[var(--glass-strong)] shadow-[-30px_0_80px_-20px_rgb(0_0_0/0.8)] backdrop-blur-xl"
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ duration: dur.base, ease: ease.out }}
            >
              <div className="flex items-start justify-between gap-4 border-b border-[var(--gold-line)] p-5">
                <div>
                  <h2 className="font-display text-lg text-gold-light">Sources</h2>
                  <p className="mt-1 text-sm text-steel-dim">{open.title}</p>
                </div>
                <button ref={closeBtn} onClick={close} className="rounded-full p-1.5 text-steel-dim hover:text-gold-light" aria-label="Close sources">
                  <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M6 6l12 12M18 6 6 18" />
                  </svg>
                </button>
              </div>
              <ol className="flex-1 space-y-3 overflow-y-auto p-5 [scrollbar-width:thin]">
                {open.sources.map((s, i) => (
                  <motion.li
                    key={s.id + i}
                    initial={{ opacity: 0, x: 24 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: dur.base, ease: ease.out, delay: 0.08 + i * 0.05 }}
                    className="rounded-[var(--radius-icon)] border border-[var(--gold-line)] bg-black/20 p-4"
                  >
                    <p className="flex flex-wrap items-baseline justify-between gap-x-3">
                      <span className="font-semibold text-gold-light">{s.author}</span>
                      <span className="text-xs tabular-nums text-steel-dim">{s.source_date}</span>
                    </p>
                    <p className="mt-0.5 text-xs text-steel-dim">
                      {[TYPE_LABEL[s.source_type] ?? s.source_type, s.elo_context !== "unknown" && `${s.elo_context} elo`, SCOPE_LABEL[s.scope] ?? "General plan"]
                        .filter(Boolean)
                        .join(", ")}
                    </p>
                    <blockquote className="mt-2 border-l-2 border-gold/50 pl-3 text-sm italic leading-relaxed text-steel">{s.claim}</blockquote>
                    {s.freshness !== "valid" && (
                      <p className={`mt-2 text-xs ${s.freshness === "possibly_outdated" ? "text-amber" : "text-steel-dim"}`}>
                        {FRESH_LABEL[s.freshness]}
                        {s.freshness_reason ? `: ${s.freshness_reason}` : ""}
                      </p>
                    )}
                    <a href={s.source_url} target="_blank" rel="noreferrer" className="mt-2 block break-all text-xs text-frost hover:underline">
                      {s.source_url}
                    </a>
                  </motion.li>
                ))}
              </ol>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </Ctx.Provider>
  );
}
