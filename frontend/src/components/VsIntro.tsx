import { useEffect, useLayoutEffect, useRef } from "react";
import gsap from "gsap";
import { champ } from "../data/assetPaths";
import { useManifest } from "../data/api";
import { intro, useIntro } from "../lib/transition";
import { focusPosition, leftBox, rightBox } from "../theme/split";

// The VS moment between picking an enemy and the matchup page (max ~1.4 s, click or Esc skips):
//  0.00  both splashes slide in from their side, diagonally split; the clicked icon flies to the stage
//  0.34  they meet: gold flash + shockwave ring
//  0.40  "VS" stamps in with a short shake
//  0.95  the stage fades away while VS and both portraits fly to their places in the matchup header
// Only transform/opacity are animated. Off with reduced motion (intro.start ignores the request).
const STAGE_ICON = 132;

export default function VsIntro() {
  const req = useIntro();
  const { data: manifest } = useManifest();
  if (!req) return null;
  const main = manifest?.main_champion ?? "Garen";
  const name = manifest?.roles[req.role].find((r) => r.id === req.enemy)?.name ?? req.enemy;
  return <Stage key={`${req.role}-${req.enemy}`} main={main} enemy={req.enemy} enemyName={name} from={req.from} />;
}

function Stage({ main, enemy, enemyName, from }: { main: string; enemy: string; enemyName: string; from: DOMRect | null }) {
  const root = useRef<HTMLDivElement>(null);
  const tl = useRef<gsap.core.Timeline | null>(null);

  useLayoutEffect(() => {
    const q = gsap.utils.selector(root);
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    // stage positions of the two portraits and the VS mark (centre line, a little below middle)
    const cy = vh * 0.56;
    const gap = Math.min(260, vw * 0.16);

    gsap.set(q("[data-part=left]"), { xPercent: -100 });
    gsap.set(q("[data-part=right]"), { xPercent: 100 });
    gsap.set(q("[data-part=flash], [data-part=seam], [data-part=names]"), { opacity: 0 });
    gsap.set(q("[data-part=ring]"), { scale: 0, opacity: 0.9 });
    gsap.set(q("[data-part=vs]"), { scale: 2.6, opacity: 0 });
    gsap.set(q("[data-part=garen-icon]"), { x: vw / 2 - gap - STAGE_ICON / 2, y: cy - STAGE_ICON / 2, scale: 0, opacity: 0, transformOrigin: "50% 50%" });
    const enemyIcon = q("[data-part=enemy-icon]");
    if (from) {
      // start exactly where the clicked grid icon was
      gsap.set(enemyIcon, { x: from.left, y: from.top, scale: from.width / STAGE_ICON, transformOrigin: "0 0" });
    } else {
      gsap.set(enemyIcon, { x: vw / 2 + gap - STAGE_ICON / 2, y: cy - STAGE_ICON / 2, scale: 0, transformOrigin: "50% 50%" });
    }

    const t = gsap.timeline({ defaults: { ease: "expo.out" }, onComplete: () => intro.finish() });
    t.to(q("[data-part=backdrop]"), { opacity: 1, duration: 0.18, ease: "none" }, 0)
      .to(q("[data-part=left]"), { xPercent: 0, duration: 0.38 }, 0)
      .to(q("[data-part=right]"), { xPercent: 0, duration: 0.38 }, 0)
      .to(enemyIcon, { x: vw / 2 + gap - STAGE_ICON / 2, y: cy - STAGE_ICON / 2, scale: 1, duration: 0.5, ease: "power4.inOut" }, 0)
      .to(q("[data-part=garen-icon]"), { scale: 1, opacity: 1, duration: 0.45, ease: "back.out(1.6)" }, 0.2)
      .to(q("[data-part=seam]"), { opacity: 1, duration: 0.2 }, 0.32)
      .to(q("[data-part=flash]"), { opacity: 0.85, duration: 0.07, ease: "none" }, 0.34)
      .to(q("[data-part=flash]"), { opacity: 0, duration: 0.35, ease: "power2.out" }, 0.41)
      .to(q("[data-part=ring]"), { scale: 4.2, opacity: 0, duration: 0.6, ease: "power2.out" }, 0.34)
      .to(q("[data-part=vs]"), { scale: 1, opacity: 1, duration: 0.24, ease: "back.out(2.2)" }, 0.4)
      .to(q("[data-part=shake]"), { keyframes: { x: [0, -9, 7, -4, 0] }, duration: 0.16, ease: "none" }, 0.62)
      .to(q("[data-part=names]"), { opacity: 1, duration: 0.4 }, 0.5)
      .addLabel("settle", 0.95)
      .to(q("[data-part=fade]"), { opacity: 0, duration: 0.45, ease: "power2.inOut" }, "settle");

    // Fly VS and both portraits into the header's matching elements, measured when the settle starts
    // (the matchup page mounts underneath during the first second).
    t.call(
      () => {
        const fly = (part: string, target: string) => {
          const el = q(`[data-part=${part}]`)[0] as HTMLElement | undefined;
          const dst = document.querySelector<HTMLElement>(`[data-morph=${target}]`);
          if (!el) return;
          if (!dst) {
            gsap.to(el, { opacity: 0, duration: 0.3 });
            return;
          }
          const a = el.getBoundingClientRect();
          const b = dst.getBoundingClientRect();
          gsap.to(el, {
            x: `+=${b.left - a.left + (b.width - a.width) / 2}`,
            y: `+=${b.top - a.top + (b.height - a.height) / 2}`,
            scale: (gsap.getProperty(el, "scale") as number) * (b.width / a.width),
            duration: 0.45,
            ease: "power4.inOut",
            transformOrigin: "50% 50%",
          });
        };
        fly("enemy-icon", "enemy-portrait");
        fly("garen-icon", "main-portrait");
        fly("vs", "vs");
      },
      [],
      "settle",
    );
    t.to({}, { duration: 0.45 }, "settle"); // keep the timeline alive until the fly-in ends
    // debug hook for frame-by-frame screenshots (scripts/screenshot_frontend.py sets it); 1 = normal speed
    t.timeScale((window as unknown as { __introSlowmo?: number }).__introSlowmo ?? 1);
    tl.current = t;
    return () => {
      t.kill();
    };
  }, [from]);

  // click or Esc jumps to the end (the header is already in place underneath)
  useEffect(() => {
    const skip = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      e.preventDefault();
      e.stopImmediatePropagation();
      tl.current?.progress(1);
    };
    window.addEventListener("keydown", skip, true);
    return () => window.removeEventListener("keydown", skip, true);
  }, []);

  const half = "absolute inset-y-0 overflow-hidden";
  return (
    <div
      ref={root}
      className="fixed inset-0 z-[60] cursor-pointer select-none"
      onClick={() => tl.current?.progress(1)}
      role="presentation"
      aria-hidden
    >
      <div data-part="fade" className="absolute inset-0">
        <div data-part="backdrop" className="absolute inset-0 bg-night opacity-0" />
        <div data-part="shake" className="absolute inset-0">
          <div data-part="left" className={half} style={leftBox}>
            <img src={champ.splash(main)} alt="" className="h-full w-full object-cover" style={{ objectPosition: focusPosition(main) }} />
            <div className="absolute inset-0 bg-[linear-gradient(90deg,rgb(6_10_19/0.55),transparent_60%)]" />
          </div>
          <div data-part="right" className={half} style={rightBox}>
            <img src={champ.splash(enemy)} alt="" className="h-full w-full object-cover" style={{ objectPosition: focusPosition(enemy) }} />
            <div className="absolute inset-0 bg-[linear-gradient(270deg,rgb(6_10_19/0.55),transparent_60%)]" />
          </div>
          <svg data-part="seam" className="absolute inset-0 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none">
            <line x1="58" y1="0" x2="42" y2="100" stroke="var(--gold)" strokeWidth="0.35" vectorEffect="non-scaling-stroke" style={{ strokeWidth: 3 }} />
          </svg>
          <div className="absolute inset-0 bg-[radial-gradient(70%_60%_at_50%_56%,transparent,rgb(6_10_19/0.75))]" />
          <div data-part="names" className="absolute inset-x-0 bottom-[12vh] flex justify-between px-[7vw] font-display text-[clamp(2.5rem,5vw,5rem)] text-gold-light [text-shadow:0_4px_30px_rgb(0_0_0/0.7)]">
            <span>{main}</span>
            <span>{enemyName}</span>
          </div>
        </div>
        <div data-part="flash" className="absolute inset-0 bg-[radial-gradient(40%_40%_at_50%_56%,rgb(255_244_214),rgb(201_165_92/0.6)_45%,transparent_75%)]" />
        <div
          data-part="ring"
          className="absolute left-1/2 top-[56%] h-[24vmin] w-[24vmin] -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-gold-light shadow-[0_0_40px_rgb(234_215_166/0.6)]"
        />
      </div>
      {/* these three outlive the fade and fly into the header */}
      <div
        data-part="vs"
        className="absolute left-1/2 top-[56%] -ml-[0.75em] -mt-[0.55em] font-display text-[clamp(5rem,11vw,10rem)] font-bold leading-none text-gold-light [text-shadow:0_0_30px_rgb(234_215_166/0.9),0_0_90px_rgb(201_165_92/0.75),0_6px_24px_rgb(0_0_0/0.8)]"
      >
        VS
      </div>
      <img data-part="garen-icon" src={champ.icon(main)} alt="" className="absolute left-0 top-0 rounded-full border-[3px] border-gold shadow-[var(--glow-gold)]" style={{ width: STAGE_ICON, height: STAGE_ICON }} />
      <img data-part="enemy-icon" src={champ.icon(enemy)} alt="" className="absolute left-0 top-0 rounded-full border-[3px] border-gold shadow-[var(--glow-gold)]" style={{ width: STAGE_ICON, height: STAGE_ICON }} />
    </div>
  );
}
