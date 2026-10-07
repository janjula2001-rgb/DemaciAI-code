import type { MatchupBundle } from "../../../data/api";
import type { AdviceItem, Conflict, Role } from "../../../data/types";
import { BUILD_CATS } from "../CheatSheet";
import { AdviceGroup, SectionShell } from "../PhaseSection";
import { items } from "../sections";
import ConflictCard from "../ConflictCard";
import Disclosure from "../../../components/Disclosure";
import AdviceCard from "../../../components/AdviceCard";
import RunePage from "./RunePage";
import { OtpBuild } from "./BuildPath";
import { SkillGrid, StartCard, SummonerCards } from "./Loadout";
import SheetCard from "./SheetCard";

const LABEL: Record<string, string> = {
  runes: "Runes",
  summoners: "Summoner spells",
  starting_items: "Starting items",
  skill_order: "Skill order",
  first_back: "First back",
  core_build: "Core build",
  situational_items: "Situational items",
};
const SHEET_URL = "docs.google.com/spreadsheets";
// advice that only restates the one-trick data or Federals1's sheet, which the cards above already show
const scripted = (it: AdviceItem) => it.sources.every((s) => s.source_type === "onetricks_data" || s.source_url.includes(SHEET_URL));

export default function BuildSection({ data, main, role, conflicts }: { data: MatchupBundle; main: string; role: Role; conflicts: Conflict[] }) {
  const { m, capture, sheetRow, sheetMeta, rolePlan, sharedPlan } = data;
  const fromGuides = BUILD_CATS.flatMap((c) => items(m, c).filter((it) => !scripted(it)).map((it) => ({ c, it })));
  const restated = BUILD_CATS.flatMap((c) => items(m, c).filter(scripted).map((it) => ({ c, it })));
  const generalCats = BUILD_CATS.filter((c) => items(rolePlan, c).length || items(sharedPlan, c).length);

  return (
    <SectionShell id="build" title="Build and runes">
      {capture ? (
        <div className="grid gap-5">
          <RunePage capture={capture} />
          <div className="grid gap-5 lg:grid-cols-2">
            <SummonerCards capture={capture} />
            <StartCard capture={capture} />
          </div>
          <OtpBuild capture={capture} />
          <SkillGrid capture={capture} main={main} />
        </div>
      ) : (
        <p className="text-steel-dim">No one-trick build data captured for this {role} matchup yet.</p>
      )}
      {sheetRow && (
        <div className="mt-5">
          <SheetCard row={sheetRow} sheet={sheetMeta} role={role} />
        </div>
      )}
      {conflicts.length > 0 && (
        <div className="mt-8 grid gap-4 xl:grid-cols-2">
          {conflicts.map((cf) => (
            <ConflictCard key={cf.topic} cf={cf} />
          ))}
        </div>
      )}
      {fromGuides.length > 0 && (
        <div className="mt-8">
          <h3 className="mb-3 font-display text-lg text-gold">From guides</h3>
          <div className="grid gap-3 xl:grid-cols-2">
            {fromGuides.map(({ c, it }, i) => (
              <div key={i}>
                <p className="mb-1.5 text-xs text-steel-dim">{LABEL[c]}</p>
                <AdviceCard it={it} />
              </div>
            ))}
          </div>
        </div>
      )}
      {restated.length > 0 && (
        <Disclosure label="The build data above as text, with its sources">
          <div className="grid gap-3 xl:grid-cols-2">
            {restated.map(({ c, it }, i) => (
              <div key={i}>
                <p className="mb-1.5 text-xs text-steel-dim">{LABEL[c]}</p>
                <AdviceCard it={it} compact />
              </div>
            ))}
          </div>
        </Disclosure>
      )}
      {generalCats.map((c) => (
        <AdviceGroup key={c} label={`${LABEL[c]}, general advice`} mine={[]} rolePlan={items(rolePlan, c)} shared={items(sharedPlan, c)} role={role} />
      ))}
    </SectionShell>
  );
}
