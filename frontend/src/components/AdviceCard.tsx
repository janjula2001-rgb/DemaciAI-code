import type { AdviceItem } from "../data/types";
import { AdviceBadges, ConfidencePips } from "./Badges";
import { useSources } from "./SourcesDrawer";
import RichText from "./RichText";

const EDGE = { high: "var(--gold)", medium: "rgb(201 165 92 / 0.55)", low: "var(--steel-dim)" };

// One piece of advice: text, quiet confidence pips, warning badges only when needed, and a sources button.
// `general` marks items from the general Garen plan (dimmer, dashed edge).
export default function AdviceCard({ it, compact = false, general = false }: { it: AdviceItem; compact?: boolean; general?: boolean }) {
  const openSources = useSources();
  return (
    <article
      data-advice
      className={`relative rounded-[var(--radius-icon)] border border-[var(--gold-line)] ${general ? "bg-black/15" : "bg-[var(--glass)]"} ${compact ? "px-4 py-3" : "px-5 py-4"}`}
      style={{ borderLeft: `3px ${general ? "dashed" : "solid"} ${EDGE[it.confidence]}` }}
    >
      <p className={`${compact ? "text-[1.02rem]" : "text-[1.0625rem]"} max-w-[var(--measure)] leading-relaxed ${general ? "text-steel" : "text-gold-light/95"}`}>
        <RichText text={it.text} />
      </p>
      <div className="mt-2.5 flex flex-wrap items-center gap-2">
        <ConfidencePips level={it.confidence} />
        <AdviceBadges it={it} />
        <button
          onClick={() => openSources({ title: it.text, sources: it.sources })}
          className="ml-auto rounded-full px-2 py-0.5 text-xs text-steel-dim transition-colors hover:text-gold-light"
        >
          {it.sources.length} source{it.sources.length === 1 ? "" : "s"}
        </button>
      </div>
    </article>
  );
}
