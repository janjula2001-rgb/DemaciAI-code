import { motion } from "motion/react";
import type { AdviceItem, Capture, Conflict, Role } from "../../data/types";
import { ease, stagger } from "../../theme/motion";
import GameIcon from "../../components/GameIcon";
import AdviceCard from "../../components/AdviceCard";

export const BUILD_CATS = ["runes", "summoners", "starting_items", "skill_order", "first_back", "core_build", "situational_items"];
export const isBuildConflict = (cf: Conflict) => cf.sides.some((s) => s.sources.some((src) => BUILD_CATS.includes(src.category)));

// The 20-second view: what to lock in (most-picked by Master+ one-tricks) and the must-know tips.
export default function CheatSheet({
  capture,
  tips,
  buildConflicts,
  main,
  role,
  ready,
}: {
  capture: Capture | null;
  tips: AdviceItem[];
  buildConflicts: number;
  main: string;
  role: Role;
  ready: boolean;
}) {
  const reveal = (i: number) => ({
    initial: { opacity: 0, y: 12 },
    animate: ready ? { opacity: 1, y: 0 } : {},
    transition: { duration: 0.55, ease: ease.out, delay: ready ? 0.35 + i * stagger.list : 0 },
  });

  return (
    <section aria-labelledby="cheat-title" className="mx-auto mt-6 max-w-[1500px] px-6 lg:px-14">
      <motion.div {...reveal(0)} className="glass grid gap-8 p-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.25fr)] lg:p-7" style={{ borderColor: "rgb(201 165 92 / 0.6)" }}>
        <div>
          <h2 id="cheat-title" className="font-display text-xl text-gold-light">
            Lock in
          </h2>
          {capture ? (
            <>
              <div className="mt-4 flex flex-wrap items-start gap-x-7 gap-y-5">
                <Slot label="Keystone" i={1} reveal={reveal}>
                  <div className="flex items-center gap-3">
                    <span className="relative">
                      <span aria-hidden className="keystone-glow absolute -inset-2 rounded-full" />
                      <GameIcon kind="rune" name={capture.keystones[0].name} size={56} glow />
                    </span>
                    <div className="text-sm">
                      <p className="text-gold-light">{capture.keystones[0].name}</p>
                      <p className="tabular-nums text-steel-dim">{capture.keystones[0].pct}% of games</p>
                      {capture.keystones[1] && capture.keystones[1].pct >= 20 && (
                        <p className="text-steel-dim">
                          or {capture.keystones[1].name} {capture.keystones[1].pct}%
                        </p>
                      )}
                    </div>
                  </div>
                </Slot>
                {capture.summoners[0] && (
                  <Slot label={`Summoners, ${capture.summoners[0].pct}%`} i={2} reveal={reveal}>
                    <div className="flex gap-2">
                      {capture.summoners[0].spells.map((s) => (
                        <GameIcon key={s} kind="spell" name={s} size={44} />
                      ))}
                    </div>
                  </Slot>
                )}
                {capture.starting_items && (
                  <Slot label={`Start, ${capture.starting_items.pct}%`} i={3} reveal={reveal}>
                    <div className="flex gap-2">
                      {capture.starting_items.items.map((s, k) => (
                        <GameIcon key={s + k} kind="item" name={s} size={44} />
                      ))}
                    </div>
                  </Slot>
                )}
                {capture.first_item && (
                  <Slot label={`First item, ${capture.first_item.pct}%`} i={4} reveal={reveal}>
                    <div className="flex gap-2">
                      {capture.first_item.items.map((s) => (
                        <GameIcon key={s} kind="item" name={s} size={44} />
                      ))}
                    </div>
                  </Slot>
                )}
                {capture.popular_boots[0] && (
                  <Slot label={`Boots, ${capture.popular_boots[0].pct}%`} i={5} reveal={reveal}>
                    <GameIcon kind="item" name={capture.popular_boots[0].item} size={44} />
                  </Slot>
                )}
                <Slot label="Skill max" i={6} reveal={reveal}>
                  <div className="flex items-center gap-1.5">
                    {capture.skill_max_order.split("").map((k, idx) => (
                      <span key={k} className="flex items-center gap-1.5">
                        {idx > 0 && <span className="text-steel-dim">›</span>}
                        <GameIcon kind="ability" name={`${main}:${k}`} size={36} />
                      </span>
                    ))}
                  </div>
                </Slot>
              </div>
              <p className="mt-5 text-xs text-steel-dim">
                Most-picked by Master+ Garen one-tricks on onetricks.gg, patches {capture.patches}.
              </p>
              {buildConflicts > 0 && (
                <a href="#build" className="mt-1.5 inline-block text-sm text-amber hover:underline">
                  Sources disagree on {buildConflicts} build choice{buildConflicts === 1 ? "" : "s"}: see the build section.
                </a>
              )}
            </>
          ) : (
            <p className="mt-4 text-steel-dim">No one-trick build data captured for this {role} matchup yet.</p>
          )}
        </div>

        <div>
          <h2 className="font-display text-xl text-gold-light">Remember</h2>
          {tips.length ? (
            <div className="mt-4 space-y-2.5">
              {tips.map((t, i) => (
                <motion.div key={i} {...reveal(7 + i)}>
                  <AdviceCard it={t} compact />
                </motion.div>
              ))}
            </div>
          ) : (
            <p className="mt-4 max-w-[var(--measure)] text-steel-dim">
              No matchup-specific tips yet. The laning sections below show the general Garen {role} plan.
            </p>
          )}
        </div>
      </motion.div>
    </section>
  );
}

function Slot({ label, i, reveal, children }: { label: string; i: number; reveal: (i: number) => object; children: React.ReactNode }) {
  return (
    <motion.div {...reveal(i)}>
      <p className="mb-2 text-xs text-steel-dim">{label}</p>
      {children}
    </motion.div>
  );
}
