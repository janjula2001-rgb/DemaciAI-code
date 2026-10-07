import { useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { useAssets } from "../../../data/api";
import type { Capture } from "../../../data/types";
import { dur, ease, spring } from "../../../theme/motion";
import GameIcon from "../../../components/GameIcon";

// Keystone options as a toggle (crossfade between them); the most-picked one shows the full page
// one-tricks used. Only that page was captured, so other keystones show just their share.
export default function RunePage({ capture }: { capture: Capture }) {
  const { data: assets } = useAssets();
  const [sel, setSel] = useState(0);
  const ks = capture.keystones;
  const k = ks[sel];
  const shownPage = k.shown_page || (sel === 0 && !ks.some((x) => x.shown_page));
  const page = capture.rune_page_shown.slice(1).filter((r) => !r.startsWith("+"));
  // the capture cuts some shard labels mid-parenthesis ("+10-180 Health (based on level"); drop the stub
  const shards = capture.rune_page_shown.filter((r) => r.startsWith("+")).map((r) => r.replace(/\s*\([^)]*$/, ""));

  return (
    <div className="glass p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="font-display text-lg text-gold-light">Runes</h3>
        <div role="tablist" aria-label="Keystone" className="flex flex-wrap gap-1 rounded-full border border-[var(--gold-line)] bg-black/25 p-1">
          {ks.map((x, i) => (
            <button
              key={x.name}
              role="tab"
              aria-selected={i === sel}
              onClick={() => setSel(i)}
              className={`relative rounded-full px-3 py-1 text-xs transition-colors ${i === sel ? "text-night" : "text-steel hover:text-gold-light"}`}
            >
              {i === sel && <motion.span layoutId="keystone-tab" transition={spring} className="absolute inset-0 -z-0 rounded-full bg-gold" />}
              <span className="relative">
                {x.name} <span className="tabular-nums opacity-75">{x.pct}%</span>
              </span>
            </button>
          ))}
        </div>
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={k.name}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: dur.quick, ease: ease.out }}
          className="mt-5 flex flex-wrap items-start gap-6"
        >
          <div className="flex items-center gap-4">
            <span className="relative">
              <span aria-hidden className="keystone-glow absolute -inset-3 rounded-full" />
              <GameIcon kind="rune" name={k.name} size={72} glow />
            </span>
            <div className="max-w-[22rem]">
              <p className="font-display text-xl text-gold-light">{k.name}</p>
              <p className="text-sm text-steel-dim">
                {assets?.runes[k.name]?.style}, picked in {k.pct}% of one-trick games
              </p>
              {assets?.runes[k.name]?.short && <p className="mt-1.5 text-sm leading-snug text-steel">{assets.runes[k.name].short}</p>}
            </div>
          </div>
          {shownPage ? (
            <div>
              <p className="mb-2 text-xs text-steel-dim">Rest of the page</p>
              <div className="flex flex-wrap gap-2.5">
                {page.map((r, i) => (
                  <GameIcon key={r + i} kind="rune" name={r} size={40} />
                ))}
              </div>
              {shards.length > 0 && <p className="mt-2 text-xs text-steel-dim">Shards: {shards.join(", ")}</p>}
            </div>
          ) : (
            <p className="max-w-[24rem] self-center text-sm text-steel-dim">The full page one-tricks use with this keystone wasn't captured; only how often they pick it.</p>
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
