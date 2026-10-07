import { useEffect, useRef, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { NAV } from "./sections";
import { spring } from "../../theme/motion";

gsap.registerPlugin(ScrollTrigger);

// Sticky game-phase timeline: the gold bar fills with scroll progress through the sections
// (ScrollTrigger scrub), the active phase is highlighted, clicking scrolls to it.
export default function PhaseNav({ containerId }: { containerId: string }) {
  const bar = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState(NAV[0].id);
  const reduced = useReducedMotion();

  useEffect(() => {
    const container = document.getElementById(containerId);
    if (!container || !bar.current) return;
    const ctx = gsap.context(() => {
      gsap.fromTo(
        bar.current,
        { scaleX: 0 },
        { scaleX: 1, ease: "none", scrollTrigger: { trigger: container, start: "top 30%", end: "bottom 70%", scrub: 0.4 } },
      );
      for (const { id } of NAV) {
        const el = document.getElementById(id);
        if (el) ScrollTrigger.create({ trigger: el, start: "top 45%", end: "bottom 45%", onToggle: (self) => self.isActive && setActive(id) });
      }
    });
    // images above load late and shift the layout; measure again once they have
    const t = setTimeout(() => ScrollTrigger.refresh(), 800);
    window.addEventListener("load", () => ScrollTrigger.refresh(), { once: true });
    return () => {
      clearTimeout(t);
      ctx.revert();
    };
  }, [containerId]);

  const go = (id: string) => document.getElementById(id)?.scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "start" });

  return (
    <nav aria-label="Game phases" className="sticky top-0 z-30 mt-10 border-y border-[var(--gold-line)] bg-[var(--glass-strong)] backdrop-blur-xl">
      <div className="mx-auto flex max-w-[1500px] items-center gap-1 overflow-x-auto px-6 [scrollbar-width:none] lg:px-14">
        {NAV.map(({ id, nav }, i) => (
          <button
            key={id}
            onClick={() => go(id)}
            aria-current={active === id ? "true" : undefined}
            className={`relative shrink-0 px-3.5 py-3.5 text-sm transition-colors duration-[var(--t-quick)] ${active === id ? "text-gold-light" : "text-steel-dim hover:text-steel"}`}
          >
            {i > 1 && i < NAV.length - 1 && <span className="mr-1.5 text-xs tabular-nums text-gold/60">{i - 1}</span>}
            {nav}
            {active === id && <motion.span layoutId="phase-active" transition={spring} className="absolute inset-x-2 bottom-0 h-[2px] rounded-full bg-gold shadow-[var(--glow-gold)]" />}
          </button>
        ))}
      </div>
      <div className="h-[2px] bg-[rgb(174_184_199/0.1)]">
        <div ref={bar} className="h-full origin-left scale-x-0 bg-[linear-gradient(90deg,var(--frost),var(--gold))]" />
      </div>
    </nav>
  );
}
