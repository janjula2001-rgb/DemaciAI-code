import { useRef, useState } from "react";
import { Link } from "react-router";
import { motion, useMotionValue, useReducedMotion, useSpring } from "motion/react";
import { champ } from "../../data/assetPaths";
import type { ManifestRow, Role } from "../../data/types";
import { ease, spring, stagger } from "../../theme/motion";
import { intro } from "../../lib/transition";

export const diffVar = (d: number) => (d <= 2 ? "var(--diff-easy)" : d === 3 ? "var(--diff-medium)" : "var(--diff-hard)");
const DIFF_WORD = ["", "easy", "easy", "medium", "hard", "very hard"];
const FRESH_WORD = { green: "up to date", amber: "some tips may be outdated", orange: "needs a refresh" };

// One enemy: difficulty ring, freshness dot, 3D tilt toward the pointer, gold glow on hover.
// Clicking hands the icon's position to the VS intro, which flies it into the matchup header.
export default function ChampionTile({ row, role, index, staggerIn }: { row: ManifestRow; role: Role; index: number; staggerIn: boolean }) {
  const reduced = useReducedMotion();
  const ref = useRef<HTMLAnchorElement>(null);
  const [img, setImg] = useState<"loading" | "ok" | "broken">("loading");
  const icon = useRef<HTMLElement>(null);
  const rx = useSpring(useMotionValue(0), spring);
  const ry = useSpring(useMotionValue(0), spring);

  const tilt = (e: React.PointerEvent) => {
    if (reduced || !ref.current) return;
    const r = ref.current.getBoundingClientRect();
    ry.set(((e.clientX - r.left) / r.width - 0.5) * 20);
    rx.set(-((e.clientY - r.top) / r.height - 0.5) * 20);
  };
  const reset = () => {
    rx.set(0);
    ry.set(0);
  };

  const ring = `0 0 0 2px var(--night), 0 0 0 4px ${diffVar(row.difficulty)}`;
  const label = `${row.name}: ${DIFF_WORD[row.difficulty]} (${row.difficulty}/5), data ${FRESH_WORD[row.freshness.level]}`;
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 14, scale: 0.86 }}
      animate={{ opacity: 1, y: 0, scale: 1, transition: { duration: 0.5, ease: ease.out, delay: staggerIn ? index * stagger.grid : 0 } }}
      exit={{ opacity: 0, scale: 0.86, transition: { duration: 0.18 } }}
      transition={spring}
      style={{ perspective: 600 }}
    >
      <Link
        ref={ref}
        to={`/${role}/${row.id}`}
        aria-label={label}
        title={`${row.name} · ${row.freshness.why}`}
        onPointerMove={tilt}
        onPointerLeave={reset}
        onClick={() => intro.start({ role, enemy: row.id, from: icon.current?.getBoundingClientRect() ?? null })}
        className="group flex flex-col items-center gap-1.5 rounded-[var(--radius-icon)] p-1.5 outline-offset-2"
      >
        <motion.div
          className="relative"
          style={{ rotateX: rx, rotateY: ry, transformStyle: "preserve-3d" }}
          whileHover={reduced ? undefined : { scale: 1.08 }}
          whileTap={{ scale: 0.96 }}
          tabIndex={-1} // Motion makes whileTap elements focusable; the link around it is the tab stop
          transition={spring}
        >
          {/* hover glow: only its opacity animates */}
          <span
            aria-hidden
            className="absolute -inset-2 rounded-[18px] opacity-0 transition-opacity duration-[var(--t-quick)] group-hover:opacity-100 group-focus-visible:opacity-100"
            style={{ boxShadow: `0 0 26px 2px ${diffVar(row.difficulty)}`, background: "radial-gradient(closest-side, rgb(234 215 166 / .18), transparent)" }}
          />
          {img === "broken" ? (
            <motion.div
              ref={icon as React.Ref<HTMLDivElement>}
              className="relative grid h-[72px] w-[72px] place-items-center rounded-[var(--radius-icon)] bg-[var(--rampart)] font-display text-xl text-gold"
              style={{ boxShadow: ring }}
            >
              {row.name.slice(0, 2)}
            </motion.div>
          ) : (
            <motion.img
              ref={icon as React.Ref<HTMLImageElement>}
              src={champ.icon(row.id)}
              srcSet={champ.iconSrcSet(row.id)}
              sizes="72px"
              alt=""
              loading="lazy"
              onLoad={() => setImg("ok")}
              onError={() => setImg("broken")}
              className={`relative h-[72px] w-[72px] rounded-[var(--radius-icon)] object-cover ${img === "loading" ? "skeleton" : ""}`}
              style={{ boxShadow: ring }}
            />
          )}
          <span
            aria-hidden
            className="absolute -bottom-1 -right-1 h-3 w-3 rounded-full border-2 border-[var(--night)]"
            style={{ background: `var(--fresh-${row.freshness.level})` }}
          />
        </motion.div>
        <span className="max-w-[84px] truncate text-[0.8rem] text-steel transition-colors duration-[var(--t-quick)] group-hover:text-gold-light">
          {row.name}
        </span>
      </Link>
    </motion.div>
  );
}
