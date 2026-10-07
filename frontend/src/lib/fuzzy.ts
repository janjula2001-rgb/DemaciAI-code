// Tiny subsequence fuzzy match: "drmun" finds "Dr. Mundo", "ks" finds "K'Sante".
// Higher score = better; null = no match. Prefix and word-start hits score more.
const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9]/g, "");

export function fuzzyScore(query: string, target: string): number | null {
  const q = norm(query);
  if (!q) return 0;
  const t = norm(target);
  if (t.startsWith(q)) return 1000 - t.length;
  let score = 0;
  let ti = 0;
  let streak = 0;
  for (const ch of q) {
    const found = t.indexOf(ch, ti);
    if (found < 0) return null;
    streak = found === ti ? streak + 1 : 0;
    score += 10 + streak * 5 - (found - ti);
    ti = found + 1;
  }
  return score;
}

export function fuzzyFilter<T>(items: T[], query: string, key: (t: T) => string): T[] {
  if (!query.trim()) return items;
  return items
    .map((it) => ({ it, s: fuzzyScore(query, key(it)) }))
    .filter((x): x is { it: T; s: number } => x.s !== null)
    .sort((a, b) => b.s - a.s)
    .map((x) => x.it);
}
