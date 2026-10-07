import { motion } from "motion/react";
import type { Capture } from "../../../data/types";
import { ease } from "../../../theme/motion";
import GameIcon from "../../../components/GameIcon";

// Summoner spells and skill order as cards that flip in (rotateY) one after another.
const flip = (i: number) => ({
  hidden: { opacity: 0, rotateY: -80 },
  shown: { opacity: 1, rotateY: 0, transition: { duration: 0.55, ease: ease.out, delay: i * 0.1 } },
});

export function SummonerCards({ capture }: { capture: Capture }) {
  return (
    <div className="glass p-6">
      <h3 className="font-display text-lg text-gold-light">Summoner spells</h3>
      <motion.div className="mt-4 flex flex-wrap gap-3" style={{ perspective: 800 }} initial="hidden" whileInView="shown" viewport={{ once: true }}>
        {capture.summoners.slice(0, 3).map((s, i) => (
          <motion.div
            key={s.spells.join("+")}
            variants={flip(i)}
            className={`flex items-center gap-3 rounded-[var(--radius-icon)] border px-3.5 py-3 ${i === 0 ? "border-gold/60 bg-[rgb(201_165_92/0.08)]" : "border-[var(--gold-line)] bg-black/20"}`}
          >
            <div className="flex gap-1.5">
              {s.spells.map((sp) => (
                <GameIcon key={sp} kind="spell" name={sp} size={40} />
              ))}
            </div>
            <div>
              <p className="text-sm text-gold-light">{s.spells.join(" + ")}</p>
              <p className="text-xs tabular-nums text-steel-dim">{s.pct}% of games</p>
            </div>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}

// 4 x 13 grid; the levelled cells light up in level order when it scrolls into view.
export function SkillGrid({ capture, main }: { capture: Capture; main: string }) {
  const order = capture.skill_order_1_13;
  return (
    <div className="glass p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <h3 className="font-display text-lg text-gold-light">Skill order</h3>
        <p className="text-sm text-steel-dim">
          Max {capture.skill_max_order.split("").join(" › ")}
          {capture.levels_1_3.length > 0 && `; levels 1–3: ${capture.levels_1_3.map((l) => `${l.order.split("").join("-")} ${l.pct}%`).join(", ")}`}
        </p>
      </div>
      <motion.table className="mt-4 border-separate border-spacing-1" initial="hidden" whileInView="shown" viewport={{ once: true }}>
        <tbody>
          {(["Q", "W", "E", "R"] as const).map((key) => (
            <tr key={key}>
              <td className="pr-2">
                <GameIcon kind="ability" name={`${main}:${key}`} size={30} />
              </td>
              {Array.from({ length: 13 }, (_, i) => {
                const on = order[i] === key;
                return (
                  <td key={i} className="relative h-8 w-8 rounded-md bg-[rgb(174_184_199/0.07)] text-center text-xs tabular-nums">
                    {on && (
                      <motion.span
                        className="absolute inset-0 grid place-items-center rounded-md bg-[linear-gradient(180deg,#e6cd8e,var(--gold))] font-semibold text-night"
                        variants={{ hidden: { opacity: 0, scale: 0.4 }, shown: { opacity: 1, scale: 1, transition: { duration: 0.3, ease: ease.out, delay: 0.15 + i * 0.06 } } }}
                      >
                        {i + 1}
                      </motion.span>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </motion.table>
    </div>
  );
}

export function StartCard({ capture }: { capture: Capture }) {
  if (!capture.starting_items) return null;
  return (
    <div className="glass p-6">
      <h3 className="font-display text-lg text-gold-light">Starting items</h3>
      <motion.div className="mt-4 flex gap-2" style={{ perspective: 800 }} initial="hidden" whileInView="shown" viewport={{ once: true }}>
        {capture.starting_items.items.map((n, i) => (
          <motion.div key={n + i} variants={flip(i)}>
            <GameIcon kind="item" name={n} size={52} label />
          </motion.div>
        ))}
      </motion.div>
      <p className="mt-3 text-sm tabular-nums text-steel-dim">{capture.starting_items.pct}% of one-trick games</p>
    </div>
  );
}
