import { useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { AnimatePresence, motion } from "motion/react";
import { dur, ease } from "../theme/motion";

// Hover/focus tooltip rendered in a portal (never clipped by scrolling panels), placed above the
// trigger and flipped below near the top edge. Fades and lifts in with the quick token.
export default function Tooltip({ content, children, className = "" }: { content: React.ReactNode; children: React.ReactNode; className?: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const tip = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState<{ x: number; y: number; below: boolean } | null>(null);

  useLayoutEffect(() => {
    if (!open || !ref.current) return;
    const r = ref.current.getBoundingClientRect();
    const h = tip.current?.offsetHeight ?? 120;
    const w = tip.current?.offsetWidth ?? 280;
    const below = r.top - h - 12 < 8;
    const x = Math.min(Math.max(r.left + r.width / 2, w / 2 + 8), window.innerWidth - w / 2 - 8);
    setPos({ x, y: below ? r.bottom + 10 : r.top - 10, below });
  }, [open]);

  return (
    <span
      ref={ref}
      className={`inline-flex ${className}`}
      onPointerEnter={() => setOpen(true)}
      onPointerLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)}
      onBlur={() => setOpen(false)}
    >
      {children}
      {createPortal(
        <AnimatePresence>
          {open && (
            <motion.div
              ref={tip}
              role="tooltip"
              initial={{ opacity: 0, y: pos?.below ? -6 : 6, scale: 0.97 }}
              animate={{ opacity: pos ? 1 : 0, y: 0, scale: 1 }}
              exit={{ opacity: 0, transition: { duration: dur.instant } }}
              transition={{ duration: dur.quick, ease: ease.out }}
              className="glass pointer-events-none fixed z-[70] max-w-[300px] px-3.5 py-2.5 text-sm leading-snug text-steel"
              style={{
                left: pos?.x ?? -9999,
                top: pos?.y ?? -9999,
                translateX: "-50%",
                translateY: pos?.below ? "0%" : "-100%",
                background: "var(--glass-strong)",
              }}
            >
              {content}
            </motion.div>
          )}
        </AnimatePresence>,
        document.body,
      )}
    </span>
  );
}
