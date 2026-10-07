import type { AdviceItem, Confidence } from "../data/types";
import Tooltip from "./Tooltip";

const CONF_TEXT: Record<Confidence, string> = {
  high: "High confidence: at least two strong sources agree.",
  medium: "Medium confidence: one strong source, or older strong sources.",
  low: "Low confidence: a single weaker source, archetype advice, or possibly outdated.",
};
const CONF_PIPS: Record<Confidence, number> = { high: 3, medium: 2, low: 1 };

// Three pips; the filled count is the confidence. Always shown, deliberately quiet.
export function ConfidencePips({ level }: { level: Confidence }) {
  return (
    <Tooltip content={CONF_TEXT[level]}>
      <span tabIndex={0} className="flex items-center gap-[3px] rounded px-0.5" aria-label={`${level} confidence`}>
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-1.5 w-3 rounded-full"
            style={{ background: i < CONF_PIPS[level] ? (level === "low" ? "var(--steel-dim)" : "var(--gold)") : "rgb(174 184 199 / 0.18)" }}
          />
        ))}
      </span>
    </Tooltip>
  );
}

// Labels appear only when something needs a second look (user request 2026-10-06: no "current" or
// "aging" labels; the aging reason stays in the sources drawer). Possibly outdated gets a slow pulse.
export function AdviceBadges({ it }: { it: AdviceItem }) {
  const reason = it.sources.find((s) => s.freshness === "possibly_outdated")?.freshness_reason;
  return (
    <>
      {it.freshness === "possibly_outdated" && (
        <Tooltip content={reason ? `Possibly outdated: ${reason}` : "Possibly outdated: a kit change since this source."}>
          <span tabIndex={0} className="relative inline-flex items-center gap-1.5 rounded-full border border-amber/70 px-2.5 py-0.5 text-xs font-medium text-amber">
            <span aria-hidden className="pulse-ring absolute inset-0 rounded-full border border-amber" />
            <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2.2" aria-hidden>
              <path d="M12 3 2 21h20L12 3Z" />
              <path d="M12 10v5M12 18h.01" />
            </svg>
            Possibly outdated
          </span>
        </Tooltip>
      )}
      {it.top_lane_only && <Tag text="From top-lane games" tip="Kit advice from top-lane sources; the matchup mechanics carry over to mid." />}
      {it.archetype_only && <Tag text="General archetype advice" tip="Not specific to this champion: advice for this type of opponent." />}
    </>
  );
}

function Tag({ text, tip }: { text: string; tip: string }) {
  return (
    <Tooltip content={tip}>
      <span tabIndex={0} className="rounded-full border border-[var(--gold-line)] px-2.5 py-0.5 text-xs text-steel-dim">
        {text}
      </span>
    </Tooltip>
  );
}
