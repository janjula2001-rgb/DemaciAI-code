import { useEffect, useRef } from "react";
import { animate, useReducedMotion } from "motion/react";

// Number that counts up from zero once `start` is true (final value immediately with reduced motion).
// Writes textContent directly: no React re-render per frame.
export default function CountUp({ value, decimals = 0, suffix = "", start = true, duration = 1.1 }: { value: number; decimals?: number; suffix?: string; start?: boolean; duration?: number }) {
  const ref = useRef<HTMLSpanElement>(null);
  const reduced = useReducedMotion();
  const fmt = (v: number) => v.toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals }) + suffix;

  useEffect(() => {
    if (!ref.current) return;
    if (reduced) {
      ref.current.textContent = fmt(value);
      return;
    }
    if (!start) {
      ref.current.textContent = fmt(0);
      return;
    }
    const controls = animate(0, value, {
      duration,
      ease: [0.16, 1, 0.3, 1],
      onUpdate: (v) => ref.current && (ref.current.textContent = fmt(v)),
    });
    return () => controls.stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, start, reduced]);

  return <span ref={ref} className="tabular-nums" aria-label={fmt(value)} />;
}
