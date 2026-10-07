import { lazy, Suspense, useEffect } from "react";
import { Route, Routes, useLocation, useNavigate } from "react-router";
import { AnimatePresence, LayoutGroup, motion, MotionConfig } from "motion/react";
import { loadManifest } from "./data/api";
import { attachPointer } from "./lib/pointer";
import { ease } from "./theme/motion";
import { CursorGlow, NoiseOverlay } from "./components/Atmosphere";
import VsIntro from "./components/VsIntro";
import HomeScreen from "./screens/home/HomeScreen";
// the matchup and freshness screens (GSAP, build components) load on first visit, keeping the home bundle small
const MatchupScreen = lazy(() => import("./screens/matchup/MatchupScreen"));
const FreshnessScreen = lazy(() => import("./screens/freshness/FreshnessScreen"));

// Every route fades + drifts in and out with the same curve.
function RouteFade({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.45, ease: ease.inout }}
    >
      <Suspense fallback={<div className="skeleton h-[min(58vh,600px)] min-h-[420px]" />}>{children}</Suspense>
    </motion.div>
  );
}

export default function App() {
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    attachPointer();
    // the theme follows the main champion (config.yaml -> ui_theme)
    loadManifest()
      .then((m) => (document.documentElement.dataset.theme = m.theme))
      .catch(() => {});
  }, []);

  // Esc goes back from any inner screen (the VS intro and search handle Esc themselves first)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && location.pathname !== "/" && !e.defaultPrevented) navigate("/");
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [location.pathname, navigate]);

  return (
    <MotionConfig reducedMotion="user">
      <LayoutGroup>
        <AnimatePresence mode="wait">
          <Routes location={location} key={location.pathname}>
            <Route path="/" element={<RouteFade><HomeScreen /></RouteFade>} />
            <Route path="/freshness" element={<RouteFade><FreshnessScreen /></RouteFade>} />
            <Route path="/:role/:enemy" element={<RouteFade><MatchupScreen /></RouteFade>} />
          </Routes>
        </AnimatePresence>
      </LayoutGroup>
      <VsIntro />
      <CursorGlow />
      <NoiseOverlay />
    </MotionConfig>
  );
}
