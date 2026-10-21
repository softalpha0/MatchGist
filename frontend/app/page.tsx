import Link from "next/link";
import { Logo } from "@/components/Logo";

const REPO = "https://github.com/softalpha0/matchgist";

// The same goal, as six fans actually receive it (text in the shape the agents produce).
const SAME_GOAL = [
  {
    who: "Studio analyst · London",
    channel: "Broadcast overlay",
    tone: "border-accent-2/40",
    body: "Dmytro Lysenko-Vale scores for Riverside Athletic (67'): RIV 2-1 NOR. A 0.31 xG chance, struck at 104 km/h.",
    meta: "lower third · 10 s cue",
  },
  {
    who: "Commuter · Jakarta",
    channel: "SMS · Bahasa",
    tone: "border-emerald-400/40",
    body: "GOL! RIV 2-1 NOR (67') Dmytro Lysenko-Vale. Peluang 0.31 xG.",
    meta: "1 segment · GSM-7 · 0.2 KB · 2 of 4 pings left",
  },
  {
    who: "Fan · Lagos",
    channel: "Voice note · Pidgin",
    tone: "border-violet-400/40",
    body: "“Dmytro Lysenko-Vale don score for Riverside Athletic, RIV 2-1 NOR.”",
    meta: "5.4 s · 10.8 KB",
  },
  {
    who: "Student · Delhi",
    channel: "SMS · Hindi",
    tone: "border-emerald-400/40",
    body: "गोल! RIV 2-1 NOR (67') Lysenko-Vale",
    meta: "1 segment · UCS-2 · 70-char limit",
    dir: "ltr",
  },
  {
    who: "Office worker · São Paulo",
    channel: "Push · Português",
    tone: "border-orange-400/40",
    body: "GOL! RIV 2-1 NOR (67') · Dmytro Lysenko-Vale marca para o Riverside Athletic.",
    meta: "title 31 chars · body 54 chars",
  },
  {
    who: "Fan roaming · Dubai",
    channel: "Watch · Arabic",
    tone: "border-pink-400/40",
    body: "هدف RIV Lysenko-Vale",
    meta: "glance · value 2-1 · 0.5 KB",
    dir: "rtl",
  },
];

const PIPELINE = [
  ["Simulator", "Seeded synthetic match: passes, shots, tackles, pressure, cards, subs. 1,300–1,500 events.", "code"],
  ["Stats Engine", "Possession, pass difficulty, xG, momentum, pressure index. The only source of numbers.", "code"],
  ["Moment Detector", "Goals, big chances, momentum swings, pressure spikes, elite passes, each with a base score.", "code"],
  ["Explainer", "Says why the moment matters, once, grounded in the stats.", "agent"],
  ["Relevance Ranker", "Scores the moment for each fan: their club, their player, their metric.", "code"],
  ["Budget Guard", "Send now, hold to bundle, or skip. Saves pings for goals and the full-time digest.", "code"],
  ["Localizer", "Rewrites it in the fan's language, tone and depth.", "agent"],
  ["Compressor", "Fits the localized text to the channel's hard limit, in that language.", "agent"],
  ["Verifier", "Every number must exist in the stats; every limit must hold. Rejects go back, then a template takes over.", "code"],
] as const;

const CONSTRAINTS = [
  ["Channel", "SMS, chat, voice note, watch glance, push alert, or a full broadcast overlay."],
  ["Data budget", "“Keep this match under 1 MB.” Every message is sized and metered."],
  ["Ping limit", "“Four messages, only when my team is involved.” The Budget Guard plans across all 90 minutes."],
  ["Language", "English, Hindi, Bahasa Indonesia, Brazilian Portuguese, Arabic and Nigerian Pidgin."],
  ["Depth", "Analyst numbers or plain-language summaries. Same facts, different telling."],
];

const NUMBERS = [
  ["160 → 70", "characters per SMS once a single Hindi, Arabic or emoji character appears"],
  ["0.2 KB", "per SMS segment, metered against each fan's budget"],
  ["15 s", "maximum voice note, sized at 16 kbps Opus"],
  ["0", "invented numbers: the Verifier checks every digit, in every script"],
];

const TECH = [
  ["Microsoft Foundry", "Hosts the models behind the Explainer, Localizer, Compressor and Digest agents."],
  ["Microsoft Agent Framework", "Agents plus a per-fan workflow with conditional edges and a Verifier retry loop."],
  ["Azure AI Speech", "Neural text-to-speech voice notes with real duration and size."],
  ["Azure Container Apps", "One container: FastAPI, the live SSE stream and this site."],
  ["GitHub Actions", "Lint, 170+ tests and a smoke run on every push."],
];

export default function Home() {
  return (
    <div className="bg-ink">
      <nav className="sticky top-0 z-40 border-b border-line/60 bg-ink/80 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center gap-6 px-6">
          <Logo className="text-lg" />
          <div className="ml-auto hidden gap-6 text-sm text-slate-300 md:flex">
            <a href="#how" className="hover:text-white">How it works</a>
            <a href="#constraints" className="hover:text-white">Constraints</a>
            <a href="#trust" className="hover:text-white">Trust</a>
            <a href="#tech" className="hover:text-white">Built with</a>
          </div>
          <Link href="/live" className="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-ink">Watch it live</Link>
        </div>
      </nav>

      {/* hero */}
      <header className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(184,243,90,0.12),transparent_60%)]" />
        <div className="mx-auto grid max-w-6xl gap-12 px-6 pb-20 pt-16 lg:grid-cols-[1.05fr_1fr] lg:pt-24">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-line bg-panel px-3 py-1 text-xs text-slate-300">
              <span className="h-1.5 w-1.5 rounded-full bg-accent" /> Multi-agent match intelligence on Microsoft Foundry
            </div>
            <h1 className="mt-5 text-5xl font-bold leading-[1.05] tracking-tight md:text-6xl">
              The match, sized to fit <span className="text-accent">every fan</span>.
            </h1>
            <p className="mt-6 max-w-xl text-lg text-slate-300">
              Most football fans don&apos;t watch on a big screen with fast Wi-Fi. They follow on mobile data, at work, on the
              bus, roaming abroad, or on a basic phone. MatchGist explains what happened and why it mattered, then fits it to
              what each fan has: an SMS, a short voice note, a watch glance or a full overlay, in their language and within
              their data budget.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/live" className="rounded-xl bg-accent px-5 py-3 font-semibold text-ink shadow-lg shadow-lime-500/20">
                Watch a match live →
              </Link>
              <a href={REPO} className="rounded-xl border border-line px-5 py-3 font-semibold text-slate-200 hover:bg-panel">
                Read the code
              </a>
            </div>
            <p className="mt-4 text-xs text-slate-500">No login. Runs on synthetic data. All clubs, players and fans are fictional.</p>
          </div>

          <div className="relative">
            <div className="mb-3 text-xs uppercase tracking-widest text-slate-400">One goal, six fans, 67th minute</div>
            <div className="grid gap-3 sm:grid-cols-2">
              {SAME_GOAL.map((g) => (
                <div key={g.who} className={`rounded-xl border bg-panel p-3 ${g.tone}`}>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="font-semibold text-slate-200">{g.who}</span>
                    <span className="text-slate-400">{g.channel}</span>
                  </div>
                  <div dir={g.dir ?? "ltr"} className="mt-2 text-[13px] leading-snug text-slate-100">{g.body}</div>
                  <div className="mt-2 font-mono text-[10px] text-slate-500">{g.meta}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </header>

      {/* numbers */}
      <section className="border-y border-line bg-panel/60">
        <div className="mx-auto grid max-w-6xl gap-6 px-6 py-10 sm:grid-cols-2 lg:grid-cols-4">
          {NUMBERS.map(([n, label]) => (
            <div key={n}>
              <div className="font-mono text-3xl font-bold text-accent">{n}</div>
              <div className="mt-1 text-sm text-slate-400">{label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* how it works */}
      <section id="how" className="mx-auto max-w-6xl px-6 py-20">
        <h2 className="text-3xl font-bold tracking-tight">Explained once. Fitted to every fan.</h2>
        <p className="mt-3 max-w-3xl text-slate-400">
          Plain code does the counting, and agents do the language. Every moment is explained once. Then, for every fan in
          parallel, a chain of agents decides whether it is worth their budget, says it their way, and squeezes it into
          their channel. A Verifier signs off every message before it leaves.
        </p>
        <ol className="mt-10 grid gap-3 md:grid-cols-3">
          {PIPELINE.map(([name, text, kind], i) => (
            <li key={name} className="relative rounded-xl border border-line bg-panel p-4">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs text-slate-500">{String(i + 1).padStart(2, "0")}</span>
                <span className="font-semibold">{name}</span>
                <span className={`ml-auto rounded px-1.5 py-px text-[10px] ${kind === "agent" ? "bg-accent/15 text-accent" : "bg-slate-700 text-slate-300"}`}>
                  {kind === "agent" ? "LLM agent" : "code"}
                </span>
              </div>
              <p className="mt-2 text-sm text-slate-400">{text}</p>
            </li>
          ))}
        </ol>
        <div className="mt-6 rounded-xl border border-line bg-panel p-4 font-mono text-xs text-slate-300">
          Explainer ─► per fan, in parallel: Ranker ─► Budget Guard ─send─► Localizer ─► Compressor ⇄ Verifier ─► deliver
          <span className="text-slate-500">   ·   hold ─► bundle within 2 min   ·   skip ─► reason logged   ·   full time ─► digest sized to what&apos;s left</span>
        </div>
      </section>

      {/* constraints */}
      <section id="constraints" className="border-y border-line bg-panel/40">
        <div className="mx-auto grid max-w-6xl gap-10 px-6 py-20 lg:grid-cols-2">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Personalised by constraint, not just by taste.</h2>
            <p className="mt-3 text-slate-400">
              Analyst or casual, favourite club, favourite player: MatchGist does all of that. It also respects what the fan
              actually has. A commuter in Jakarta on 1 MB gets four SMS, sent when Riverside are involved. A fan in Lagos gets
              short voice notes in Pidgin. A roaming fan in Dubai gets a glance on the wrist. The Budget Guard plans the whole
              match and shows which limit is binding.
            </p>
            <div className="mt-6 rounded-xl border border-amber-400/30 bg-amber-400/5 p-4 text-sm text-amber-100">
              <div className="font-semibold">The SMS trap, handled in code</div>
              <p className="mt-1 text-amber-100/80">
                One Hindi letter, Arabic letter, emoji or even a Portuguese “ç” switches an SMS from GSM-7 to UCS-2 and cuts it
                from 160 to 70 characters. MatchGist measures segments with a real encoder check, never with <code>len()</code>,
                and the Compressor rewrites in the target language until it fits.
              </p>
            </div>
          </div>
          <dl className="space-y-3">
            {CONSTRAINTS.map(([k, v]) => (
              <div key={k} className="rounded-xl border border-line bg-panel p-4">
                <dt className="font-semibold">{k}</dt>
                <dd className="mt-1 text-sm text-slate-400">{v}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      {/* trust */}
      <section id="trust" className="mx-auto max-w-6xl px-6 py-20">
        <h2 className="text-3xl font-bold tracking-tight">Numbers you can check. A feed that never stops.</h2>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {[
            ["LLMs never invent numbers", "Every number in every message must exist in the moment's facts from the Stats Engine. That includes Devanagari and Arabic-Indic digits."],
            ["Hard limits, enforced in code", "Segments, characters, seconds and bytes are checked before sending. A rejection goes back to the Compressor with the exact reason, up to twice."],
            ["Always a fallback", "Every agent call has a timeout and retries. After that, a template written for each channel and language takes over, so the fan still gets the update."],
          ].map(([t, d]) => (
            <div key={t} className="rounded-xl border border-line bg-panel p-5">
              <div className="font-semibold">{t}</div>
              <p className="mt-2 text-sm text-slate-400">{d}</p>
            </div>
          ))}
        </div>
      </section>

      {/* tech */}
      <section id="tech" className="border-t border-line bg-panel/40">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <h2 className="text-3xl font-bold tracking-tight">Built with</h2>
          <div className="mt-8 grid gap-3 md:grid-cols-5">
            {TECH.map(([t, d]) => (
              <div key={t} className="rounded-xl border border-line bg-panel p-4">
                <div className="font-semibold">{t}</div>
                <p className="mt-1 text-xs text-slate-400">{d}</p>
              </div>
            ))}
          </div>
          <div className="mt-12 flex flex-col items-center gap-3 rounded-2xl border border-accent/30 bg-accent/5 p-10 text-center">
            <div className="text-2xl font-semibold">See one match reach six fans six different ways.</div>
            <Link href="/live" className="rounded-xl bg-accent px-6 py-3 font-semibold text-ink">Open the live demo</Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-line">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-4 px-6 py-8 text-xs text-slate-500">
          <Logo />
          <span>Built for the Inside the Game Developer Hackathon.</span>
          <span className="ml-auto">All clubs, players, matches and fans are fictional. Synthetic data only.</span>
        </div>
      </footer>
    </div>
  );
}
