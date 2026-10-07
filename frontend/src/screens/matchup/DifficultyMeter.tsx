import { motion } from "motion/react";
import { diffVar } from "../home/ChampionTile";
import { ease } from "../../theme/motion";

const WORD = ["", "Easy", "Easy", "Medium", "Hard", "Very hard"];

// Five segments that fill one after another (scaleX) once the page is ready.
export default function DifficultyMeter({ value, start }: { value: number; start: boolean }) {
  const color = diffVar(value);
  return (
    <div className="flex items-center gap-4" role="meter" aria-valuemin={1} aria-valuemax={5} aria-valuenow={value} aria-label={`Difficulty ${value} of 5`}>
      <div className="flex gap-1.5">
        {[1, 2, 3, 4, 5].map((i) => (
          <span key={i} className="relative h-2.5 w-9 overflow-hidden rounded-full bg-[rgb(174_184_199/0.14)]">
            {i <= value && (
              <motion.span
                className="absolute inset-0 origin-left rounded-full"
                style={{ background: color, boxShadow: `0 0 12px ${color}` }}
                initial={{ scaleX: 0 }}
                animate={{ scaleX: start ? 1 : 0 }}
                transition={{ duration: 0.45, ease: ease.out, delay: start ? 0.15 + i * 0.12 : 0 }}
              />
            )}
          </span>
        ))}
      </div>
      <span className="font-display text-lg" style={{ color }}>
        {WORD[value]}
      </span>
      <span className="text-sm text-steel-dim">{value} of 5</span>
    </div>
  );
}
