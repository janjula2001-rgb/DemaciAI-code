import { motion } from "motion/react";

// A small arrow that draws itself (pathLength) after the item before it has appeared.
export default function Arrow({ delay = 0 }: { delay?: number }) {
  return (
    <svg width="34" height="16" viewBox="0 0 34 16" fill="none" aria-hidden className="shrink-0 self-center">
      <motion.path
        d="M2 8 H30 M24 3 L31 8 L24 13"
        stroke="var(--gold)"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        variants={{ hidden: { pathLength: 0, opacity: 0 }, shown: { pathLength: 1, opacity: 1, transition: { duration: 0.35, delay, ease: "easeOut" } } }}
      />
    </svg>
  );
}
