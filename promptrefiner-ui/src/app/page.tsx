'use client';

import { FormEvent, ReactNode, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { signIn, signOut, useSession } from "next-auth/react";
import { useTheme } from "@/components/theme-provider";
import { DecryptedText } from "@/components/decrypted-text";
import type {
  PromptAnalysisResult,
  PromptRefinementResult,
} from "@/types/prompt";

type RefinementStage = "collect" | "analyzed" | "refined";
type PendingAction = "analyze" | "refine" | null;

const MODEL_PRESETS = [
  "None / Not sure yet",
  "OpenAI GPT (chat/completions)",
  "OpenAI O-models",
  "OpenAI Codex (legacy)",
  "Anthropic Claude Sonnet",
  "Anthropic Claude Opus",
  "Anthropic Claude Haiku",
  "Google Gemini Pro",
  "Google Gemini Flash",
  "xAI Grok",
  "Mistral (general)",
] as const;

const INITIAL_FORM = {
  prompt: "",
  targetModel: MODEL_PRESETS[0],
  context: "",
  tone: "",
  outputRequirements: "",
  useWebSearch: false,
};

const HERO_TAGLINES = [
  "Designed for clarity. Crafted for results.",
  "Built for precision. Optimized for impact.",
  "Made for simplicity. Tuned for excellence.",
  "Created for purpose. Delivered with power.",
  "Refined for insight. Made to drive change.",
  "Focused on clarity. Engineered for success.",
] as const;

async function parseJson<T>(response: Response): Promise<T> {
  try {
    return (await response.json()) as T;
  } catch {
    const fallback = await response.text();
    const message = fallback?.trim()?.length
      ? fallback.trim()
      : response.statusText || "Unexpected response";
    throw new Error(message);
  }
}

function ThinkingIndicator({ color = "cyan" }: { color?: "cyan" | "emerald" | "slate" }) {
  const palette: Record<string, string> = {
    cyan: "bg-cyan-200 shadow-[0_0_8px_rgba(56,189,248,0.55)]",
    emerald: "bg-emerald-200 shadow-[0_0_8px_rgba(16,185,129,0.55)]",
    slate: "bg-slate-300 shadow-[0_0_6px_rgba(148,163,184,0.45)]",
  };

  return (
    <span className="inline-flex items-center gap-[3px]">
      {Array.from({ length: 3 }).map((_, index) => (
        <span
          key={index}
          className={`h-1.5 w-1.5 rounded-full animate-dotPulse ${
            palette[color] ?? palette.cyan
          }`}
          style={{ animationDelay: `${index * 0.18}s` }}
        />
      ))}
    </span>
  );
}

function SocialIcon({
  href,
  label,
  children,
}: {
  href: string;
  label: string;
  children: ReactNode;
}) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={label}
      className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-[rgba(148,163,184,0.35)] bg-[var(--surface-card-soft)] text-soft transition duration-300 hover:-translate-y-0.5 hover:scale-[1.05] hover:border-[rgba(148,163,184,0.65)] hover:text-white"
    >
      {children}
    </a>
  );
}

function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isLight = theme === "light";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="group relative inline-flex items-center gap-3 rounded-full border border-[var(--surface-border)] bg-[var(--surface-card-soft)] px-3 py-1.5 text-xs font-semibold tracking-[0.28em] uppercase text-soft transition duration-300 hover:shadow-[0_18px_45px_-28px_rgba(56,189,248,0.55)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-400"
      aria-label="Toggle theme"
    >
      <span className="hidden sm:inline">{isLight ? "Light" : "Dark"}</span>
      <span className="relative flex h-8 w-16 items-center justify-start overflow-hidden rounded-full bg-[var(--surface-card)] px-1 py-0.5">
        <span className="absolute inset-0 rounded-full bg-gradient-to-r from-cyan-400/40 via-emerald-400/30 to-cyan-400/40 opacity-20 blur" />
        <span
          className={`relative z-10 flex h-6 w-6 items-center justify-center rounded-full bg-gradient-to-br from-cyan-400 to-emerald-400 text-slate-900 shadow-lg transition-transform duration-500 ease-out ${
            isLight ? "translate-x-8" : "translate-x-0"
          }`}
        >
          {isLight ? (
            <svg
              className="h-3 w-3"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="12" cy="12" r="5" />
              <line x1="12" y1="1" x2="12" y2="3" />
              <line x1="12" y1="21" x2="12" y2="23" />
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
              <line x1="1" y1="12" x2="3" y2="12" />
              <line x1="21" y1="12" x2="23" y2="12" />
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
            </svg>
          ) : (
            <svg
              className="h-3 w-3"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </svg>
          )}
        </span>
      </span>
    </button>
  );
}

function formatPlanLabel(plan?: string | null): string | null {
  if (!plan) {
    return null;
  }
  const normalized = plan.replace(/[_-]/g, " ").toLowerCase();
  return normalized.replace(/\b\w/g, (char) => char.toUpperCase());
}

export default function Home() {
  const navLinks = [
    { label: "Features", href: "#features" },
    { label: "Blueprints", href: "#blueprint" },
    { label: "Workflow", href: "#workflow" },
    { label: "Docs", href: "#docs" },
    { label: "Pricing", href: "/pricing" },
  ];

  const socialLinks = [
    {
      label: "Twitter",
      href: "https://twitter.com",
      icon: (
        <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="currentColor">
          <path d="M22.46 6c-.77.35-1.6.58-2.46.69a4.18 4.18 0 0 0 1.84-2.31 8.36 8.36 0 0 1-2.65 1.04 4.14 4.14 0 0 0-7.06 3.77A11.73 11.73 0 0 1 3.16 4.9a4.12 4.12 0 0 0 1.28 5.52 4.11 4.11 0 0 1-1.87-.52v.05a4.14 4.14 0 0 0 3.32 4.06 4.2 4.2 0 0 1-1.86.07 4.15 4.15 0 0 0 3.87 2.88A8.33 8.33 0 0 1 2 19.54a11.75 11.75 0 0 0 6.29 1.84c7.55 0 11.68-6.26 11.68-11.68 0-.18 0-.35-.01-.53A8.35 8.35 0 0 0 22.46 6Z" />
        </svg>
      ),
    },
    {
      label: "GitHub",
      href: "https://github.com",
      icon: (
        <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="currentColor">
          <path
            fillRule="evenodd"
            d="M12 2a10 10 0 0 0-3.16 19.48c.5.09.68-.22.68-.48v-1.7c-2.78.61-3.37-1.34-3.37-1.34-.45-1.16-1.1-1.47-1.1-1.47-.9-.62.07-.6.07-.6 1 .07 1.53 1.05 1.53 1.05.88 1.52 2.32 1.08 2.88.83.09-.64.35-1.08.63-1.33-2.22-.25-4.55-1.11-4.55-4.95 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.64 0 0 .84-.27 2.75 1.02a9.6 9.6 0 0 1 2.5-.34c.85 0 1.7.11 2.5.34 1.9-1.29 2.74-1.02 2.74-1.02.56 1.37.21 2.39.1 2.64.65.7 1.03 1.59 1.03 2.68 0 3.85-2.34 4.7-4.57 4.95.36.32.68.94.68 1.9v2.82c0 .27.18.58.69.48A10 10 0 0 0 12 2Z"
          />
        </svg>
      ),
    },
    {
      label: "Dribbble",
      href: "https://dribbble.com",
      icon: (
        <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="currentColor">
          <path d="M12 2C6.49 2 2 6.49 2 12s4.49 10 10 10 10-4.49 10-10S17.51 2 12 2Zm6.6 4.81a8.15 8.15 0 0 1 1.86 5.15c-.28-.06-3-.62-5.76-.27-.12-.29-.23-.6-.37-.9-.37-.87-.8-1.71-1.24-2.52 3.37-1.45 5.38-1.4 5.51-1.39ZM12 3.65c2 0 3.83.76 5.2 2-1.13-.03-2.74.16-4.7.92a31.9 31.9 0 0 0-3.63-4.44c.37-.05.73-.08 1.13-.08Zm-2.22.32a30.76 30.76 0 0 1 3.48 4.26c-4.61 1.73-8.7 1.67-8.96 1.67a8.33 8.33 0 0 1 5.48-5.93ZM3.62 12.1v-.1c.25.01 4.9.03 9.34-1.6.3.53.57 1.1.82 1.67-.1.03-.2.06-.3.1-4.7 1.52-7.26 5.1-7.44 5.36A8.3 8.3 0 0 1 3.62 12.1Zm2.77 6.3c.14-.23 2.06-3.2 6.93-4.75 1.85 4.81 2.61 8.75 2.72 9.43-1.26.54-2.64.84-4.04.84-2.27 0-4.35-.8-5.96-2.14Zm11.36.75c-.07-.46-.8-4.23-2.54-8.64 2.51-.4 4.7.25 4.96.33a8.3 8.3 0 0 1-2.42 8.3Z" />
        </svg>
      ),
    },
  ];
  const [form, setForm] = useState(() => ({ ...INITIAL_FORM }));
  const [analysis, setAnalysis] = useState<PromptAnalysisResult | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [refinement, setRefinement] = useState<PromptRefinementResult | null>(
    null,
  );
  const [stage, setStage] = useState<RefinementStage>("collect");
  const [pendingAction, setPendingAction] = useState<PendingAction>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [rewriteCount, setRewriteCount] = useState(0);
  const { data: session, status } = useSession();
  const planLabel = formatPlanLabel(session?.user?.subscriptionPlan);
  const subscriptionPlan =
    (session?.user?.subscriptionPlan as string | undefined)?.toUpperCase() ??
    "FREE";
  const isPaidPlan = subscriptionPlan !== "FREE";
  const firecrawlHelperText = isPaidPlan
    ? "Pulls supporting facts from the web to help Gemini identify missing context. Requires a valid FIRECRAWL_API_KEY."
    : "Available on Pro plans. Upgrade to unlock Firecrawl web search for richer context.";

  const isAuthenticated = status === "authenticated";
  const handleAuthButtonClick = () => {
    if (isAuthenticated) {
      const callbackUrl =
        typeof window !== "undefined" ? window.location.origin : "/";
      void signOut({ callbackUrl });
      return;
    }
    const callbackUrl =
      typeof window !== "undefined" ? window.location.href : "/";
    void signIn("google", { callbackUrl });
  };

  const isAnalyzing = pendingAction === "analyze";
  const isRefining = pendingAction === "refine";

  const blueprint = analysis?.blueprint;

  const unansweredQuestions = useMemo(() => {
    if (!analysis?.questions?.length) {
      return false;
    }

    return analysis.questions.some(
      (question) => !answers[question.id]?.trim(),
    );
  }, [analysis, answers]);

  const handleFormChange = <T extends keyof typeof form>(
    key: T,
    value: string,
  ) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleAnswerChange = (id: string, value: string) => {
    setAnswers((prev) => ({ ...prev, [id]: value }));
  };

  const handleWebSearchToggle = (value: boolean) => {
    if (!isPaidPlan) {
      return;
    }
    setForm((prev) => ({ ...prev, useWebSearch: value }));
  };

  useEffect(() => {
    if (!isPaidPlan && form.useWebSearch) {
      setForm((prev) => ({ ...prev, useWebSearch: false }));
    }
  }, [isPaidPlan, form.useWebSearch]);

  const handleAnalyze = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!isAuthenticated) {
      await signIn("google", { callbackUrl: window.location.href });
      return;
    }

    setPendingAction("analyze");
    setError(null);
    setAnalysis(null);
    setAnswers({});
    setRefinement(null);

    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: form.prompt,
          targetModel: form.targetModel,
          context: form.context || undefined,
          useWebSearch: form.useWebSearch || undefined,
        }),
      });

      if (!response.ok) {
        const payload = await parseJson<{ error?: string }>(response);
        throw new Error(payload.error ?? "Analysis request failed.");
      }

      const payload = await parseJson<PromptAnalysisResult>(response);

      setAnalysis(payload);
      setAnswers(
        payload.questions.reduce<Record<string, string>>((acc, question) => {
          acc[question.id] = "";
          return acc;
        }, {}),
      );
      setStage("analyzed");
      setRewriteCount(0);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Unable to analyze prompt.";
      setError(message);
      setStage("collect");
    } finally {
      setPendingAction(null);
    }
  };

  const submitRefine = async (variationHint?: string): Promise<boolean> => {
    if (!analysis) {
      return false;
    }

    if (!isAuthenticated) {
      await signIn("google", { callbackUrl: window.location.href });
      return false;
    }

    setPendingAction("refine");
    setError(null);

    try {
      const response = await fetch("/api/refine", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: form.prompt,
          targetModel: form.targetModel,
          context: form.context || undefined,
          tone: form.tone || undefined,
          outputRequirements: form.outputRequirements || undefined,
          answers,
          questions: analysis.questions,
          blueprint: analysis.blueprint,
          externalContext: analysis.externalContext,
          variationHint: variationHint || undefined,
        }),
      });

      if (!response.ok) {
        const payload = await parseJson<{ error?: string }>(response);
        throw new Error(payload.error ?? "Refinement request failed.");
      }

      const payload = await parseJson<PromptRefinementResult>(response);

      setCopied(false);
      setRefinement(payload);
      setStage("refined");
      return true;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Unable to refine prompt.";
      setError(message);
      return false;
    } finally {
      setPendingAction(null);
    }
  };

  const handleRefine = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const success = await submitRefine();
    if (success) {
      setRewriteCount(0);
    }
  };

  const handleRewrite = async () => {
    if (!analysis || unansweredQuestions || pendingAction === "refine") {
      return;
    }

    const nextCount = rewriteCount + 1;
    const hint = `Generate an alternate refined prompt that approaches the task from a different angle than previous variant #${nextCount}. Maintain accuracy while varying structure, tone, or emphasis.`;
    const success = await submitRefine(hint);
    if (success) {
      setRewriteCount(nextCount);
    }
  };

  const handleReset = () => {
    setForm({ ...INITIAL_FORM });
    setAnalysis(null);
    setAnswers({});
    setRefinement(null);
    setStage("collect");
    setError(null);
    setCopied(false);
    setRewriteCount(0);
  };

  const handleCopy = async () => {
    if (!refinement?.refinedPrompt) {
      return;
    }

    try {
      await navigator.clipboard.writeText(refinement.refinedPrompt);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Copy failed", err);
      setError("Unable to copy to clipboard. Please copy manually.");
    }
  };

  return (
    <div className="min-h-screen bg-[var(--background)] text-[var(--foreground)] transition-colors duration-500">
      <main className="mx-auto flex w-full max-w-5xl flex-col gap-10 px-6 py-12">
        <nav className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center justify-between gap-4">
            <span className="text-sm font-semibold uppercase tracking-[0.4em] text-soft">
              PromptTriage
            </span>
            <div className="flex items-center gap-3 md:hidden">
              <ThemeToggle />
              <button
                type="button"
                disabled={status === "loading"}
                onClick={handleAuthButtonClick}
                className="inline-flex items-center gap-2 rounded-full border border-[rgba(148,163,184,0.35)] bg-[var(--surface-card)] px-3 py-1 text-[0.6rem] font-semibold uppercase tracking-[0.32em] text-soft transition duration-200 hover:-translate-y-0.5 hover:border-[rgba(148,163,184,0.55)] hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-400 disabled:cursor-not-allowed disabled:opacity-70"
              >
                {isAuthenticated ? "Sign out" : "Login / Sign up"}
              </button>
            </div>
          </div>
          <div className="hidden items-center gap-8 text-xs font-medium text-muted md:flex">
            {navLinks.map((link) => (
              link.href.startsWith("#") ? (
                <a
                  key={link.label}
                  href={link.href}
                  className="tracking-[0.36em] uppercase transition duration-300 hover:text-soft"
                >
                  {link.label}
                </a>
              ) : (
                <Link
                  key={link.label}
                  href={link.href}
                  className="tracking-[0.36em] uppercase transition duration-300 hover:text-soft"
                >
                  {link.label}
                </Link>
              )
            ))}
          </div>
          <div className="hidden items-center gap-3 md:flex">
            <ThemeToggle />
            {socialLinks.map((item) => (
              <SocialIcon key={item.label} href={item.href} label={item.label}>
                {item.icon}
              </SocialIcon>
            ))}
            {isAuthenticated && planLabel ? (
              <span className="inline-flex items-center gap-[6px] rounded-full border border-[rgba(148,163,184,0.35)] bg-[var(--surface-card-soft)] px-3 py-[6px] text-[0.6rem] font-semibold uppercase tracking-[0.32em] text-soft">
                <span className="h-1.5 w-1.5 rounded-full bg-gradient-to-br from-cyan-400 to-emerald-400" />
                {planLabel}
              </span>
            ) : null}
            <button
              type="button"
              disabled={status === "loading"}
              onClick={handleAuthButtonClick}
              className="inline-flex items-center gap-2 rounded-full border border-[rgba(148,163,184,0.35)] bg-[var(--surface-card)] px-5 py-1.5 text-xs font-semibold uppercase tracking-[0.28em] text-soft transition duration-200 hover:-translate-y-0.5 hover:border-[rgba(148,163,184,0.55)] hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-400 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {isAuthenticated ? "Sign out" : "Login / Sign up"}
            </button>
          </div>
        </nav>

        <section className="flex flex-col items-center gap-6 text-center">
          <p className="text-xs uppercase tracking-[0.4em] text-muted">
            Precision prompt engineering
          </p>
          <h1 className="hero-gradient-text text-4xl font-semibold md:text-6xl">
            A Fast Prompt. <br className="hidden md:block" /> Scalable Guidance.
          </h1>
          <h2 className="text-3xl font-semibold text-soft md:text-5xl">
            <DecryptedText
              phrases={HERO_TAGLINES}
              interval={5200}
              duration={1400}
              className="block text-soft whitespace-nowrap"
            />
          </h2>
          <p className="max-w-2xl text-base leading-relaxed text-muted md:text-lg">
            From quick iterations to production-ready briefs, PromptTriage refines your ideas
            into crisp instructions tailored for any model. Turn vague requests into structured,
            high-impact prompts—without losing your creative spark.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <a className="cta-primary" href="#prompt-refiner">
              Get started
            </a>
            <a className="cta-secondary" href="#blueprint">
              View blueprint
            </a>
          </div>
        </section>

        <div className="flex items-center justify-center gap-3 md:hidden">
          {socialLinks.map((item) => (
            <SocialIcon key={item.label} href={item.href} label={item.label}>
              {item.icon}
            </SocialIcon>
          ))}
          {isAuthenticated && planLabel ? (
            <span className="inline-flex items-center gap-[6px] rounded-full border border-[rgba(148,163,184,0.35)] bg-[var(--surface-card-soft)] px-3 py-[6px] text-[0.6rem] font-semibold uppercase tracking-[0.32em] text-soft">
              <span className="h-1.5 w-1.5 rounded-full bg-gradient-to-br from-cyan-400 to-emerald-400" />
              {planLabel}
            </span>
          ) : null}
        </div>

        <div className="prompt-panel-shell">
          <form
            id="prompt-refiner"
            onSubmit={handleAnalyze}
            className="prompt-panel space-y-6 rounded-3xl theme-card p-8 shadow-xl shadow-slate-950/40"
          >
          <div className="space-y-2">
            <label
              htmlFor="prompt"
              className="text-sm font-medium text-soft"
            >
              Prompt to refine
            </label>
            <textarea
              id="prompt"
              name="prompt"
              rows={8}
              required
              placeholder="Describe the task you want an AI to complete..."
              className="w-full rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-card-strong)] p-4 text-base text-[var(--foreground)] placeholder:text-muted transition-all duration-300 ease-out focus:-translate-y-0.5 focus:scale-[1.01] focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/30"
              value={form.prompt}
              onChange={(event) => handleFormChange("prompt", event.target.value)}
            />
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-2">
              <label
                htmlFor="targetModel"
                className="text-sm font-medium text-soft"
              >
                Target AI model
              </label>
              <div className="flex gap-3">
                <select
                  id="targetModel"
                  name="targetModel"
                  className="flex-1 rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-card-strong)] px-4 py-2.5 text-base text-[var(--foreground)] placeholder:text-muted transition-all duration-300 ease-out focus:-translate-y-0.5 focus:scale-[1.01] focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/30"
                  value={form.targetModel}
                  onChange={(event) =>
                    handleFormChange("targetModel", event.target.value)
                  }
                >
                  {MODEL_PRESETS.map((model) => (
                    <option key={model} value={model}>
                      {model}
                    </option>
                  ))}
                </select>
              </div>
              <p className="text-sm text-muted">
                Tailor the prompt format and structure to the model you plan to
                use, or pick &quot;None / Not sure yet&quot; if you&apos;re undecided.
              </p>
            </div>

            <div className="space-y-2">
              <label
                htmlFor="context"
                className="text-sm font-medium text-soft"
              >
                Extra context (optional)
              </label>
              <textarea
                id="context"
                name="context"
                rows={4}
                placeholder="Domain knowledge, constraints, success metrics, or any background the model should know."
                className="w-full rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-card-strong)] p-3 text-base text-[var(--foreground)] placeholder:text-muted transition-all duration-300 ease-out focus:-translate-y-0.5 focus:scale-[1.01] focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/30"
                value={form.context}
                onChange={(event) =>
                  handleFormChange("context", event.target.value)
                }
              />
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-2">
              <label htmlFor="tone" className="text-sm font-medium text-soft">
                Desired tone (optional)
              </label>
              <input
                id="tone"
                name="tone"
                type="text"
                placeholder="e.g. friendly, expert, concise, marketing-savvy"
                className="w-full rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-card-strong)] px-4 py-2.5 text-base text-[var(--foreground)] placeholder:text-muted transition-all duration-300 ease-out focus:-translate-y-0.5 focus:scale-[1.01] focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/30"
                value={form.tone}
                onChange={(event) => handleFormChange("tone", event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <label
                htmlFor="outputRequirements"
                className="text-sm font-medium text-soft"
              >
                Output requirements (optional)
              </label>
              <input
                id="outputRequirements"
                name="outputRequirements"
                type="text"
                placeholder="Formatting, length, structure, evaluation criteria..."
                className="w-full rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-card-strong)] px-4 py-2.5 text-base text-[var(--foreground)] placeholder:text-muted transition-all duration-300 ease-out focus:-translate-y-0.5 focus:scale-[1.01] focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/30"
                value={form.outputRequirements}
                onChange={(event) =>
                  handleFormChange("outputRequirements", event.target.value)
                }
              />
            </div>
          </div>

          <div className="rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-card-soft)] p-4">
            <label
              htmlFor="useWebSearch"
              className="flex items-center gap-3 text-sm font-medium text-soft"
            >
              <input
                id="useWebSearch"
                name="useWebSearch"
                type="checkbox"
                className="h-4 w-4 rounded border-[var(--surface-border)] bg-[var(--surface-card-strong)] text-cyan-400 transition duration-200 ease-out focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:ring-offset-0 checked:shadow-[0_0_12px_rgba(56,189,248,0.45)]"
                checked={form.useWebSearch}
                disabled={!isPaidPlan}
                onChange={(event) => handleWebSearchToggle(event.target.checked)}
              />
              Enrich analysis with web search (Firecrawl)
            </label>
            <p className="mt-2 text-xs text-muted">{firecrawlHelperText}</p>
          </div>

          {error && stage === "collect" ? (
            <p className="rounded-2xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
              {error}
            </p>
          ) : null}

          <div className="flex flex-wrap gap-3">
            <button
              type="submit"
              disabled={isAnalyzing || !form.prompt.trim()}
              className="inline-flex items-center justify-center rounded-2xl bg-cyan-500/90 px-6 py-3 text-base font-semibold text-slate-900 shadow-[0_20px_45px_-28px_rgba(34,211,238,0.85)] transition-transform duration-300 ease-out hover:-translate-y-0.5 hover:scale-[1.03] hover:bg-cyan-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-400 disabled:translate-y-0 disabled:scale-100 disabled:cursor-not-allowed disabled:bg-[var(--surface-card-soft)] disabled:text-muted"
            >
              <span className="flex items-center gap-2">
                <span>{isAnalyzing ? "Analyzing prompt..." : "Analyze prompt"}</span>
                {isAnalyzing ? <ThinkingIndicator color="cyan" /> : null}
              </span>
            </button>
            <button
              type="button"
              onClick={handleReset}
              className="inline-flex items-center justify-center rounded-2xl border border-[var(--surface-border)] px-6 py-3 text-base font-semibold text-soft transition-transform duration-300 ease-out hover:-translate-y-0.5 hover:scale-[1.02] hover:border-[rgba(148,163,184,0.65)] hover:text-[var(--foreground)]"
            >
              Reset
            </button>
          </div>
        </form>
      </div>

        {analysis ? (
          <section className="space-y-8 rounded-3xl theme-card p-8 shadow-[0_45px_120px_-80px_rgba(15,118,110,0.65)] transition duration-500">
            <header className="space-y-2">
              <p className="text-xs uppercase tracking-[0.3em] text-cyan-300">
                phase 02
              </p>
              <h2 className="text-2xl font-semibold text-soft md:text-3xl">
                Gemini&apos;s take on your prompt
              </h2>
              <p className="text-muted">
                Review the critique and provide answers so we can tailor the
                final prompt perfectly for {form.targetModel}.
              </p>
            </header>

            <div className="grid gap-6 md:grid-cols-[2fr,3fr]">
              <div className="space-y-4 rounded-2xl theme-card-strong p-6 transition duration-300">
                <h3 className="text-lg font-semibold text-soft">
                  Strengths & gaps
                </h3>
                <p className="text-muted">{analysis.analysis}</p>
                <div className="space-y-2">
                  <p className="text-sm font-medium text-soft">
                    Missing details to address
                  </p>
                  <ul className="list-disc space-y-2 pl-5 text-sm text-muted">
                    {analysis.improvementAreas?.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
                {analysis.overallConfidence ? (
                  <p className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
                    Readiness: {analysis.overallConfidence}
                  </p>
                ) : null}

                {analysis.externalContextError ? (
                  <p className="rounded-xl theme-info px-4 py-3 text-xs text-muted">
                    {analysis.externalContextError}
                  </p>
                ) : null}

                {blueprint ? (
                  <div className="space-y-4 rounded-2xl theme-card-soft p-5">
                    <h4 className="text-base font-semibold text-soft">
                      Blueprint summary
                    </h4>
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="space-y-1">
                        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-muted">
                          Intent
                        </p>
                        <p className="text-sm text-soft">
                          {blueprint.intent}
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-muted">
                          Audience
                        </p>
                        <p className="text-sm text-soft">
                          {blueprint.audience}
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-muted">
                          Tone
                        </p>
                        <p className="text-sm text-soft">
                          {blueprint.tone}
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-muted">
                          Output format
                        </p>
                        <p className="text-sm text-soft">
                          {blueprint.outputFormat}
                        </p>
                      </div>
                    </div>

                    <div className="grid gap-6 md:grid-cols-2">
                      <div className="space-y-2">
                        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-muted">
                          Success criteria
                        </p>
                        <ul className="list-disc space-y-2 pl-5 text-sm text-muted">
                          {blueprint.successCriteria.map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                      </div>
                      <div className="space-y-2">
                        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-muted">
                          Required inputs
                        </p>
                        <ul className="list-disc space-y-2 pl-5 text-sm text-muted">
                          {blueprint.requiredInputs.map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <p className="text-xs font-semibold uppercase tracking-[0.3em] text-muted">
                        Domain context
                      </p>
                      <ul className="list-disc space-y-2 pl-5 text-sm text-muted">
                        {blueprint.domainContext.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="grid gap-6 md:grid-cols-2">
                      <div className="space-y-2">
                        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-muted">
                          Constraints & guardrails
                        </p>
                        <ul className="list-disc space-y-2 pl-5 text-sm text-muted">
                          {blueprint.constraints.map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                      </div>
                      <div className="space-y-2">
                        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-muted">
                          Risks to watch
                        </p>
                        <ul className="list-disc space-y-2 pl-5 text-sm text-muted">
                          {blueprint.risks.map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <p className="text-xs font-semibold uppercase tracking-[0.3em] text-muted">
                        Evaluation checklist
                      </p>
                      <ul className="list-disc space-y-2 pl-5 text-sm text-muted">
                        {blueprint.evaluationChecklist.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ) : null}

                {analysis.externalContext?.length ? (
                  <div className="space-y-2 rounded-2xl theme-info p-5 text-muted">
                    <p className="text-sm font-semibold text-soft">
                      Supporting sources
                    </p>
                    <ul className="space-y-3 text-xs">
                      {analysis.externalContext.map((item) => (
                        <li key={item.url} className="space-y-1">
                          <a
                            href={item.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-medium text-soft underline underline-offset-2 transition hover:text-white"
                          >
                            {item.title}
                          </a>
                          <p className="leading-relaxed text-muted">
                            {item.snippet}
                          </p>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </div>

              <form
                onSubmit={handleRefine}
                className="space-y-6 rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-card)] p-6 backdrop-blur-sm transition duration-300"
              >
                <h3 className="text-lg font-semibold text-soft">
                  Clarifying questions
                </h3>
                <div className="space-y-6">
                  {analysis.questions.map((question) => (
                    <div key={question.id} className="space-y-2">
                      <label
                        htmlFor={`answer-${question.id}`}
                        className="text-sm font-medium text-soft"
                      >
                        {question.question}
                      </label>
                      {question.purpose ? (
                        <p className="text-xs text-muted">
                          Why it matters: {question.purpose}
                        </p>
                      ) : null}
                      <textarea
                        id={`answer-${question.id}`}
                        name={question.id}
                        rows={3}
                        required
                        className="w-full rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-card-strong)] p-3 text-sm text-[var(--foreground)] placeholder:text-muted transition-all duration-300 ease-out focus:-translate-y-0.5 focus:scale-[1.01] focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/30"
                        placeholder="Type your answer..."
                        value={answers[question.id] ?? ""}
                        onChange={(event) =>
                          handleAnswerChange(question.id, event.target.value)
                        }
                      />
                    </div>
                  ))}
                </div>

                {error && stage !== "collect" ? (
                  <p className="rounded-2xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                    {error}
                  </p>
                ) : null}

                <button
                  type="submit"
                  disabled={isRefining || unansweredQuestions}
                  className="group relative inline-flex w-full items-center justify-center overflow-hidden rounded-2xl bg-emerald-500/90 px-6 py-3 text-base font-semibold text-emerald-950 shadow-[0_25px_55px_-30px_rgba(16,185,129,0.85)] transition-transform duration-300 ease-out hover:-translate-y-0.5 hover:scale-[1.03] hover:bg-emerald-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-400 disabled:translate-y-0 disabled:scale-100 disabled:cursor-not-allowed disabled:bg-[var(--surface-card-soft)] disabled:text-muted"
                >
                  <span className="flex items-center gap-2">
                    <span>
                      {isRefining
                        ? "Generating refined prompt..."
                        : unansweredQuestions
                          ? "Answer all questions to continue"
                          : "Generate refined prompt"}
                    </span>
                    {isRefining ? <ThinkingIndicator color="emerald" /> : null}
                  </span>
                  <span className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-40">
                    <span className="absolute inset-y-0 left-0 w-1/2 -translate-x-full bg-gradient-to-r from-transparent via-white/40 to-transparent animate-shimmer" />
                  </span>
                </button>
              </form>
            </div>
          </section>
      ) : null}

        {refinement ? (
          <section className="space-y-6 rounded-3xl theme-card p-8 shadow-[0_55px_150px_-90px_rgba(14,116,144,0.75)] transition duration-500">
            <header className="space-y-2">
              <p className="text-xs uppercase tracking-[0.3em] text-emerald-300">
                phase 03
              </p>
              <h2 className="text-2xl font-semibold text-soft md:text-3xl">
                Your AI-ready prompt
              </h2>
              <p className="text-muted">
                Copy it straight into {form.targetModel} or tweak it if you need
                a slightly different angle.
              </p>
            </header>

            <div className="flex flex-col gap-4 rounded-2xl theme-card-strong p-6 transition duration-300">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h3 className="text-lg font-semibold text-soft">
                  Refined prompt
                </h3>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={handleRewrite}
                    disabled={isRefining || unansweredQuestions}
                    className="inline-flex items-center justify-center rounded-xl border border-emerald-500/40 bg-emerald-500/10 px-4 py-2 text-sm font-medium text-emerald-100 transition-transform duration-300 ease-out hover:-translate-y-0.5 hover:scale-[1.02] hover:border-emerald-400 hover:bg-emerald-400/20 disabled:translate-y-0 disabled:scale-100 disabled:cursor-not-allowed disabled:border-[var(--surface-border)] disabled:bg-[var(--surface-card-soft)] disabled:text-muted"
                  >
                    <span className="flex items-center gap-2">
                      <span>{isRefining ? "Rewriting..." : "Re-write with new angle"}</span>
                      {isRefining ? <ThinkingIndicator color="emerald" /> : null}
                    </span>
                  </button>
                  <button
                    type="button"
                    onClick={handleCopy}
                    className="inline-flex items-center justify-center rounded-xl border border-[var(--surface-border)] px-4 py-2 text-sm font-medium text-soft transition-transform duration-300 ease-out hover:-translate-y-0.5 hover:scale-[1.02] hover:border-[rgba(148,163,184,0.65)] hover:text-[var(--foreground)]"
                  >
                    {copied ? "Copied!" : "Copy to clipboard"}
                  </button>
                </div>
              </div>
              <pre className="whitespace-pre-wrap rounded-2xl theme-card-soft p-4 text-soft">
                {refinement.refinedPrompt}
              </pre>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
              <div className="space-y-2 rounded-2xl theme-card-soft p-6 transition duration-300">
                <h3 className="text-lg font-semibold text-soft">
                  Usage guidance
                </h3>
                <p className="text-sm text-muted">{refinement.guidance}</p>
              </div>
              <div className="space-y-2 rounded-2xl theme-card-soft p-6 transition duration-300">
                <h3 className="text-lg font-semibold text-soft">
                  Change summary
                </h3>
                <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
                  {refinement.changeSummary.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>

            {refinement.assumptions.length ? (
              <div className="space-y-2">
                <h3 className="text-sm font-semibold text-soft">
                  Assumptions we made
                </h3>
                <ul className="list-disc space-y-2 rounded-2xl theme-card-soft p-5 pl-8 text-sm text-muted">
                  {refinement.assumptions.map((assumption) => (
                    <li key={assumption}>{assumption}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            {refinement.evaluationCriteria.length ? (
              <div className="space-y-2">
                <h3 className="text-sm font-semibold text-soft">
                  Evaluate the AI&apos;s response with these checkpoints
                </h3>
                <ul className="list-disc space-y-2 rounded-2xl theme-card-soft p-5 pl-8 text-sm text-muted">
                  {refinement.evaluationCriteria.map((criterion) => (
                    <li key={criterion}>{criterion}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </section>
        ) : null}
      </main>
    </div>
  );
}
