import { motion } from "motion/react";
import type { Conflict } from "../../data/types";
import { ease } from "../../theme/motion";
import { useSources } from "../../components/SourcesDrawer";
import RichText from "../../components/RichText";

// "Community is split": both positions side by side, each with a bar that grows to its share of the
// total source weight (scaleX), so the stronger side is visible at a glance. Neither side is hidden.
export default function ConflictCard({ cf }: { cf: Conflict }) {
  const openSources = useSources();
  const sides = cf.sides.slice(0, 2);
  const total = sides.reduce((a, s) => a + s.weight, 0) || 1;
  return (
    <motion.article
      data-conflict
      className="glass p-5"
      initial="hidden"
      whileInView="shown"
      viewport={{ once: true, margin: "0px 0px -10% 0px" }}
      variants={{ hidden: { opacity: 0, y: 10 }, shown: { opacity: 1, y: 0, transition: { duration: 0.5, ease: ease.out } } }}
    >
      <p className="text-sm text-amber">Community is split</p>
      <h3 className="mt-0.5 font-display text-lg text-gold-light">{cf.topic}</h3>
      <div className="mt-4 grid gap-4 md:grid-cols-[1fr_auto_1fr]">
        {sides.map((s, i) => (
          <div key={i} className={i === 1 ? "md:order-3" : ""}>
            <p className="leading-relaxed text-steel">
              <RichText text={s.position} />
            </p>
            <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-[rgb(174_184_199/0.12)]">
              <motion.div
                className="h-full origin-left rounded-full"
                style={{ background: i === 0 ? "var(--gold)" : "var(--frost)" }}
                variants={{ hidden: { scaleX: 0 }, shown: { scaleX: s.weight / total, transition: { duration: 0.9, ease: ease.out, delay: 0.25 } } }}
              />
            </div>
            <p className="mt-1.5 flex items-center justify-between text-xs text-steel-dim">
              <span className="tabular-nums">source weight {s.weight}</span>
              <button onClick={() => openSources({ title: `${cf.topic}: ${s.position}`, sources: s.sources })} className="hover:text-gold-light">
                {s.sources.length} source{s.sources.length === 1 ? "" : "s"}
              </button>
            </p>
          </div>
        ))}
        <span className="hidden self-center font-display text-sm text-steel-dim md:order-2 md:block">or</span>
      </div>
    </motion.article>
  );
}
