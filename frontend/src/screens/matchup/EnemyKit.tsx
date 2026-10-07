import { motion } from "motion/react";
import type { MatchupBundle } from "../../data/api";
import type { Role } from "../../data/types";
import { ease } from "../../theme/motion";
import GameIcon from "../../components/GameIcon";
import { AdviceGroup, SectionShell } from "./PhaseSection";
import { items } from "./sections";

const KEYS = ["P", "Q", "W", "E", "R"] as const;

// The enemy's kit as a strip of ability icons, then the advice about which abilities to respect.
export default function EnemyKit({ data, enemyName, role }: { data: MatchupBundle; enemyName: string; role: Role }) {
  const { m, rolePlan, sharedPlan } = data;
  const names = m.ability_names[m.enemy] ?? {};
  return (
    <SectionShell id="kit" title={`${enemyName}'s kit`}>
      <motion.div className="flex flex-wrap gap-5" initial="hidden" whileInView="shown" viewport={{ once: true }}>
        {KEYS.map((k, i) => (
          <motion.div
            key={k}
            className="flex w-[104px] flex-col items-center gap-1.5 text-center"
            variants={{ hidden: { opacity: 0, y: 10 }, shown: { opacity: 1, y: 0, transition: { duration: 0.45, ease: ease.out, delay: i * 0.07 } } }}
          >
            <GameIcon kind="ability" name={`${m.enemy}:${k}`} size={60} />
            <span className="text-xs text-steel-dim">{k === "P" ? "Passive" : k}</span>
            <span className="text-sm leading-tight text-gold-light">{names[k]}</span>
          </motion.div>
        ))}
      </motion.div>
      <div className="mt-8">
        <AdviceGroup
          label="Abilities to respect"
          mine={items(m, "enemy_key_abilities")}
          rolePlan={items(rolePlan, "enemy_key_abilities")}
          shared={items(sharedPlan, "enemy_key_abilities")}
          role={role}
          emptyText="No sourced notes about their abilities for this matchup yet."
        />
      </div>
    </SectionShell>
  );
}
