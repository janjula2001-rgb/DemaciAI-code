import { useState } from "react";
import { motion, useReducedMotion, useSpring, useTransform } from "motion/react";
import { champ } from "../../data/assetPaths";
import { pointer } from "../../lib/pointer";
import { ease, softSpring } from "../../theme/motion";
import { DEFAULT_FOCUS, SPLASH_FOCUS } from "../../theme/splashFocus";
import DustField from "../../components/DustField";

const WIDTH_VW = 130; // the art is wider than the screen so its focal point can sit where we want it
const FOCUS_AT_VW = 45; // the gap between the title block and the picker panel
const SPLASH_RATIO = 1215 / 717;

// Full-bleed splash: slow Ken Burns on the art, mouse parallax at three depths
// (art moves least, dust most), gradient scrims so text and the panel stay readable.
export default function ParallaxSplash({ champion }: { champion: string }) {
  const reduced = useReducedMotion();
  const [loaded, setLoaded] = useState(false);
  const x = useSpring(useTransform(pointer.nx, (v) => (reduced ? 0 : v * -14)), softSpring);
  const y = useSpring(useTransform(pointer.ny, (v) => (reduced ? 0 : v * -10)), softSpring);
  const focus = SPLASH_FOCUS[champion] ?? DEFAULT_FOCUS;
  const origin = `${focus.x * 100}% ${focus.y * 100}%`;

  return (
    <div className="fixed inset-0 overflow-hidden bg-night" aria-hidden>
      <motion.div className="absolute -inset-6" style={{ x, y }}>
        <motion.div
          className="absolute top-0 h-full"
          style={{
            width: `${WIDTH_VW}vw`,
            minHeight: `calc(${WIDTH_VW}vw / ${SPLASH_RATIO})`,
            left: `${FOCUS_AT_VW - focus.x * WIDTH_VW}vw`,
            // the art may end before the right edge (behind the panel); fade it instead of a hard cut
            maskImage: "linear-gradient(90deg, #000 0%, #000 78%, transparent 100%)",
            WebkitMaskImage: "linear-gradient(90deg, #000 0%, #000 78%, transparent 100%)",
          }}
          initial={{ opacity: 0, scale: 1.12 }}
          animate={loaded ? { opacity: 1, scale: 1 } : {}}
          transition={{ duration: reduced ? 0.2 : 1.6, ease: ease.out }}
        >
          <img
            src={champ.splash(champion)}
            srcSet={champ.splashSrcSet(champion)}
            sizes={`${WIDTH_VW}vw`}
            alt=""
            onLoad={() => setLoaded(true)}
            className="h-full w-full object-cover"
            style={{
              objectPosition: origin,
              transformOrigin: origin,
              animation: reduced ? undefined : "kenburns var(--t-ambient) ease-in-out infinite alternate",
            }}
          />
        </motion.div>
      </motion.div>
      {/* scrims: left for the title, right for the panel, bottom vignette, cold top light */}
      <div className="absolute inset-0 bg-[linear-gradient(90deg,var(--night)_0%,rgb(6_10_19/0.8)_24%,rgb(6_10_19/0.1)_46%,rgb(6_10_19/0.1)_56%,rgb(6_10_19/0.7)_74%,var(--night)_100%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(120%_80%_at_50%_120%,var(--night)_20%,transparent_60%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(60%_40%_at_40%_-10%,rgb(121_184_255/0.14),transparent_70%)]" />
      <DustField />
    </div>
  );
}
