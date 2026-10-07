import { useEffect, useState } from "react";
import { motion, useReducedMotion, useSpring } from "motion/react";
import { pointer } from "../lib/pointer";

// Subtle light that follows a fine pointer (mouse/pen only, off with reduced motion).
export function CursorGlow() {
  const reduced = useReducedMotion();
  const [fine, setFine] = useState(false);
  useEffect(() => {
    setFine(window.matchMedia("(pointer: fine)").matches);
  }, []);
  const x = useSpring(pointer.px, { stiffness: 260, damping: 30, mass: 0.4 });
  const y = useSpring(pointer.py, { stiffness: 260, damping: 30, mass: 0.4 });
  if (!fine || reduced) return null;
  return (
    <motion.div
      aria-hidden
      className="pointer-events-none fixed left-0 top-0 z-50 h-[520px] w-[520px] rounded-full mix-blend-screen"
      style={{
        x,
        y,
        translateX: "-50%",
        translateY: "-50%",
        background: "radial-gradient(closest-side, rgb(234 215 166 / 0.10), rgb(121 184 255 / 0.04) 55%, transparent)",
      }}
    />
  );
}

// Film grain over everything, so flat panels and gradients don't band.
const GRAIN =
  "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .9 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>\")";

export function NoiseOverlay() {
  return (
    <div
      aria-hidden
      className="pointer-events-none fixed inset-0 z-40 opacity-[0.045] mix-blend-overlay"
      style={{ backgroundImage: GRAIN }}
    />
  );
}

// Riot's fan-project notice (required by their Legal Jibber Jabber policy).
export function RiotFooter({ className = "" }: { className?: string }) {
  return (
    <p className={`text-[0.72rem] leading-snug text-steel-dim/80 ${className}`}>
      Garen Companion isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone
      officially involved in producing or managing Riot Games properties. Riot Games and all associated properties are
      trademarks or registered trademarks of Riot Games, Inc.
    </p>
  );
}
