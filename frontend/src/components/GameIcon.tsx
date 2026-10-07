import { useState } from "react";
import { useAssets } from "../data/api";
import { champ, itemIcon, runeIcon, spellIcon } from "../data/assetPaths";
import type { Assets } from "../data/types";
import Tooltip from "./Tooltip";

export type IconKind = "item" | "rune" | "spell" | "ability";

// Federals1's sheet has typos and "A/ B" cells; assets.json maps those to real item names.
export const resolveItems = (assets: Assets | null, name: string): string[] =>
  assets?.items[name] ? [name] : (assets?.item_aliases[name] ?? []);

interface Props {
  kind: IconKind;
  name: string; // item/rune/spell name, or for abilities "<ChampionId>:<P|Q|W|E|R>"
  size?: number;
  pct?: number;
  label?: boolean;
  glow?: boolean;
}

// An item, rune, summoner spell or ability icon from the local Data Dragon cache, with a rich
// tooltip (cost and stats for items). Unknown names render as a lettered tile, never a broken image.
export default function GameIcon({ kind, name, size = 44, pct, label = false, glow = false }: Props) {
  const { data: assets } = useAssets();
  const [broken, setBroken] = useState(false);
  const info = lookup(assets, kind, name);

  const box = (
    <span className="flex flex-col items-center gap-1" style={{ width: label ? Math.max(size, 64) : undefined }}>
      <span
        className={`relative grid place-items-center overflow-hidden bg-[var(--rampart)] ${kind === "rune" ? "rounded-full" : "rounded-[10px]"} ${
          glow ? "shadow-[var(--glow-gold)]" : ""
        }`}
        style={{ width: size, height: size, boxShadow: kind === "rune" ? undefined : "inset 0 0 0 1px var(--gold-line)" }}
      >
        {info.src && !broken ? (
          <img src={info.src} alt={info.title} width={size} height={size} loading="lazy" onError={() => setBroken(true)} className="h-full w-full object-cover" />
        ) : (
          <span className="font-display text-sm text-gold">{info.title.slice(0, 2)}</span>
        )}
      </span>
      {pct !== undefined && <span className="text-xs font-semibold tabular-nums text-gold-light">{pct}%</span>}
      {label && <span className="max-w-full text-center text-xs leading-tight text-steel">{info.title}</span>}
    </span>
  );
  return (
    <Tooltip content={info.tip}>
      <span tabIndex={0} aria-label={info.title} className="rounded-[10px]">
        {box}
      </span>
    </Tooltip>
  );
}

function lookup(assets: Assets | null, kind: IconKind, name: string): { src: string | null; title: string; tip: React.ReactNode } {
  if (kind === "ability") {
    const [cid, key] = name.split(":") as [string, "P" | "Q" | "W" | "E" | "R"];
    const title = assets?.champions[cid]?.abilities[key] ?? `${cid} ${key}`;
    return { src: champ.ability(cid, key), title, tip: <TipTitle title={title} sub={key === "P" ? "Passive" : key} /> };
  }
  if (kind === "item") {
    const real = resolveItems(assets, name)[0];
    const it = real ? assets!.items[real] : null;
    if (!it) return { src: null, title: name, tip: <TipTitle title={name} /> };
    return {
      src: itemIcon(it.id),
      title: real,
      tip: (
        <>
          <TipTitle title={real} sub={`${it.cost.toLocaleString()} gold`} />
          {it.plaintext && <p className="mt-1 italic text-steel-dim">{it.plaintext}</p>}
          <p className="mt-1.5 whitespace-pre-line">{it.description.slice(0, 420)}</p>
        </>
      ),
    };
  }
  if (kind === "rune") {
    const r = assets?.runes[name];
    return {
      src: r ? runeIcon(r.id) : null,
      title: name,
      tip: (
        <>
          <TipTitle title={name} sub={r?.style} />
          {r?.short && <p className="mt-1.5">{r.short}</p>}
        </>
      ),
    };
  }
  const s = assets?.spells[name];
  return {
    src: s ? spellIcon(s.id) : null,
    title: name,
    tip: (
      <>
        <TipTitle title={name} sub="Summoner spell" />
        {s?.description && <p className="mt-1.5">{s.description}</p>}
      </>
    ),
  };
}

function TipTitle({ title, sub }: { title: string; sub?: string }) {
  return (
    <p className="flex items-baseline justify-between gap-4">
      <span className="font-display text-base text-gold-light">{title}</span>
      {sub && <span className="text-xs text-steel-dim">{sub}</span>}
    </p>
  );
}
