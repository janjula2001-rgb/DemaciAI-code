import { Link } from "react-router";
import { motion, useReducedMotion } from "motion/react";
import { champ } from "../../data/assetPaths";
import type { Matchup } from "../../data/types";
import { ease } from "../../theme/motion";
import { focusPosition, leftBox, rightBox } from "../../theme/split";
import CountUp from "../../components/CountUp";
import RichText from "../../components/RichText";
import DifficultyMeter from "./DifficultyMeter";


// Both splashes in a diagonal split (same geometry as the VS intro, so the intro settles into it),
// portraits + VS on the seam (the intro's flying elements land on [data-morph] targets),
// then a glass strip with difficulty, summary and Platinum+ numbers.
export default function MatchupHeader({ m, main, enemyName, ready, introPlaying }: { m: Matchup; main: string; enemyName: string; ready: boolean; introPlaying: boolean }) {
  const reduced = useReducedMotion();
  const sentences = m.summary.match(/[^.!?]+[.!?]+(\s|$)/g) ?? [m.summary];
  const stats = m.stats;
  const elo = stats?.elo_filter ? stats.elo_filter.replace(/^\w/, (c) => c.toUpperCase()) : "Platinum+";
  const hiddenWhileIntro = { opacity: introPlaying ? 0 : 1 };

  return (
    <header className="relative">
      <div className="relative h-[min(58vh,600px)] min-h-[420px] overflow-hidden">
        <motion.div
          className="absolute inset-y-0"
          style={leftBox}
          initial={reduced ? false : { x: -60, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.9, ease: ease.out }}
        >
          <img src={champ.splash(main)} srcSet={champ.splashSrcSet(main)} sizes="100vw" alt="" className="h-full w-full object-cover" style={{ objectPosition: focusPosition(main) }} />
        </motion.div>
        <motion.div
          className="absolute inset-y-0"
          style={rightBox}
          initial={reduced ? false : { x: 60, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.9, ease: ease.out }}
        >
          <img src={champ.splash(m.enemy)} srcSet={champ.splashSrcSet(m.enemy)} sizes="100vw" alt="" className="h-full w-full object-cover" style={{ objectPosition: focusPosition(m.enemy) }} />
        </motion.div>
        <svg className="absolute inset-0 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden>
          <line x1="58" y1="0" x2="42" y2="100" stroke="var(--gold)" strokeWidth="3" vectorEffect="non-scaling-stroke" />
        </svg>
        {/* scrims: readable names at the bottom, darker outer edges */}
        <div className="absolute inset-0 bg-[linear-gradient(180deg,rgb(6_10_19/0.55)_0%,transparent_22%,transparent_50%,var(--night)_100%)]" />
        <div className="absolute inset-0 bg-[linear-gradient(90deg,rgb(6_10_19/0.6),transparent_25%,transparent_75%,rgb(6_10_19/0.6))]" />

        <Link
          to={`/?role=${m.role}`}
          className="glass glass-blur absolute left-6 top-6 z-10 flex items-center gap-2 px-4 py-2 text-sm text-steel transition-colors hover:text-gold-light lg:left-14"
        >
          <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
            <path d="m15 18-6-6 6-6" />
          </svg>
          Matchups
          <kbd className="ml-1 rounded border border-[var(--gold-line)] px-1 text-[0.7rem] text-steel-dim">Esc</kbd>
        </Link>

        {/* names on their own side, portraits + VS on the seam */}
        <div className="absolute inset-x-0 bottom-28 flex items-end justify-between px-6 lg:px-14">
          <h1 className="sr-only">
            Garen vs {enemyName}, {m.role} lane
          </h1>
          <p aria-hidden className="font-display text-[clamp(2.4rem,4.6vw,4.6rem)] leading-none text-gold-light [text-shadow:0_4px_30px_rgb(0_0_0/0.75)]">
            {main}
          </p>
          <p aria-hidden className="font-display text-right text-[clamp(2.4rem,4.6vw,4.6rem)] leading-none text-gold-light [text-shadow:0_4px_30px_rgb(0_0_0/0.75)]">
            {enemyName}
          </p>
        </div>
        <div className="absolute bottom-24 left-1/2 flex -translate-x-1/2 items-center gap-5" aria-hidden>
          <Portrait id={main} morph="main-portrait" style={hiddenWhileIntro} />
          <span data-morph="vs" className="font-display text-4xl font-bold text-gold-light [text-shadow:0_0_24px_rgb(201_165_92/0.8)]" style={hiddenWhileIntro}>
            VS
          </span>
          <Portrait id={m.enemy} morph="enemy-portrait" style={hiddenWhileIntro} />
        </div>
      </div>

      {/* info strip overlapping the art */}
      <div className="relative z-10 mx-auto -mt-16 grid max-w-[1500px] gap-6 px-6 lg:grid-cols-[minmax(0,1.7fr)_minmax(320px,1fr)] lg:px-14">
        <motion.section
          className="glass glass-blur p-6 lg:p-7"
          initial={{ opacity: 0, y: 24 }}
          animate={ready ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7, ease: ease.out }}
          aria-label="Summary"
        >
          <DifficultyMeter value={m.difficulty} start={ready} />
          <p className="mt-5 max-w-[var(--measure)] text-[1.12rem] leading-[1.7] text-gold-light/95">
            {sentences.map((s, i) => (
              <motion.span
                key={i}
                initial={{ opacity: 0 }}
                animate={ready ? { opacity: 1 } : {}}
                transition={{ duration: 0.6, ease: ease.out, delay: ready ? 0.25 + i * 0.12 : 0 }}
              >
                <RichText text={s} />
              </motion.span>
            ))}
          </p>
          <p className="mt-4 max-w-[var(--measure)] text-sm leading-relaxed text-steel-dim">{m.difficulty_basis}</p>
        </motion.section>

        <motion.section
          className="glass glass-blur flex flex-col gap-5 self-start p-6 lg:p-7"
          initial={{ opacity: 0, y: 24 }}
          animate={ready ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7, ease: ease.out, delay: 0.1 }}
          aria-label="Platinum+ statistics"
        >
          <div>
            <h2 className="font-display text-base text-gold">{elo} win rate</h2>
            <div className="mt-3 grid grid-cols-2 gap-4">
              {(["ugg", "lolalytics"] as const).map((k) => {
                const s = stats?.[k];
                return (
                  <div key={k}>
                    <p className="font-display text-[2.1rem] leading-none text-gold-light">
                      {s?.win_rate != null ? <CountUp value={s.win_rate} decimals={1} suffix="%" start={ready} /> : "–"}
                    </p>
                    <p className="mt-1.5 text-xs text-steel-dim">
                      {k === "ugg" ? "u.gg" : "lolalytics"}
                      {s?.games != null && (
                        <>
                          {", "}
                          <CountUp value={s.games} start={ready} /> games
                        </>
                      )}
                    </p>
                  </div>
                );
              })}
            </div>
            {stats?.small_sample && <p className="mt-3 text-xs text-amber">Small sample: read these numbers loosely.</p>}
            <p className="mt-3 text-xs text-steel-dim">A sanity check from {elo} games on patch {m.generated_at_patch_display}, not advice.</p>
          </div>
          <div className="border-t border-[var(--gold-line)] pt-4">
            <h2 className="font-display text-base text-gold">Last kit changes</h2>
            <ul className="mt-2 space-y-1.5 text-sm">
              {Object.entries(m.last_kit_change).map(([cid, k]) => (
                <li key={cid}>
                  <span className="text-gold-light">{cid === m.enemy ? enemyName : cid}</span>
                  <span className="text-steel-dim">
                    {k.last_mechanic_change ? `: ${k.last_mechanic_change.section}, patch ${k.last_mechanic_change.patch}` : ": no mechanic change on record"}
                    {k.kit_baseline?.kind && k.kit_baseline.kind !== "release" ? ` (${k.kit_baseline.kind} ${k.kit_baseline.patch})` : ""}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </motion.section>
      </div>
    </header>
  );
}

function Portrait({ id, morph, style }: { id: string; morph: string; style: React.CSSProperties }) {
  return (
    <img
      data-morph={morph}
      src={champ.icon(id)}
      alt=""
      className="h-[84px] w-[84px] rounded-full border-[3px] border-gold shadow-[var(--glow-gold)]"
      style={style}
    />
  );
}
