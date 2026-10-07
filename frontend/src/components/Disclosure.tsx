import { useId, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { dur, ease } from "../theme/motion";

// A quiet "show more" toggle; the content fades and lifts in (opacity/transform only).
export default function Disclosure({ label, children }: { label: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const id = useId();
  return (
    <div className="mt-6">
      <button onClick={() => setOpen((o) => !o)} aria-expanded={open} aria-controls={id} className="flex items-center gap-2 text-sm text-steel-dim hover:text-gold-light">
        <motion.svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" animate={{ rotate: open ? 90 : 0 }} transition={{ duration: dur.quick }} aria-hidden>
          <path d="m9 6 6 6-6 6" />
        </motion.svg>
        {label}
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div id={id} initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6, transition: { duration: dur.instant } }} transition={{ duration: dur.quick, ease: ease.out }} className="mt-3">
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
