import { motion } from "motion/react";
import type { Role } from "../../data/types";
import { spring } from "../../theme/motion";

const LABEL: Record<Role, string> = { top: "Top", mid: "Mid" };

// Segmented control; the gold plate slides between options (shared layoutId).
export default function RoleToggle({ role, counts, onChange }: { role: Role; counts: Record<Role, number>; onChange: (r: Role) => void }) {
  return (
    <div role="radiogroup" aria-label="Role" className="relative flex rounded-full border border-[var(--gold-line)] bg-black/25 p-1">
      {(Object.keys(LABEL) as Role[]).map((r) => {
        const active = r === role;
        return (
          <button
            key={r}
            role="radio"
            aria-checked={active}
            onClick={() => onChange(r)}
            className={`relative z-10 flex items-baseline gap-2 rounded-full px-5 py-1.5 font-display text-[1.05rem] transition-colors duration-[var(--t-quick)] ${
              active ? "text-night" : "text-steel hover:text-gold-light"
            }`}
          >
            {active && (
              <motion.span
                layoutId="role-plate"
                transition={spring}
                className="absolute inset-0 -z-10 rounded-full bg-[linear-gradient(180deg,#e6cd8e,var(--gold))] shadow-[var(--glow-gold)]"
              />
            )}
            {LABEL[r]}
            <span className={`font-body text-xs tabular-nums ${active ? "text-night/70" : "text-steel-dim"}`}>{counts[r]}</span>
          </button>
        );
      })}
    </div>
  );
}
