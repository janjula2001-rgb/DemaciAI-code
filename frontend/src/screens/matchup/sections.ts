import type { AdviceItem, Matchup } from "../../data/types";

// The game-phase timeline: nav label, anchor id, and the claim categories each phase shows (in order).
export interface Phase {
  id: string;
  nav: string;
  title: string;
  cats: { cat: string; label?: string }[];
}

export const PHASES: Phase[] = [
  { id: "lv1-3", nav: "Levels 1–3", title: "Levels 1–3", cats: [{ cat: "laning_1_3" }] },
  { id: "lv3-6", nav: "Levels 3–6", title: "Levels 3–6", cats: [{ cat: "laning_3_6" }, { cat: "wave_management", label: "Wave management" }] },
  { id: "post-6", nav: "Post-6", title: "After level 6", cats: [{ cat: "post_6" }] },
  { id: "mid-game", nav: "Mid game", title: "Mid game and side lane", cats: [{ cat: "midgame" }, { cat: "jungle", label: "Jungle" }] },
  { id: "teamfights", nav: "Teamfights", title: "Teamfights", cats: [{ cat: "teamfight" }] },
];

export const NAV = [
  { id: "build", nav: "Build" },
  { id: "kit", nav: "Their kit" },
  ...PHASES.map((p) => ({ id: p.id, nav: p.nav })),
  { id: "about", nav: "About" },
];

export const items = (m: Matchup | null | undefined, cat: string): AdviceItem[] => ((m?.[cat] as AdviceItem[] | undefined) ?? []);
