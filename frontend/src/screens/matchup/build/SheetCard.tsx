import { useAssets } from "../../../data/api";
import type { Role, Sheet, SheetRow } from "../../../data/types";
import GameIcon from "../../../components/GameIcon";
import { SheetBuild } from "./BuildPath";

// Federals1's matchup spreadsheet (Challenger, top lane): his ordered build path, runes, skill max, rating.
export default function SheetCard({ row, sheet, role }: { row: SheetRow; sheet: Sheet | null; role: Role }) {
  const { data: assets } = useAssets();
  return (
    <div className="glass p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <h3 className="font-display text-lg text-gold-light">Federals1's matchup sheet</h3>
        <p className="text-sm text-steel-dim">
          Challenger Garen{role !== "top" ? ", written for top lane" : ""}. Rates it <span className="text-gold-light">{row.difficulty_label}</span>
          {sheet && (
            <>
              {" "}
              <a href={sheet.source_url} target="_blank" rel="noreferrer" className="text-frost hover:underline">
                (sheet)
              </a>
            </>
          )}
        </p>
      </div>
      <div className="mt-5">
        <SheetBuild row={row} />
      </div>
      <div className="mt-6 grid gap-5 md:grid-cols-[auto_auto_1fr]">
        <div>
          <p className="mb-1.5 text-xs text-steel-dim">Skill max</p>
          <p className="text-gold-light">{row.skill_order}</p>
        </div>
        <div>
          <p className="mb-1.5 text-xs text-steel-dim">Summoners</p>
          <p className="text-gold-light">{row.summoners || "–"}</p>
        </div>
        <div>
          <p className="mb-1.5 text-xs text-steel-dim">Runes</p>
          <div className="space-y-2">
            {row.runes.map((line) => {
              const [tree, rest] = line.includes(":") ? [line.slice(0, line.indexOf(":")), line.slice(line.indexOf(":") + 1)] : ["", line];
              const names = rest.split(",").map((x) => x.trim()).filter(Boolean);
              const known = names.every((n) => assets?.runes[n]);
              return (
                <div key={line} className="flex flex-wrap items-center gap-2">
                  <span className="w-28 text-sm text-steel">{tree}</span>
                  {known ? names.map((n) => <GameIcon key={n} kind="rune" name={n} size={30} />) : <span className="text-sm text-steel">{rest.trim()}</span>}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
