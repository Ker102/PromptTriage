import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Research | PromptTriage",
  description:
    "Original research on LLM system prompts, format impact, and model benchmarks. Data-driven studies backed by 1,000+ evaluations.",
};

const STUDIES = [
  {
    tag: "Study E",
    title: "AI Format Wars",
    subtitle: "Does the shape of your prompt matter?",
    stats: "1,080 evals · 5 models · 3-judge jury",
    href: "https://blog.kaelux.dev/page/ai-format-wars",
    live: true,
  },
  {
    tag: "Study C",
    title: "The Prompt Invariance Illusion",
    subtitle: "Does your system prompt actually matter?",
    stats: "104 evals · 2 models · 3-judge jury",
    href: "#",
    live: false,
  },
  {
    tag: "Analysis",
    title: "170 System Prompts from Top AI Companies",
    subtitle: "3 critical anti-patterns found in production systems.",
    stats: "170 prompts analyzed",
    href: "#",
    live: false,
  },
];

export default function ResearchPage() {
  return (
    <div className="relative min-h-screen bg-[var(--background)] text-[var(--foreground)] transition-colors duration-500">
      <main className="relative z-10 mx-auto flex w-full max-w-3xl flex-col gap-16 px-4 pt-16 pb-24 md:px-6">
        {/* Back */}
        <Link
          href="/"
          className="inline-flex w-fit items-center gap-2 text-xs uppercase tracking-[0.2em] text-muted transition hover:text-[var(--foreground)]"
        >
          ← Back
        </Link>

        {/* Header */}
        <header className="space-y-3">
          <p className="text-[0.65rem] font-semibold uppercase tracking-[0.4em] text-muted">
            PromptTriage
          </p>
          <h1 className="text-3xl font-semibold tracking-tight md:text-4xl">
            Research
          </h1>
          <p className="max-w-lg text-sm leading-relaxed text-muted">
            Data-driven studies on prompt engineering and LLM behavior. All
            evaluations scored by a multi-model jury on a 100-point scale.
          </p>
        </header>

        {/* Studies */}
        <div className="flex flex-col gap-4">
          {STUDIES.map((study) => {
            const Wrapper = study.live ? "a" : "div";
            const wrapperProps = study.live
              ? {
                  href: study.href,
                  target: "_blank" as const,
                  rel: "noopener noreferrer",
                }
              : {};

            return (
              <Wrapper
                key={study.tag}
                {...wrapperProps}
                className={`group relative flex flex-col gap-2 rounded-2xl border border-[var(--surface-border)] p-5 transition-all duration-300 md:p-6 ${
                  study.live
                    ? "cursor-pointer hover:-translate-y-0.5 hover:border-white/20"
                    : "opacity-50"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[0.6rem] font-semibold uppercase tracking-[0.25em] text-muted">
                    {study.tag}
                  </span>
                  {study.live ? (
                    <span className="text-[0.6rem] text-muted/40 transition-transform group-hover:translate-x-0.5">
                      Read →
                    </span>
                  ) : (
                    <span className="text-[0.55rem] uppercase tracking-[0.2em] text-muted/40">
                      Coming soon
                    </span>
                  )}
                </div>

                <h2 className="text-lg font-medium md:text-xl">
                  {study.title}
                </h2>
                <p className="text-sm text-muted">{study.subtitle}</p>
                <p className="text-[0.65rem] uppercase tracking-[0.15em] text-muted/40">
                  {study.stats}
                </p>
              </Wrapper>
            );
          })}
        </div>

        {/* Footer link */}
        <p className="text-center text-xs text-muted/50">
          Datasets and scripts are open-source on{" "}
          <a
            href="https://github.com/Ker102/PromptTriage"
            target="_blank"
            rel="noopener noreferrer"
            className="underline transition hover:text-muted"
          >
            GitHub
          </a>
          .
        </p>
      </main>
    </div>
  );
}
