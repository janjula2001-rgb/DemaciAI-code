import { createContext, Fragment, useContext, useMemo } from "react";
import { champ } from "../data/assetPaths";

// Ability names in advice text ("Apprehend", "Decisive Strike") get their icon inline, so the reader
// can match the advice to what they see in game. The page provides the names via AbilityNamesProvider.
type Key = "P" | "Q" | "W" | "E" | "R";
type Names = Record<string, Record<string, string>>; // champion id -> key -> ability name

const Ctx = createContext<Names>({});
export const AbilityNamesProvider = ({ names, children }: { names: Names; children: React.ReactNode }) => <Ctx.Provider value={names}>{children}</Ctx.Provider>;

const escape = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

export default function RichText({ text }: { text: string }) {
  const names = useContext(Ctx);
  const { re, lookup } = useMemo(() => {
    const lookup = new Map<string, { cid: string; key: Key }>();
    for (const [cid, keys] of Object.entries(names)) for (const [key, name] of Object.entries(keys)) if (name.length > 3) lookup.set(name, { cid, key: key as Key });
    const list = [...lookup.keys()].sort((a, b) => b.length - a.length).map(escape);
    return { re: list.length ? new RegExp(`\\b(${list.join("|")})\\b`, "g") : null, lookup };
  }, [names]);
  if (!re) return <>{text}</>;
  const parts = text.split(re);
  return (
    <>
      {parts.map((part, i) => {
        const hit = i % 2 === 1 ? lookup.get(part) : undefined;
        if (!hit) return <Fragment key={i}>{part}</Fragment>;
        return (
          <span key={i} className="whitespace-nowrap font-semibold text-gold-light">
            <img src={champ.ability(hit.cid, hit.key)} alt="" className="mr-1 inline-block h-[1.15em] w-[1.15em] -translate-y-[0.1em] rounded-[4px] align-middle" />
            {part}
          </span>
        );
      })}
    </>
  );
}
