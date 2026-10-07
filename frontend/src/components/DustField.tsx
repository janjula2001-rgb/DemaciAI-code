import { useEffect, useRef } from "react";
import { motion, useReducedMotion, useSpring, useTransform } from "motion/react";
import { pointer } from "../lib/pointer";
import { softSpring } from "../theme/motion";

// Ambient gold dust: ~60 soft motes drifting upward, drawn from one pre-rendered sprite.
// Pauses when the tab is hidden; off entirely with reduced motion.
const COUNT = 60;

interface Mote {
  x: number;
  y: number;
  r: number;
  vy: number;
  sway: number;
  phase: number;
  twinkle: number;
}

export default function DustField({ depth = 26 }: { depth?: number }) {
  const ref = useRef<HTMLCanvasElement>(null);
  const reduced = useReducedMotion();
  const x = useSpring(useTransform(pointer.nx, (v) => v * -depth), softSpring);
  const y = useSpring(useTransform(pointer.ny, (v) => v * -depth), softSpring);

  useEffect(() => {
    if (reduced) return;
    const canvas = ref.current!;
    const ctx = canvas.getContext("2d")!;
    const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    let w = 0;
    let h = 0;
    const resize = () => {
      w = canvas.clientWidth;
      h = canvas.clientHeight;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    window.addEventListener("resize", resize);

    const sprite = document.createElement("canvas");
    sprite.width = sprite.height = 64;
    const s = sprite.getContext("2d")!;
    const g = s.createRadialGradient(32, 32, 0, 32, 32, 32);
    g.addColorStop(0, "rgba(255,236,190,1)");
    g.addColorStop(0.25, "rgba(232,200,130,0.65)");
    g.addColorStop(1, "rgba(201,165,92,0)");
    s.fillStyle = g;
    s.fillRect(0, 0, 64, 64);

    const rand = (a: number, b: number) => a + Math.random() * (b - a);
    const spawn = (anywhere: boolean): Mote => ({
      x: rand(0, w),
      y: anywhere ? rand(0, h) : h + 20,
      r: rand(0.8, 2.6) * (Math.random() < 0.12 ? 2.2 : 1),
      vy: rand(6, 20),
      sway: rand(8, 26),
      phase: rand(0, Math.PI * 2),
      twinkle: rand(0.6, 1.8),
    });
    const motes = Array.from({ length: COUNT }, () => spawn(true));

    let raf = 0;
    let last = performance.now();
    const frame = (now: number) => {
      const dt = Math.min((now - last) / 1000, 0.05);
      last = now;
      ctx.clearRect(0, 0, w, h);
      ctx.globalCompositeOperation = "lighter";
      for (let i = 0; i < motes.length; i++) {
        const m = motes[i];
        m.y -= m.vy * dt;
        m.phase += dt * 0.6;
        if (m.y < -20) motes[i] = spawn(false);
        const alpha = 0.35 + 0.35 * Math.sin(now / 1000 * m.twinkle + m.phase);
        const size = m.r * 6;
        ctx.globalAlpha = Math.max(0, alpha) * Math.min(1, m.y / (h * 0.25));
        ctx.drawImage(sprite, m.x + Math.sin(m.phase) * m.sway - size / 2, m.y - size / 2, size, size);
      }
      raf = requestAnimationFrame(frame);
    };
    const onVisibility = () => {
      cancelAnimationFrame(raf);
      if (!document.hidden) {
        last = performance.now();
        raf = requestAnimationFrame(frame);
      }
    };
    raf = requestAnimationFrame(frame);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [reduced]);

  if (reduced) return null;
  return (
    <motion.canvas
      ref={ref}
      aria-hidden
      className="pointer-events-none absolute -inset-8 h-[calc(100%+4rem)] w-[calc(100%+4rem)]"
      style={{ x, y }}
    />
  );
}
