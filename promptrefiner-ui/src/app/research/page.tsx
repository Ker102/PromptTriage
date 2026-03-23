import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Research | PromptTriage",
  description:
    "Original research on LLM system prompts, format impact, and model benchmarks. 1,080+ evaluations across 5 frontier models.",
};

const STUDIES = [
  {
    tag: "Study E v2",
    title: "AI Format Wars: Does the Shape of Your Prompt Matter?",
    description:
      "1,080 evaluations across GPT-5.4, Nemotron 120B, Claude, Gemini, and Qwen. JSON output improves reasoning. Short prompts beat long ones by 20%.",
    findings: [
      "Short prompts (<50 words) scored 80.1 vs long prompts at 66.9",
      "JSON/YAML output beats plain text — structure acts as cognitive scaffold",
      "Nemotron 120B scored 85.1, just 3 pts behind GPT-5.4 (88.1)",
    ],
    href: "https://blog.kaelux.dev/ai-format-wars",
    models: "GPT-5.4 · Nemotron 120B · Claude 4.6 · Gemini 3.1 · Qwen 397B",
    evaluations: "1,080",
  },
  {
    tag: "Study C v2",
    title: "Does Your System Prompt Actually Matter?",
    description:
      "104 evaluations across 13 complex tasks. Expert persona prompts underperform simple, concise instructions. Structured prompts give a ~5% reliability bump.",
    findings: [
      "Bare (zero-shot): 72.1 vs Simple instructions: 76.5 / 100",
      "Expert Persona (200 words) underperforms simple rules",
      "System prompts cannot inject reasoning the model doesn't have",
    ],
    href: "https://blog.kaelux.dev/does-your-system-prompt-matter",
    models: "Gemini 3.1 Pro · Nemotron 3 Super",
    evaluations: "104",
  },
  {
    tag: "Analysis",
    title: "170 System Prompts from Top AI Companies",
    description:
      "We analyzed 170 production system prompts from leading AI systems. Found 3 critical anti-patterns that most prompts share.",
    findings: [
      "Kitchen-sink prompts: 62% try to do too much in one prompt",
      "Redundant constraints: 45% duplicate what the model already does",
      "Missing negative examples: 71% lack boundary definitions",
    ],
    href: "https://blog.kaelux.dev/170-system-prompts-analysis",
    models: "N/A — Static Analysis",
    evaluations: "170 prompts",
  },
];

export default function ResearchPage() {
  return (
    <div className="relative min-h-screen bg-[var(--background)] text-[var(--foreground)] transition-colors duration-500">
      <main className="relative z-10 mx-auto flex w-full max-w-4xl flex-col gap-12 px-4 pt-12 pb-20 md:px-6">
        {/* Back nav */}
        <Link
          href="/"
          className="inline-flex w-fit items-center gap-2 text-xs uppercase tracking-[0.2em] text-muted transition hover:text-[var(--foreground)]"
        >
          ← Back to PromptTriage
        </Link>

        {/* Header */}
        <header className="space-y-4">
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-muted">
            PromptTriage Research
          </p>
          <h1 className="text-3xl font-semibold text-[var(--foreground)] md:text-5xl">
            Original Research
          </h1>
          <p className="max-w-2xl text-base leading-relaxed text-muted md:text-lg">
            Data-driven studies on prompt engineering, system prompt impact, and
            LLM benchmarks. All evaluations are scored by a 3-judge LLM jury on
            a 100-point scale.
          </p>
        </header>

        {/* Study cards */}
        <div className="flex flex-col gap-6">
          {STUDIES.map((study) => (
            <a
              key={study.tag}
              href={study.href}
              target="_blank"
              rel="noopener noreferrer"
              className="group relative rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-card)] p-6 transition-all duration-300 hover:-translate-y-0.5 hover:border-white/20 hover:shadow-lg hover:shadow-slate-950/20 md:p-8"
            >
              {/* Tag + eval count */}
              <div className="mb-3 flex items-center gap-3">
                <span className="rounded-full border border-[rgba(148,163,184,0.2)] px-3 py-0.5 text-[0.6rem] font-semibold uppercase tracking-[0.2em] text-muted">
                  {study.tag}
                </span>
                <span className="text-[0.65rem] text-muted/60">
                  {study.evaluations} evaluations
                </span>
              </div>

              {/* Title */}
              <h2 className="mb-2 text-xl font-semibold text-[var(--foreground)] transition-colors group-hover:text-white md:text-2xl">
                {study.title}
                <span className="ml-2 inline-block text-muted/40 transition-transform group-hover:translate-x-1">
                  →
                </span>
              </h2>

              {/* Description */}
              <p className="mb-4 text-sm leading-relaxed text-muted md:text-base">
                {study.description}
              </p>

              {/* Key findings */}
              <div className="mb-4 space-y-1.5">
                {study.findings.map((finding, i) => (
                  <div key={i} className="flex items-start gap-2 text-sm text-muted/80">
                    <span className="mt-0.5 shrink-0 text-muted/40">▸</span>
                    <span>{finding}</span>
                  </div>
                ))}
              </div>

              {/* Models badge */}
              <p className="text-[0.65rem] font-medium uppercase tracking-[0.15em] text-muted/50">
                Models: {study.models}
              </p>
            </a>
          ))}
        </div>

        {/* CTA */}
        <div className="text-center">
          <p className="mb-4 text-sm text-muted">
            All datasets and analysis scripts are open-source.
          </p>
          <a
            href="https://github.com/Ker102/PromptTriage"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-full border border-[rgba(148,163,184,0.25)] px-6 py-2.5 text-xs font-semibold uppercase tracking-[0.2em] text-muted transition duration-300 hover:border-[rgba(148,163,184,0.5)] hover:text-[var(--foreground)]"
          >
            View on GitHub →
          </a>
        </div>
      </main>
    </div>
  );
}
