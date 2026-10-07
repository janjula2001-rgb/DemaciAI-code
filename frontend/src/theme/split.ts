import { DEFAULT_FOCUS, SPLASH_FOCUS } from "./splashFocus";

// Diagonal split shared by the VS intro and the matchup header: the seam runs from 58% (top) to 42% (bottom).
// Each splash sits in its own 58%-wide box (so it crops to its half, faces stay visible) and is clipped there.
export const SEAM = { top: 58, bottom: 42 };
const W = SEAM.top; // box width in % of the stage
export const leftBox = { left: "0%", width: `${W}%`, clipPath: `polygon(0 0, 100% 0, ${(SEAM.bottom / W) * 100}% 100%, 0 100%)` };
export const rightBox = {
  left: `${SEAM.bottom}%`,
  width: `${W}%`,
  clipPath: `polygon(${((SEAM.top - SEAM.bottom) / W) * 100}% 0, 100% 0, 100% 100%, 0 100%)`,
};
export const focusPosition = (id: string) => {
  const f = SPLASH_FOCUS[id] ?? DEFAULT_FOCUS;
  return `${f.x * 100}% ${f.y * 100}%`;
};
