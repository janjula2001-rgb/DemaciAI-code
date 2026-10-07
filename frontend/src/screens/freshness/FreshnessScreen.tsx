import { useEffect, useState } from "react";
import { Link } from "react-router";
import { motion } from "motion/react";
import { champ } from "../../data/assetPaths";
import { ease, stagger } from "../../theme/motion";
import { RiotFooter } from "../../components/Atmosphere";

interface Finding {
  kind: string;
  severity: "high" | "medium" | "low";
  what: string;
  detail: string;
  todo: string;
  affects: { matchup: string; ability?: string; sections?: string[] }[];
}
interface Report {
  checked_at: string;
  current_patch: string;
  data_built_on: string;
  findings: Finding[];
  manual_checks: { source: string; how: string; captured: string | string[]; items?: { author: string; url: string }[] }[];
}

const COMMAND = String.raw`.venv\Scripts\python scripts\refresh_patch.py`;
const SEV_COLOR = { high: "var(--blood)", medium: "var(--amber)", low: "var(--frost)" };

// Read-only view of the last freshness check and patch-refresh to-do. A refresh runs from the terminal
// (user's choice): it updates the data and re-exports it for this app.
export default function FreshnessScreen() {
  const [report, setReport] = useState<Report | null>(null);
  const [todo, setTodo] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetch("/data/freshness_report.json").then((r) => (r.ok ? r.json() : null)).then(setReport).catch(() => setReport(null));
    fetch("/data/refresh_todo.md").then((r) => (r.ok ? r.text() : null)).then(setTodo).catch(() => setTodo(null));
  }, []);

  const copy = () => {
    navigator.clipboard.writeText(COMMAND).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    });
  };

  return (
    <main className="relative min-h-screen pb-24">
      <div className="relative h-56 overflow-hidden">
        <img src={champ.splash("Garen")} alt="" className="h-full w-full object-cover opacity-40" style={{ objectPosition: "80% 30%" }} />
        <div className="absolute inset-0 bg-[linear-gradient(180deg,transparent,var(--night))]" />
        <div className="absolute inset-0 mx-auto max-w-[1100px] px-6 lg:px-14">
        <Link to="/" className="glass glass-blur absolute left-6 top-6 flex items-center gap-2 px-4 py-2 text-sm text-steel hover:text-gold-light lg:left-14">
          <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
            <path d="m15 18-6-6 6-6" />
          </svg>
          Matchups
        </Link>
        <h1 className="absolute bottom-6 left-6 font-display text-[length:var(--text-2xl)] text-gold-light lg:left-14">Data freshness</h1>
        </div>
      </div>

      <div className="mx-auto max-w-[1100px] space-y-6 px-6 lg:px-14">
        {report && (
          <motion.div
            className="grid gap-4 sm:grid-cols-3"
            initial="hidden"
            animate="shown"
            variants={{ shown: { transition: { staggerChildren: stagger.list } } }}
          >
            {[
              [report.current_patch, "Current patch"],
              [report.data_built_on, "Data built on"],
              [String(report.findings.length), `Things to review (checked ${report.checked_at})`],
            ].map(([v, k]) => (
              <motion.div key={k} className="glass p-5" variants={{ hidden: { opacity: 0, y: 10 }, shown: { opacity: 1, y: 0, transition: { duration: 0.5, ease: ease.out } } }}>
                <p className="font-display text-3xl text-gold-light">{v}</p>
                <p className="mt-1 text-sm text-steel-dim">{k}</p>
              </motion.div>
            ))}
          </motion.div>
        )}

        <section className="glass p-6">
          <h2 className="font-display text-lg text-gold-light">Refresh after a new patch</h2>
          <p className="mt-1 max-w-[var(--measure)] text-sm text-steel-dim">
            Run this in the project folder. It updates patch data, change logs, stats and every page, re-exports the data for this app, and writes the
            to-do below for whatever needs Claude. Reload this page when it's done.
          </p>
          <div className="mt-4 flex items-center gap-3 rounded-[var(--radius-icon)] border border-[var(--gold-line)] bg-black/30 px-4 py-3">
            <code className="flex-1 overflow-x-auto text-sm text-gold-light">{COMMAND}</code>
            <button onClick={copy} className="rounded-full border border-[var(--gold-line)] px-3 py-1 text-xs text-steel transition-colors hover:border-gold hover:text-gold-light">
              {copied ? "Copied" : "Copy"}
            </button>
          </div>
        </section>

        {report && report.findings.length === 0 && (
          <section className="glass p-6">
            <p className="text-gold-light">Nothing relevant to Garen has changed since the data was built.</p>
          </section>
        )}
        {report?.findings.map((f, i) => (
          <section key={i} className="glass p-6" style={{ borderLeft: `3px solid ${SEV_COLOR[f.severity]}` }}>
            <h2 className="font-display text-lg text-gold-light">{f.what}</h2>
            <p className="mt-1 text-sm text-steel-dim">{f.detail.slice(0, 600)}</p>
            {f.affects.length > 0 && (
              <ul className="mt-3 space-y-1 text-sm text-steel">
                {f.affects.map((a, j) => (
                  <li key={j}>
                    {a.matchup}
                    {a.sections?.length ? `: ${a.sections.join(", ")}` : ""}
                  </li>
                ))}
              </ul>
            )}
            <p className="mt-3 text-sm text-amber">To do: {f.todo}</p>
          </section>
        ))}

        {todo && (
          <section className="glass p-6">
            <h2 className="font-display text-lg text-gold-light">Patch refresh to-do for Claude Code</h2>
            <p className="mt-1 text-sm text-steel-dim">From the last refresh. Paste it into a Claude Code session and work through it one section at a time.</p>
            <Markdown text={todo} />
          </section>
        )}

        {report && report.manual_checks.length > 0 && (
          <section className="glass p-6">
            <h2 className="font-display text-lg text-gold-light">Manual checks (sites that block scripts)</h2>
            <ul className="mt-3 space-y-4">
              {report.manual_checks.map((mc) => (
                <li key={mc.source}>
                  <p className="text-gold-light">{mc.source}</p>
                  <p className="text-sm text-steel-dim">
                    {mc.how}. Captured {Array.isArray(mc.captured) ? mc.captured.join(", ") : mc.captured}.
                  </p>
                  {mc.items && (
                    <ul className="mt-1 flex flex-wrap gap-x-4 text-sm">
                      {mc.items.map((it) => (
                        <li key={it.url}>
                          <a href={it.url} target="_blank" rel="noreferrer" className="text-frost hover:underline">
                            {it.author}
                          </a>
                        </li>
                      ))}
                    </ul>
                  )}
                </li>
              ))}
            </ul>
          </section>
        )}
        <RiotFooter />
      </div>
    </main>
  );
}

// Just enough Markdown for refresh_todo.md: headings, bullets, paragraphs, **bold**.
function Markdown({ text }: { text: string }) {
  const bold = (s: string) => s.split(/\*\*(.+?)\*\*/g).map((p, i) => (i % 2 ? <strong key={i} className="text-gold-light">{p}</strong> : p));
  const blocks: React.ReactNode[] = [];
  let list: string[] = [];
  const flush = () => {
    if (list.length) blocks.push(<ul key={blocks.length} className="ml-5 list-disc space-y-1 text-sm text-steel">{list.map((l, i) => <li key={i}>{bold(l)}</li>)}</ul>);
    list = [];
  };
  for (const line of text.split("\n")) {
    if (line.startsWith("- ")) {
      list.push(line.slice(2));
      continue;
    }
    flush();
    if (line.startsWith("# ")) continue; // the page has its own title
    if (line.startsWith("## ")) blocks.push(<h3 key={blocks.length} className="mt-4 font-display text-base text-gold">{line.slice(3)}</h3>);
    else if (line.trim()) blocks.push(<p key={blocks.length} className="text-sm text-steel">{bold(line)}</p>);
  }
  flush();
  return <div className="mt-4 space-y-2">{blocks}</div>;
}
