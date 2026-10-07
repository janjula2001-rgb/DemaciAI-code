import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { useAssets, useManifest } from "../../data/api";
import type { Role } from "../../data/types";
import { fuzzyFilter } from "../../lib/fuzzy";
import { intro } from "../../lib/transition";
import { ease } from "../../theme/motion";
import { RiotFooter } from "../../components/Atmosphere";
import ParallaxSplash from "./ParallaxSplash";
import RoleToggle from "./RoleToggle";
import SearchBox from "./SearchBox";
import ChampionTile from "./ChampionTile";

const ROLE_KEY = "garen.role";
const readRole = (): Role => {
  try {
    return localStorage.getItem(ROLE_KEY) === "mid" ? "mid" : "top";
  } catch {
    return "top";
  }
};

export default function HomeScreen() {
  const { data: manifest, error } = useManifest();
  const { data: assets } = useAssets();
  const reduced = useReducedMotion();
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const role: Role = (params.get("role") as Role) || readRole();
  const [query, setQuery] = useState("");
  const [staggerIn, setStaggerIn] = useState(true);
  const search = useRef<HTMLInputElement>(null);

  const main = manifest?.main_champion ?? "Garen";
  const rows = useMemo(() => fuzzyFilter(manifest?.roles[role] ?? [], query, (r) => r.name), [manifest, role, query]);

  const setRole = (r: Role) => {
    try {
      localStorage.setItem(ROLE_KEY, r);
    } catch {
      /* private mode: role just isn't remembered */
    }
    setStaggerIn(true);
    setParams({ role: r }, { replace: true });
  };

  // "/" focuses search from anywhere on the screen
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "/" && document.activeElement !== search.current) {
        e.preventDefault();
        search.current?.focus();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // after the entrance stagger, filtering should feel instant
  useEffect(() => {
    if (!staggerIn) return;
    const t = setTimeout(() => setStaggerIn(false), 900);
    return () => clearTimeout(t);
  }, [staggerIn, role]);

  const title = assets?.champions[main]?.title;
  const letters = main.toUpperCase().split("");

  return (
    <main className="relative min-h-screen">
      <ParallaxSplash champion={main} />

      <div className="relative z-10 mx-auto grid min-h-screen max-w-[1760px] grid-cols-1 gap-8 px-6 py-8 lg:grid-cols-[minmax(0,1fr)_minmax(520px,600px)] lg:px-14 lg:py-10">
        {/* Title block */}
        <section className="flex flex-col justify-end pb-6 lg:pb-16">
          <h1 aria-label={main} className="font-display flex text-[length:var(--text-display)] font-bold leading-[0.9] text-gold-light [text-shadow:0_4px_40px_rgb(201_165_92/0.35)]">
            {letters.map((ch, i) => (
              <motion.span
                key={i}
                aria-hidden
                initial={reduced ? { opacity: 0 } : { y: "0.35em", opacity: 0 }}
                animate={{ y: "0em", opacity: 1 }}
                transition={{ duration: reduced ? 0.2 : 0.9, ease: ease.out, delay: reduced ? 0 : 0.35 + i * 0.06 }}
                className="inline-block"
              >
                {ch}
              </motion.span>
            ))}
          </h1>
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: ease.out, delay: reduced ? 0 : 0.8 }}
            className="mt-4 max-w-[34rem]"
          >
            {title && <p className="font-display text-xl text-steel">{title[0].toUpperCase() + title.slice(1)}</p>}
            <div className="mt-5 h-px w-40 origin-left bg-[linear-gradient(90deg,var(--gold),transparent)]" />
            <p className="mt-5 text-lg text-steel">Pick who you're laning against.</p>
            {manifest && (
              <p className="mt-1 text-sm text-steel-dim">
                Built on patch {manifest.patch.display}.{" "}
                <Link to="/freshness" className="text-frost hover:underline">
                  Data freshness
                </Link>
              </p>
            )}
          </motion.div>
          <RiotFooter className="mt-10 max-w-[40rem]" />
        </section>

        {/* Picker panel */}
        <motion.section
          aria-label="Pick an enemy"
          initial={{ opacity: 0, x: reduced ? 0 : 40 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.9, ease: ease.out, delay: reduced ? 0 : 0.5 }}
          className="glass glass-blur flex max-h-[calc(100vh-5rem)] flex-col overflow-hidden lg:sticky lg:top-10"
        >
          <div className="flex flex-col gap-4 border-b border-[var(--gold-line)] p-5">
            <div className="flex items-center justify-between gap-4">
              <h2 className="font-display text-xl text-gold-light">Matchups</h2>
              {manifest && (
                <RoleToggle role={role} counts={{ top: manifest.roles.top.length, mid: manifest.roles.mid.length }} onChange={setRole} />
              )}
            </div>
            <SearchBox ref={search} value={query} onChange={setQuery} onSubmit={() => {
                if (!rows[0]) return;
                intro.start({ role, enemy: rows[0].id, from: null });
                navigate(`/${role}/${rows[0].id}`);
              }} />
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-4 [scrollbar-color:var(--gold-line)_transparent] [scrollbar-width:thin]">
            {error && <p className="p-4 text-amber">Couldn't load the matchup list: {error}. Run scripts/export_frontend.py.</p>}
            {!manifest && !error && (
              <div className="grid grid-cols-[repeat(auto-fill,minmax(88px,1fr))] gap-x-2 gap-y-3">
                {Array.from({ length: 24 }, (_, i) => (
                  <div key={i} className="flex flex-col items-center gap-2 p-1.5">
                    <div className="skeleton h-[72px] w-[72px] rounded-[var(--radius-icon)]" />
                    <div className="skeleton h-3 w-14 rounded" />
                  </div>
                ))}
              </div>
            )}
            {manifest && (
              <motion.div layout className="grid grid-cols-[repeat(auto-fill,minmax(88px,1fr))] gap-x-2 gap-y-3">
                <AnimatePresence mode="popLayout">
                  {rows.map((row, i) => (
                    <ChampionTile key={`${role}-${row.id}`} row={row} role={role} index={i} staggerIn={staggerIn} />
                  ))}
                </AnimatePresence>
              </motion.div>
            )}
            {manifest && rows.length === 0 && (
              <p className="px-2 py-8 text-center text-steel-dim">
                No {role} matchup matches "{query}". Press Esc to clear the search.
              </p>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-[var(--gold-line)] px-5 py-3 text-xs text-steel-dim">
            <Legend color="var(--diff-easy)" ring label="Easy" />
            <Legend color="var(--diff-medium)" ring label="Medium" />
            <Legend color="var(--diff-hard)" ring label="Hard" />
            <span className="mx-1 h-3 w-px bg-[var(--gold-line)]" />
            <Legend color="var(--fresh-green)" label="Current" />
            <Legend color="var(--fresh-amber)" label="Some tips old" />
            <Legend color="var(--fresh-orange)" label="Needs refresh" />
          </div>
        </motion.section>
      </div>
    </main>
  );
}

function Legend({ color, label, ring = false }: { color: string; label: string; ring?: boolean }) {
  return (
    <span className="flex items-center gap-1.5">
      <span
        className={ring ? "h-2.5 w-2.5 rounded-[3px]" : "h-2 w-2 rounded-full"}
        style={ring ? { boxShadow: `inset 0 0 0 2px ${color}` } : { background: color }}
      />
      {label}
    </span>
  );
}

