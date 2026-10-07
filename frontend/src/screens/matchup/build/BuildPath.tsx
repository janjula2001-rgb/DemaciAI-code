import { Fragment } from "react";
import { motion } from "motion/react";
import { useAssets } from "../../../data/api";
import type { Capture, SheetRow } from "../../../data/types";
import { ease } from "../../../theme/motion";
import GameIcon, { resolveItems } from "../../../components/GameIcon";
import Arrow from "./Arrow";

const STEP = 0.16; // seconds between items appearing

const pop = (i: number) => ({
  hidden: { opacity: 0, scale: 0.8 },
  shown: { opacity: 1, scale: 1, transition: { duration: 0.4, ease: ease.out, delay: i * STEP } },
});

// Items appear one by one with an arrow drawing between them.
function Sequence({ steps }: { steps: { names: string[]; pct?: number; caption?: string }[] }) {
  return (
    <motion.div className="flex flex-wrap items-start gap-y-4" initial="hidden" whileInView="shown" viewport={{ once: true, margin: "0px 0px -10% 0px" }}>
      {steps.map((s, i) => (
        <Fragment key={i}>
          {i > 0 && <Arrow delay={i * STEP - 0.08} />}
          <motion.div variants={pop(i)} className="flex flex-col items-center gap-1">
            <div className="flex gap-1.5">
              {s.names.map((n, j) => (
                <GameIcon key={n + j} kind="item" name={n} size={52} />
              ))}
            </div>
            {s.pct !== undefined && <span className="text-xs tabular-nums text-gold-light">{s.pct}%</span>}
            {s.caption && <span className="text-[0.7rem] text-steel-dim">{s.caption}</span>}
          </motion.div>
        </Fragment>
      ))}
    </motion.div>
  );
}

export function OtpBuild({ capture }: { capture: Capture }) {
  const steps: { names: string[]; pct?: number; caption?: string }[] = [];
  if (capture.starting_items) steps.push({ names: capture.starting_items.items, pct: capture.starting_items.pct, caption: "Start" });
  if (capture.early_purchase_order) steps.push({ names: capture.early_purchase_order.items, pct: capture.early_purchase_order.pct, caption: "Early buys" });
  if (capture.first_item) steps.push({ names: capture.first_item.items, pct: capture.first_item.pct, caption: "First item" });
  if (capture.popular_boots[0]) steps.push({ names: [capture.popular_boots[0].item], pct: capture.popular_boots[0].pct, caption: "Boots" });
  return (
    <div className="glass p-6">
      <h3 className="font-display text-lg text-gold-light">Build path, Master+ one-tricks</h3>
      <p className="mb-5 mt-1 text-sm text-steel-dim">onetricks.gg, patches {capture.patches}. Percentages are how often they pick it; there are no game counts.</p>
      <Sequence steps={steps} />
      <div className="mt-7 grid gap-6 md:grid-cols-[auto_1fr]">
        <div>
          <p className="mb-2 text-xs text-steel-dim">Boots</p>
          <div className="flex gap-3">
            {capture.popular_boots.slice(0, 3).map((b) => (
              <GameIcon key={b.item} kind="item" name={b.item} size={44} pct={b.pct} />
            ))}
          </div>
        </div>
        <div>
          <p className="mb-2 text-xs text-steel-dim">Most built after that, by how often (not a strict order)</p>
          <div className="flex flex-wrap gap-3">
            {capture.popular_items.slice(0, 7).map((b) => (
              <GameIcon key={b.item} kind="item" name={b.item} size={44} pct={b.pct} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// Federals1's sheet lists a real ordered path; cells like "A/ B" become options in one step.
export function SheetBuild({ row }: { row: SheetRow }) {
  const { data: assets } = useAssets();
  const steps = row.build_path
    .map((raw) => ({ raw, names: assets?.items[raw] ? [raw] : resolveItems(assets, raw) }))
    .filter((s) => s.names.length)
    .map((s) => ({ names: s.names, caption: s.names.length > 1 ? "either" : undefined }));
  return <Sequence steps={steps} />;
}
