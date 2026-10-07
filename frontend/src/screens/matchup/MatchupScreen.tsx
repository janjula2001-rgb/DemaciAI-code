import { useEffect } from "react";
import { Link, useParams } from "react-router";
import { useManifest, useMatchupBundle } from "../../data/api";
import type { AdviceItem, Role } from "../../data/types";
import { useIntro } from "../../lib/transition";
import { RiotFooter } from "../../components/Atmosphere";
import { SourcesProvider } from "../../components/SourcesDrawer";
import { AbilityNamesProvider } from "../../components/RichText";
import MatchupHeader from "./MatchupHeader";
import CheatSheet, { isBuildConflict } from "./CheatSheet";
import PhaseNav from "./PhaseNav";
import { AdviceGroup, SectionShell } from "./PhaseSection";
import { items, PHASES } from "./sections";
import BuildSection from "./build/BuildSection";
import EnemyKit from "./EnemyKit";
import AboutMatchup from "./AboutMatchup";

export default function MatchupScreen() {
  const { role, enemy } = useParams() as { role: Role; enemy: string };
  const { data, error } = useMatchupBundle(role, enemy);
  const { data: manifest } = useManifest();
  const introPlaying = useIntro() !== null;
  const ready = !!data && !introPlaying; // entrance animations wait for the VS intro to land

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [role, enemy]);

  const main = manifest?.main_champion ?? "Garen";
  const enemyName = manifest?.roles[role]?.find((r) => r.id === enemy)?.name ?? enemy;

  if (error) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-24">
        <p className="text-amber">Couldn't load Garen vs {enemy} ({role}): {error}. Run scripts/export_frontend.py and reload.</p>
      </main>
    );
  }
  if (!data) return <MatchupSkeleton />;

  const { m, rolePlan, sharedPlan } = data;
  const conflicts = [...m.conflicts, ...(rolePlan?.conflicts ?? [])];
  const buildConflicts = conflicts.filter(isBuildConflict);
  return (
    <AbilityNamesProvider names={m.ability_names}>
      <SourcesProvider>
        <main className="pb-24">
          <MatchupHeader m={m} main={main} enemyName={enemyName} ready={ready} introPlaying={introPlaying} />
          <CheatSheet capture={data.capture} tips={(m.key_tips ?? []) as AdviceItem[]} buildConflicts={buildConflicts.length} main={main} role={role} ready={ready} />

          <PhaseNav containerId="phases" />
          <div id="phases" className="mx-auto max-w-[1500px] px-6 lg:px-14">
            <BuildSection data={data} main={main} role={role} conflicts={buildConflicts} />
            <EnemyKit data={data} enemyName={enemyName} role={role} />
            {PHASES.map((p) => (
              <SectionShell
                key={p.id}
                id={p.id}
                title={p.title}
                intro={p.cats.every(({ cat }) => !items(m, cat).length) ? "No matchup-specific advice for this phase yet; the general plan below applies." : undefined}
              >
                {p.cats.map(({ cat, label }) => (
                  <AdviceGroup
                    key={cat}
                    label={label}
                    mine={items(m, cat)}
                    rolePlan={items(rolePlan, cat)}
                    shared={items(sharedPlan, cat)}
                    role={role}
                  />
                ))}
              </SectionShell>
            ))}
            <AboutMatchup data={data} role={role} conflicts={conflicts.filter((cf) => !isBuildConflict(cf))} />
          </div>

          <footer className="mx-auto mt-20 max-w-[1500px] px-6 lg:px-14">
            <p className="border-t border-[var(--gold-line)] pt-6 text-sm text-steel-dim">
              Built on patch {m.generated_at_patch_display} on {m.generated_at_date}.{" "}
              <Link to="/freshness" className="text-frost hover:underline">
                Data freshness
              </Link>
            </p>
            <RiotFooter className="mt-2 max-w-[48rem]" />
          </footer>
        </main>
      </SourcesProvider>
    </AbilityNamesProvider>
  );
}

function MatchupSkeleton() {
  return (
    <main aria-busy="true" aria-label="Loading matchup">
      <div className="skeleton h-[min(58vh,600px)] min-h-[420px]" />
      <div className="mx-auto -mt-16 grid max-w-[1500px] gap-6 px-6 lg:grid-cols-[1.7fr_1fr] lg:px-14">
        <div className="skeleton h-64 rounded-[var(--radius-panel)]" />
        <div className="skeleton h-64 rounded-[var(--radius-panel)]" />
      </div>
      <div className="mx-auto mt-6 max-w-[1500px] px-6 lg:px-14">
        <div className="skeleton h-56 rounded-[var(--radius-panel)]" />
      </div>
    </main>
  );
}
