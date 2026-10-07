import { motion } from "motion/react";
import type { AdviceItem, Role } from "../../data/types";
import { ease, stagger } from "../../theme/motion";
import AdviceCard from "../../components/AdviceCard";

// A section of the matchup page: the title's gold rule draws, then the content rises in once on scroll.
export function SectionShell({ id, title, intro, children }: { id: string; title: string; intro?: React.ReactNode; children: React.ReactNode }) {
  return (
    <section id={id} aria-labelledby={`${id}-title`} className="scroll-mt-20 pt-16">
      <motion.div initial="hidden" whileInView="shown" viewport={{ once: true, margin: "0px 0px -15% 0px" }}>
        <h2 id={`${id}-title`} className="font-display text-[length:var(--text-2xl)] leading-tight text-gold-light">
          {title}
        </h2>
        <motion.div
          className="mt-3 h-px w-48 origin-left bg-[linear-gradient(90deg,var(--gold),transparent)]"
          variants={{ hidden: { scaleX: 0 }, shown: { scaleX: 1, transition: { duration: 0.7, ease: ease.out } } }}
        />
        {intro && (
          <motion.div variants={{ hidden: { opacity: 0 }, shown: { opacity: 1, transition: { duration: 0.6, delay: 0.15 } } }} className="mt-4 max-w-[var(--measure)] text-steel-dim">
            {intro}
          </motion.div>
        )}
        <motion.div
          className="mt-6"
          variants={{ hidden: { opacity: 0, y: 12 }, shown: { opacity: 1, y: 0, transition: { duration: 0.6, ease: ease.out, delay: 0.2 } } }}
        >
          {children}
        </motion.div>
      </motion.div>
    </section>
  );
}

// Matchup advice first; the general Garen plans (role, then shared) below, dimmed and labelled.
export function AdviceGroup({ label, mine, rolePlan, shared, role, emptyText }: { label?: string; mine: AdviceItem[]; rolePlan: AdviceItem[]; shared: AdviceItem[]; role: Role; emptyText?: string }) {
  if (!mine.length && !rolePlan.length && !shared.length && !emptyText) return null;
  return (
    <div className="mt-6 first:mt-0">
      {label && <h3 className="mb-3 font-display text-lg text-gold">{label}</h3>}
      {!mine.length && emptyText && <p className="mb-3 text-steel-dim">{emptyText}</p>}
      <List items={mine} />
      {rolePlan.length > 0 && (
        <>
          <p className={`mb-2 text-sm text-steel-dim ${mine.length ? "mt-5" : ""}`}>From the general Garen {role} plan, true in most {role} matchups</p>
          <List items={rolePlan} general />
        </>
      )}
      {shared.length > 0 && (
        <>
          <p className={`mb-2 text-sm text-steel-dim ${mine.length || rolePlan.length ? "mt-5" : ""}`}>From the general Garen plan, true in most matchups</p>
          <List items={shared} general />
        </>
      )}
    </div>
  );
}

function List({ items, general = false }: { items: AdviceItem[]; general?: boolean }) {
  return (
    <motion.ul
      className="grid gap-3 xl:grid-cols-2"
      initial="hidden"
      whileInView="shown"
      viewport={{ once: true, margin: "0px 0px -10% 0px" }}
      variants={{ shown: { transition: { staggerChildren: stagger.list } } }}
    >
      {items.map((it, i) => (
        <motion.li key={i} variants={{ hidden: { opacity: 0, y: 10 }, shown: { opacity: 1, y: 0, transition: { duration: 0.5, ease: ease.out } } }}>
          <AdviceCard it={it} general={general} />
        </motion.li>
      ))}
    </motion.ul>
  );
}
