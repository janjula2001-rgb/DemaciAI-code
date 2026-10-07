import { motionValue, type MotionValue } from "motion/react";

// One window-level pointer listener shared by every parallax layer and the cursor glow.
// px/py: pointer position in pixels; nx/ny: normalised to -1..1 from the viewport centre.
export const pointer = {
  px: motionValue(-9999),
  py: motionValue(-9999),
  nx: motionValue(0),
  ny: motionValue(0),
};

let attached = false;
export function attachPointer() {
  if (attached || typeof window === "undefined") return;
  attached = true;
  window.addEventListener(
    "pointermove",
    (e) => {
      pointer.px.set(e.clientX);
      pointer.py.set(e.clientY);
      pointer.nx.set((e.clientX / window.innerWidth) * 2 - 1);
      pointer.ny.set((e.clientY / window.innerHeight) * 2 - 1);
    },
    { passive: true },
  );
}

export type Pointer = Record<keyof typeof pointer, MotionValue<number>>;
