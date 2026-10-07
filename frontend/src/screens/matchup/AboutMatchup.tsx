import type { MatchupBundle } from "../../data/api";
import type { Conflict, Role } from "../../data/types";
import { useSources } from "../../components/SourcesDrawer";
import ConflictCard from "./ConflictCard";
import { AdviceGroup, SectionShell } from "./PhaseSection";
import { items } from "./sections";

// Overview notes, the disagreements that aren't about the build, and the sources left out as outdated.
export default function AboutMatchup({ data, role, conflicts }: { data: MatchupBundle; role: Role; conflicts: Conflict[] }) {
  const { m, rolePlan, sharedPlan } = data;
  const openSources = useSources();
  return (
    <SectionShell id="about" title="About this matchup">
      <AdviceGroup mine={items(m, "overview")} rolePlan={items(rolePlan, "overview")} shared={items(sharedPlan, "overview")} role={role} emptyText="No overview notes for this matchup." />
      {conflicts.length > 0 && (
        <div className="mt-8 grid gap-4 xl:grid-cols-2">
          {conflicts.map((cf) => (
            <ConflictCard key={cf.topic} cf={cf} />
          ))}
        </div>
      )}
      {m.outdated.length > 0 && (
        <div className="glass mt-8 flex flex-wrap items-center justify-between gap-4 p-5">
          <div className="max-w-[var(--measure)]">
            <h3 className="font-display text-lg text-gold-light">Left out as outdated</h3>
            <p className="mt-1 text-sm text-steel-dim">
              {m.outdated.length} source claim{m.outdated.length === 1 ? "" : "s"}: build advice from before the last item overhaul, or kit advice from
              before a champion's last rework. Not used anywhere above; kept for reference.
            </p>
          </div>
          <button
            onClick={() => openSources({ title: "Outdated claims, not used as advice", sources: m.outdated })}
            className="rounded-full border border-[var(--gold-line)] px-4 py-2 text-sm text-steel transition-colors hover:border-gold hover:text-gold-light"
          >
            Show them
          </button>
        </div>
      )}
    </SectionShell>
  );
}
