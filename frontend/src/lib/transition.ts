import { useSyncExternalStore } from "react";
import type { Role } from "../data/types";

// Hand-off between the home grid and the matchup screen: which icon was clicked and where it was,
// so the VS intro can fly that exact icon into the matchup header (a shared-element transition that
// survives the route change). `active` is non-null while the intro plays.
export interface IntroRequest {
  role: Role;
  enemy: string;
  from: DOMRect | null; // null when opened from search (Enter): the icon grows from the stage instead
}

let active: IntroRequest | null = null;
const listeners = new Set<() => void>();
const emit = () => listeners.forEach((l) => l());

export const intro = {
  start(req: IntroRequest) {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    active = req;
    emit();
  },
  finish() {
    active = null;
    emit();
  },
  get: () => active,
};

const subscribe = (l: () => void) => {
  listeners.add(l);
  return () => listeners.delete(l);
};

export const useIntro = () => useSyncExternalStore(subscribe, () => active);
