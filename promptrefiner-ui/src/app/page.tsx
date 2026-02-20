'use client';

import { FormEvent, ReactNode, useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import type { User } from "@supabase/supabase-js";
import { createClient } from "@/lib/supabase/client";
import { useTheme } from "@/components/theme-provider";
import { DecryptedText } from "@/components/decrypted-text";
import { OutputFormatSelector, OutputFormatId } from "@/components/OutputFormatSelector";
import { ModalitySelector, Modality, MODALITY_CONFIG } from "@/components/ModalitySelector";
import { ImageUploader, UploadedImage } from "@/components/ImageUploader";
import { DesiredOutputSelector, DesiredOutputId } from "@/components/DesiredOutputSelector";
import ErrorFeedback from "@/components/ErrorFeedback";
import PipelineProgress from "@/components/PipelineProgress";
import { motion } from "framer-motion";
import { Github, Instagram, ArrowUpRight, Moon, Sun, Menu, X } from "lucide-react";

import type {
  PromptAnalysisResult,
  PromptRefinementResult,
} from "@/types/prompt";

type RefinementStage = "collect" | "analyzed" | "refined";
type PendingAction = "analyze" | "refine" | null;

// Auto-derive vendor from the selected target model for RAG namespace routing
function deriveVendorFromModel(model: string): string | undefined {
  const lower = model.toLowerCase();
  if (lower.includes("anthropic") || lower.includes("claude")) return "anthropic";
  if (lower.includes("openai") || lower.includes("gpt") || lower.includes("chatgpt") || lower.includes("o-series") || lower.includes("dall-e") || lower.includes("sora")) return "openai";
  if (lower.includes("google") || lower.includes("gemini") || lower.includes("imagen") || lower.includes("veo")) return "google";
  return undefined;
}

const INITIAL_FORM = {
  prompt: "",
  modality: "text" as Modality,
  targetModel: MODALITY_CONFIG.text.models[0] as string,
  context: "",
  tone: "",
  outputFormats: [] as OutputFormatId[],
  desiredOutput: null as DesiredOutputId | null,

  useWebSearch: false,
  images: [] as UploadedImage[],
  thinkingMode: false,
};

const HERO_TAGLINES = [
  "Powered by 28,000+ expert-analyzed prompt patterns.",
  "Turn vague ideas into precise, model-ready instructions.",
  "Your prompts, refined by real prompt engineering data.",
  "Built on patterns from leading AI systems worldwide.",
  "From rough draft to production-ready in seconds.",
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

function ThinkingIndicator({ color = "white" }: { color?: "white" | "slate" }) {
  const palette: Record<string, string> = {
    white: "bg-white/80 shadow-[0_0_8px_rgba(255,255,255,0.4)]",
    slate: "bg-slate-300 shadow-[0_0_6px_rgba(148,163,184,0.45)]",
  };

  return (
    <span className="inline-flex items-center gap-[3px]">
      {Array.from({ length: 3 }).map((_, index) => (
        <span
          key={index}
          className={`h-1.5 w-1.5 rounded-full animate-dotPulse ${palette[color] ?? palette.white
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
      className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-[rgba(148,163,184,0.2)] bg-transparent text-[var(--text-muted)] transition duration-300 hover:scale-110 hover:border-[rgba(148,163,184,0.5)] hover:text-[var(--foreground)]"
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
      className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-[rgba(148,163,184,0.2)] bg-transparent text-[var(--text-muted)] transition duration-300 hover:scale-110 hover:border-[rgba(148,163,184,0.5)] hover:text-[var(--foreground)]"
      aria-label="Toggle theme"
    >
      {isLight ? <Moon className="h-3.5 w-3.5" /> : <Sun className="h-3.5 w-3.5" />}
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
    { label: "Refiner", href: "#prompt-refiner" },
    { label: "Pricing", href: "/pricing" },
  ];

  const socialLinks = [
    {
      label: "GitHub",
      href: "https://github.com/Ker102/PromptTriage",
      icon: <Github className="h-3.5 w-3.5" />,
    },
    {
      label: "Instagram",
      href: "https://instagram.com/kaelux.dev",
      icon: <Instagram className="h-3.5 w-3.5" />,
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
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  // Modify feature: allow user to refine the generated prompt with additional instructions
  const [showModifyInput, setShowModifyInput] = useState(false);
  const [modifyInstruction, setModifyInstruction] = useState("");
  // ── Supabase Auth ──
  const [supabase] = useState(() => createClient());
  const [user, setUser] = useState<User | null>(null);
  const [authLoading, setAuthLoading] = useState(true);

  useEffect(() => {
    // Get initial user
    supabase.auth.getUser().then(({ data: { user: u } }) => {
      setUser(u);
      setAuthLoading(false);
    });
    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setUser(session?.user ?? null);
        setAuthLoading(false);
      },
    );
    return () => subscription.unsubscribe();
  }, [supabase]);

  // Fetch subscription plan from server-side subscriptions table
  const [serverPlan, setServerPlan] = useState<string>("FREE");
  useEffect(() => {
    if (user) {
      fetch("/api/subscription")
        .then((r) => r.json())
        .then((data) => setServerPlan(data.plan ?? "FREE"))
        .catch(() => setServerPlan("FREE"));
    }
  }, [user]);

  const subscriptionPlan = serverPlan;
  const planLabel = formatPlanLabel(subscriptionPlan === "FREE" ? null : subscriptionPlan);
  // Dev bypass: treat as paid plan for UI testing when NEXT_PUBLIC_DEV_SUPERUSER is true
  const isDevSuperuser = process.env.NEXT_PUBLIC_DEV_SUPERUSER === "true";
  const isPaidPlan = subscriptionPlan !== "FREE" || isDevSuperuser;
  const firecrawlHelperText = isPaidPlan
    ? "Pulls supporting facts from the web to help our AI identify missing context. Requires a valid FIRECRAWL_API_KEY."
    : "Available on Pro plans. Upgrade to unlock Firecrawl web search for richer context.";

  const isAuthenticated = !!user;
  const handleAuthButtonClick = useCallback(async () => {
    if (isAuthenticated) {
      await supabase.auth.signOut();
      return;
    }
    await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    });
  }, [isAuthenticated, supabase]);

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

    // Require authentication — redirect to login page if not signed in
    if (!isAuthenticated) {
      window.location.href = "/login";
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
          tone: form.tone || undefined,
          outputFormats: form.outputFormats.length > 0 ? form.outputFormats : undefined,
          desiredOutput: form.desiredOutput || undefined,
          targetVendor: deriveVendorFromModel(form.targetModel),
          modality: form.modality,
          thinkingMode: form.thinkingMode,
          useWebSearch: form.useWebSearch || undefined,
          images: form.images.length > 0 ? form.images : undefined,
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

    // Require authentication — redirect to login page if not signed in
    if (!isAuthenticated) {
      window.location.href = "/login";
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
          outputFormats: form.outputFormats.length ? form.outputFormats : undefined,
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

  // Fast Mode: Use refinedPrompt directly from analysis (no refine API call needed)
  const handleFastModeRefine = () => {
    if (!analysis?.refinedPrompt) {
      setError("No refined prompt available. Please try again.");
      return;
    }

    // Set the refinement result directly using the analysis.refinedPrompt
    setRefinement({
      refinedPrompt: analysis.refinedPrompt,
      guidance: analysis.analysis || "Fast Mode optimization applied.",
      changeSummary: analysis.improvementAreas || [],
      assumptions: [],
      evaluationCriteria: analysis.blueprint?.evaluationChecklist || [],
    });
    setStage("refined");
    setRewriteCount(0);
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

  // Handle modify: refine the current prompt with user's additional instructions
  const handleModify = async () => {
    if (!modifyInstruction.trim() || !refinement?.refinedPrompt || pendingAction === "refine") {
      return;
    }

    const modifyHint = `The user wants to modify the generated prompt with these instructions: "${modifyInstruction}"\n\nCurrent generated prompt:\n${refinement.refinedPrompt}\n\nApply the user's modification request while preserving the original intent and quality.`;
    const success = await submitRefine(modifyHint);
    if (success) {
      setModifyInstruction("");
      setShowModifyInput(false);
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
    setShowModifyInput(false);
    setModifyInstruction("");
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
    <div className="relative min-h-screen bg-[var(--background)] text-[var(--foreground)] transition-colors duration-500 overflow-hidden">
      {/* Background Crystals (Light Mode) */}
      <div className="absolute inset-0 pointer-events-none z-0 dark:hidden">
        <img src="/whitebgcrystals/Layer 0 - 15whitebg.png" alt="" className="absolute -left-16 top-20 w-72 h-auto drop-shadow-[0_20px_40px_rgba(0,0,0,0.15)] opacity-80" />
        <img src="/whitebgcrystals/Layer 0 - 6whitebg.png" alt="" className="absolute -right-20 top-64 w-64 h-auto drop-shadow-[0_20px_40px_rgba(0,0,0,0.15)] opacity-80" />
        <img src="/whitebgcrystals/Layer 0 - 12whitebg.png" alt="" className="absolute left-4 top-[500px] w-56 h-auto drop-shadow-[0_20px_40px_rgba(0,0,0,0.15)] opacity-80" />
        <img src="/whitebgcrystals/Layer 0 - 5whitebg.png" alt="" className="absolute right-12 top-[750px] w-72 h-auto drop-shadow-[0_20px_40px_rgba(0,0,0,0.15)] opacity-80" />
      </div>

      {/* Background Crystals (Dark Mode) */}
      <div className="absolute inset-0 pointer-events-none z-0 hidden dark:block">
        <img src="/blackbgcrystals/Layer 0 - 15blackbg.png" alt="" className="absolute -left-16 top-20 w-72 h-auto drop-shadow-[0_20px_40px_rgba(0,0,0,0.6)] opacity-70" />
        <img src="/blackbgcrystals/Layer 0 - 6blackbg.png" alt="" className="absolute -right-20 top-64 w-64 h-auto drop-shadow-[0_20px_40px_rgba(0,0,0,0.6)] opacity-70" />
        <img src="/blackbgcrystals/Layer 0 - 1blackbg.png" alt="" className="absolute left-4 top-[500px] w-56 h-auto drop-shadow-[0_20px_40px_rgba(0,0,0,0.6)] opacity-70" />
        <img src="/blackbgcrystals/Layer 0 - 5blackbg.png" alt="" className="absolute right-12 top-[750px] w-72 h-auto drop-shadow-[0_20px_40px_rgba(0,0,0,0.6)] opacity-70" />
      </div>

      <main className="relative z-10 mx-auto flex w-full max-w-5xl flex-col gap-10 px-4 pt-6 pb-12 md:px-6">
        {/* ── Liquid Glass Navigation ── */}
        <motion.nav
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="liquid-glass-nav sticky top-4 z-50 mx-auto flex w-full max-w-3xl items-center justify-between px-4 py-2.5 md:px-5"
        >
          <span className="text-sm font-semibold uppercase tracking-[0.3em] text-soft">
            PromptTriage
          </span>

          {/* Desktop nav */}
          <div className="hidden items-center gap-6 text-xs font-medium text-muted md:flex">
            {navLinks.map((link) =>
              link.href.startsWith("#") ? (
                <a
                  key={link.label}
                  href={link.href}
                  className="nav-link tracking-[0.2em] uppercase transition duration-300 hover:text-[var(--foreground)]"
                >
                  {link.label}
                </a>
              ) : (
                <Link
                  key={link.label}
                  href={link.href}
                  className="nav-link tracking-[0.2em] uppercase transition duration-300 hover:text-[var(--foreground)]"
                >
                  {link.label}
                </Link>
              )
            )}
          </div>

          <div className="hidden items-center gap-2 md:flex">
            <ThemeToggle />
            {socialLinks.map((item) => (
              <SocialIcon key={item.label} href={item.href} label={item.label}>
                {item.icon}
              </SocialIcon>
            ))}
            {isAuthenticated && planLabel ? (
              <span className="inline-flex items-center gap-[5px] rounded-full border border-[rgba(148,163,184,0.2)] px-2.5 py-1 text-[0.55rem] font-semibold uppercase tracking-[0.2em] text-muted">
                <span className="h-1.5 w-1.5 rounded-full bg-white/70" />
                {planLabel}
              </span>
            ) : null}
            {isAuthenticated ? (
              <button
                type="button"
                onClick={handleAuthButtonClick}
                className="inline-flex items-center gap-1.5 rounded-full border border-[rgba(148,163,184,0.25)] px-4 py-1.5 text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-muted transition duration-300 hover:border-[rgba(148,163,184,0.5)] hover:text-[var(--foreground)]"
              >
                Sign out
              </button>
            ) : (
              <a
                href="/login"
                className="inline-flex items-center gap-1.5 rounded-full border border-[rgba(148,163,184,0.25)] px-4 py-1.5 text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-muted transition duration-300 hover:border-[rgba(148,163,184,0.5)] hover:text-[var(--foreground)]"
              >
                Sign in
              </a>
            )}
          </div>

          {/* Mobile hamburger */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-[rgba(148,163,184,0.2)] bg-transparent text-[var(--text-muted)] transition duration-300 hover:text-[var(--foreground)] md:hidden"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </button>
        </motion.nav>

        {/* Mobile menu overlay */}
        {mobileMenuOpen && (
          <div className="fixed inset-x-0 top-[68px] z-40 mx-auto w-full max-w-3xl px-4 md:hidden">
            <div className="rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-card-strong)] p-5 shadow-2xl backdrop-blur-xl">
              <div className="flex flex-col gap-4">
                {navLinks.map((link) =>
                  link.href.startsWith("#") ? (
                    <a
                      key={link.label}
                      href={link.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className="text-sm font-medium uppercase tracking-[0.2em] text-soft transition hover:text-[var(--foreground)]"
                    >
                      {link.label}
                    </a>
                  ) : (
                    <Link
                      key={link.label}
                      href={link.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className="text-sm font-medium uppercase tracking-[0.2em] text-soft transition hover:text-[var(--foreground)]"
                    >
                      {link.label}
                    </Link>
                  )
                )}
                <div className="h-px bg-[var(--surface-border)]" />
                <div className="flex items-center gap-3">
                  <ThemeToggle />
                  {socialLinks.map((item) => (
                    <SocialIcon key={item.label} href={item.href} label={item.label}>
                      {item.icon}
                    </SocialIcon>
                  ))}
                  {isAuthenticated && planLabel ? (
                    <span className="inline-flex items-center gap-[5px] rounded-full border border-[rgba(148,163,184,0.2)] px-2.5 py-1 text-[0.55rem] font-semibold uppercase tracking-[0.2em] text-muted">
                      <span className="h-1.5 w-1.5 rounded-full bg-white/70" />
                      {planLabel}
                    </span>
                  ) : null}
                </div>
                {isAuthenticated ? (
                  <button
                    type="button"
                    onClick={() => { handleAuthButtonClick(); setMobileMenuOpen(false); }}
                    className="inline-flex items-center justify-center rounded-full border border-[rgba(148,163,184,0.25)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-muted transition duration-300 hover:text-[var(--foreground)]"
                  >
                    Sign out
                  </button>
                ) : (
                  <a
                    href="/login"
                    onClick={() => setMobileMenuOpen(false)}
                    className="inline-flex items-center justify-center rounded-full border border-[rgba(148,163,184,0.25)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-muted transition duration-300 hover:text-[var(--foreground)]"
                  >
                    Sign in
                  </a>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ── Hero Section ── */}
        <section className="flex flex-col items-center gap-7 pt-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <Link
              href="https://kaelux.dev"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-xs uppercase tracking-[0.35em] text-muted transition duration-300 hover:text-[var(--foreground)]"
            >
              <span>A Kaelux Technologies Product</span>
              <ArrowUpRight className="h-3.5 w-3.5" />
            </Link>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.35 }}
            className="hero-gradient-text text-4xl font-semibold md:text-6xl"
          >
            Write Better Prompts. <br className="hidden md:block" /> Get Better Results.
          </motion.h1>

          <motion.h2
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            className="text-xl font-medium text-soft md:text-2xl"
          >
            <DecryptedText
              phrases={HERO_TAGLINES}
              interval={5200}
              duration={1400}
              className="block text-soft"
            />
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.65 }}
            className="max-w-2xl text-base leading-relaxed text-muted md:text-lg"
          >
            PromptTriage analyzes your prompt against a knowledge base of 28,000+ real-world
            patterns from leading AI systems — then rewrites it for maximum clarity and impact.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.8 }}
            className="flex flex-wrap items-center justify-center gap-4"
          >
            <a className="cta-primary" href="#prompt-refiner">
              Get started
            </a>
            <Link className="cta-secondary" href="/pricing">
              View pricing
            </Link>
          </motion.div>
        </section>


        <div className="prompt-panel-shell">
          <form
            id="prompt-refiner"
            onSubmit={handleAnalyze}
            className="prompt-panel space-y-6 rounded-2xl md:rounded-3xl theme-card p-4 md:p-8 shadow-xl shadow-slate-950/40"
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
                className="w-full rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-card-strong)] p-4 text-base text-[var(--foreground)] placeholder:text-muted transition-all duration-300 ease-out focus:-translate-y-0.5 focus:scale-[1.01] focus:border-white/40 focus:outline-none focus:ring-2 focus:ring-white/20"
                value={form.prompt}
                onChange={(event) => handleFormChange("prompt", event.target.value)}
              />
            </div>

            <div className="space-y-4">
              <ModalitySelector
                modality={form.modality}
                model={form.targetModel}
                onModalityChange={(mod) => setForm((prev) => ({ ...prev, modality: mod }))}
                onModelChange={(model) => setForm((prev) => ({ ...prev, targetModel: model }))}
              />
            </div>

            {/* Image upload for image/video modalities */}
            {(form.modality === "image" || form.modality === "video") && (
              <div className="space-y-2">
                <ImageUploader
                  images={form.images}
                  onChange={(images) => setForm((prev) => ({ ...prev, images }))}
                  maxImages={3}
                />
                <p className="text-xs text-muted">
                  Upload reference images to help the AI understand your vision. The analyzer will describe the image context.
                </p>
              </div>
            )}

            <div className="grid gap-6 md:grid-cols-2">
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
                  className="w-full rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-card-strong)] p-3 text-base text-[var(--foreground)] placeholder:text-muted transition-all duration-300 ease-out focus:-translate-y-0.5 focus:scale-[1.01] focus:border-white/40 focus:outline-none focus:ring-2 focus:ring-white/20"
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
                  className="w-full rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-card-strong)] px-4 py-2.5 text-base text-[var(--foreground)] placeholder:text-muted transition-all duration-300 ease-out focus:-translate-y-0.5 focus:scale-[1.01] focus:border-white/40 focus:outline-none focus:ring-2 focus:ring-white/20"
                  value={form.tone}
                  onChange={(event) => handleFormChange("tone", event.target.value)}
                />
              </div>
              <div className="space-y-2">
                <label
                  htmlFor="outputFormats"
                  className="text-sm font-medium text-soft"
                >
                  Prompt structure format (optional)
                </label>
                <OutputFormatSelector
                  selected={form.outputFormats}
                  onChange={(selected) => setForm((prev) => ({ ...prev, outputFormats: selected }))}
                />
                <p className="text-xs text-muted">
                  Format of the refined prompt itself (JSON, XML, Markdown).
                </p>
              </div>
            </div>

            {/* Desired Final Output - only for Text and System modalities */}
            {(form.modality === "text" || form.modality === "system") && (
              <div className="space-y-2">
                <label
                  htmlFor="desiredOutput"
                  className="text-sm font-medium text-soft"
                >
                  Desired final output (optional)
                </label>
                <DesiredOutputSelector
                  selected={form.desiredOutput}
                  onChange={(selected) => setForm((prev) => ({ ...prev, desiredOutput: selected }))}
                />
              </div>
            )}



            <div className="rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-card-soft)] p-4">
              <label
                htmlFor="useWebSearch"
                className="flex items-center gap-3 text-sm font-medium text-soft"
              >
                <input
                  id="useWebSearch"
                  name="useWebSearch"
                  type="checkbox"
                  className="h-4 w-4 rounded border-[var(--surface-border)] bg-[var(--surface-card-strong)] text-white/80 transition duration-200 ease-out focus:outline-none focus:ring-2 focus:ring-white/30 focus:ring-offset-0 checked:shadow-[0_0_12px_rgba(255,255,255,0.15)]"
                  checked={form.useWebSearch}
                  disabled={!isPaidPlan}
                  onChange={(event) => handleWebSearchToggle(event.target.checked)}
                />
                Enrich analysis with web search (Firecrawl)
              </label>
              <p className="mt-2 text-xs text-muted">{firecrawlHelperText}</p>
            </div>

            {/* Thinking Mode Toggle */}
            <div className="rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-card-soft)] p-4">
              <label
                htmlFor="thinkingMode"
                className="flex items-center justify-between text-sm font-medium text-soft"
              >
                <div className="flex items-center gap-3">
                  <input
                    id="thinkingMode"
                    name="thinkingMode"
                    type="checkbox"
                    className="h-4 w-4 rounded border-[var(--surface-border)] bg-[var(--surface-card-strong)] text-white/80 transition duration-200 ease-out focus:outline-none focus:ring-2 focus:ring-white/30 focus:ring-offset-0 checked:shadow-[0_0_12px_rgba(255,255,255,0.2)]"
                    checked={form.thinkingMode}
                    disabled={!isPaidPlan}
                    onChange={(event) => setForm((prev) => ({ ...prev, thinkingMode: event.target.checked }))}
                  />
                  <div>
                    <span>Thinking Mode</span>
                    <span className="ml-2 rounded-full bg-white/10 px-2 py-0.5 text-xs text-slate-400">
                      Deep Analysis
                    </span>
                  </div>
                </div>
              </label>
              <p className="mt-2 text-xs text-muted">
                {isPaidPlan
                  ? "Multi-pass iterative analysis with self-critique for deeper insights."
                  : "Available on paid plans. Upgrade for deeper, multi-pass analysis."}
              </p>
            </div>

            {error && stage === "collect" ? (
              <ErrorFeedback
                errorMessage={error}
                onRetry={() => {
                  setError(null);
                  const fakeEvent = { preventDefault: () => { } } as FormEvent<HTMLFormElement>;
                  handleAnalyze(fakeEvent);
                }}
                onDismiss={() => setError(null)}
                context={{
                  modality: form.modality,
                  targetModel: form.targetModel,
                  thinkingMode: form.thinkingMode,
                  action: "analyze",
                }}
              />
            ) : null}

            <div className="flex flex-wrap gap-3">
              <button
                type="submit"
                disabled={isAnalyzing || !form.prompt.trim()}
                className="inline-flex items-center justify-center rounded-2xl bg-white/90 px-6 py-3 text-base font-semibold text-[#0f172a] shadow-[0_20px_45px_-28px_rgba(255,255,255,0.25)] transition-transform duration-300 ease-out hover:-translate-y-0.5 hover:scale-[1.03] hover:bg-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white/60 disabled:translate-y-0 disabled:scale-100 disabled:cursor-not-allowed disabled:bg-[var(--surface-card-soft)] disabled:text-muted"
              >
                <span className="flex items-center gap-2">
                  <span>{isAnalyzing ? "Analyzing prompt..." : "Analyze prompt"}</span>
                  {isAnalyzing ? <ThinkingIndicator color="white" /> : null}
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

        {/* Pipeline Progress Indicator */}
        {pendingAction && (
          <PipelineProgress
            mode={pendingAction === "analyze" ? "analyze" : "refine"}
            thinkingMode={form.thinkingMode}
          />
        )}

        {
          analysis ? (
            <section className="space-y-8 rounded-2xl md:rounded-3xl theme-card p-4 md:p-8 shadow-[0_45px_120px_-80px_rgba(148,163,184,0.15)] transition duration-500">
              <header className="space-y-2">
                <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
                  {analysis.questions?.length > 0 ? "phase 02" : "refined prompt"}
                </p>
                <h2 className="text-2xl font-semibold text-soft md:text-3xl">
                  PromptTriage&apos;s take on your prompt
                </h2>
                <p className="text-muted">
                  {analysis.questions?.length > 0
                    ? `Review the critique and provide answers so we can tailor the final prompt perfectly for ${form.targetModel}.`
                    : `Here's your refined prompt, optimized for ${form.targetModel}. Click the button below to copy or continue editing.`}
                </p>
              </header>

              {/* Fast Mode: Show button first, then full-width analysis */}
              {!analysis.questions?.length && (
                <div className="space-y-6">
                  <button
                    type="button"
                    onClick={handleFastModeRefine}
                    disabled={isRefining || !analysis.refinedPrompt}
                    className="group relative inline-flex w-full items-center justify-center overflow-hidden rounded-2xl bg-white/90 px-6 py-3 text-base font-semibold text-[#0f172a] shadow-[0_20px_45px_-28px_rgba(255,255,255,0.25)] transition-transform duration-300 ease-out hover:-translate-y-0.5 hover:scale-[1.03] hover:bg-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white/60 disabled:translate-y-0 disabled:scale-100 disabled:cursor-not-allowed disabled:bg-[var(--surface-card-soft)] disabled:text-muted"
                  >
                    <span className="flex items-center gap-2">
                      <span>
                        {!analysis.refinedPrompt
                          ? "Generating prompt..."
                          : "View refined prompt"}
                      </span>
                    </span>
                  </button>

                  <div className="space-y-4 rounded-2xl theme-card-strong p-6 transition duration-300">
                    <h3 className="text-lg font-semibold text-soft">
                      Analysis & improvements applied
                    </h3>
                    <p className="text-muted">{analysis.analysis}</p>
                    <div className="space-y-2">
                      <p className="text-sm font-medium text-soft">
                        Missing details to address
                      </p>
                      <ul className="list-disc space-y-2 pl-5 text-sm text-muted">
                        {analysis.improvementAreas?.map((item, index) => (
                          <li key={`improvement-${index}-${item.slice(0, 20)}`}>{item}</li>
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
                </div>
              )}

              {/* Thinking Mode: 2-column layout with questions */}
              {analysis.questions?.length > 0 && (
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
                            className="w-full rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-card-strong)] p-3 text-sm text-[var(--foreground)] placeholder:text-muted transition-all duration-300 ease-out focus:-translate-y-0.5 focus:scale-[1.01] focus:border-white/40 focus:outline-none focus:ring-2 focus:ring-white/20"
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
                      className="group relative inline-flex w-full items-center justify-center overflow-hidden rounded-2xl bg-white/90 px-6 py-3 text-base font-semibold text-[#0f172a] shadow-[0_20px_45px_-28px_rgba(255,255,255,0.25)] transition-transform duration-300 ease-out hover:-translate-y-0.5 hover:scale-[1.03] hover:bg-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white/60 disabled:translate-y-0 disabled:scale-100 disabled:cursor-not-allowed disabled:bg-[var(--surface-card-soft)] disabled:text-muted"
                    >
                      <span className="flex items-center gap-2">
                        <span>
                          {isRefining
                            ? "Generating refined prompt..."
                            : unansweredQuestions
                              ? "Answer all questions to continue"
                              : "Generate refined prompt"}
                        </span>
                        {isRefining ? <ThinkingIndicator color="white" /> : null}
                      </span>
                      <span className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-40">
                        <span className="absolute inset-y-0 left-0 w-1/2 -translate-x-full bg-gradient-to-r from-transparent via-white/40 to-transparent animate-shimmer" />
                      </span>
                    </button>
                  </form>
                </div>
              )}
            </section>
          ) : null
        }

        {
          refinement ? (
            <section className="space-y-6 rounded-2xl md:rounded-3xl theme-card p-4 md:p-8 shadow-[0_55px_150px_-90px_rgba(148,163,184,0.15)] transition duration-500">
              <header className="space-y-2">
                <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
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
                      className="inline-flex items-center justify-center rounded-xl border border-white/20 bg-white/5 px-4 py-2 text-sm font-medium text-slate-200 transition-transform duration-300 ease-out hover:-translate-y-0.5 hover:scale-[1.02] hover:border-white/40 hover:bg-white/20 disabled:translate-y-0 disabled:scale-100 disabled:cursor-not-allowed disabled:border-[var(--surface-border)] disabled:bg-[var(--surface-card-soft)] disabled:text-muted"
                    >
                      <span className="flex items-center gap-2">
                        <span>{isRefining ? "Rewriting..." : "Re-write with new angle"}</span>
                        {isRefining ? <ThinkingIndicator color="white" /> : null}
                      </span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowModifyInput(!showModifyInput)}
                      disabled={isRefining}
                      className="inline-flex items-center justify-center rounded-xl border border-white/20 bg-white/5 px-4 py-2 text-sm font-medium text-slate-200 transition-transform duration-300 ease-out hover:-translate-y-0.5 hover:scale-[1.02] hover:border-white/40 hover:bg-white/20 disabled:translate-y-0 disabled:scale-100 disabled:cursor-not-allowed disabled:border-[var(--surface-border)] disabled:bg-[var(--surface-card-soft)] disabled:text-muted"
                    >
                      {showModifyInput ? "Cancel" : "Modify"}
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

                {/* Modify Input Section */}
                {showModifyInput && (
                  <div className="space-y-3 rounded-2xl border border-white/15 bg-white/[0.03] p-4">
                    <label className="text-sm font-medium text-soft">
                      How would you like to modify this prompt?
                    </label>
                    <textarea
                      value={modifyInstruction}
                      onChange={(e) => setModifyInstruction(e.target.value)}
                      placeholder="e.g., Make it more formal, add more detail about X, shorten the introduction..."
                      rows={3}
                      className="w-full rounded-xl border border-[var(--surface-border)] bg-[var(--surface-card)] p-3 text-sm text-[var(--foreground)] placeholder:text-muted transition-all duration-300 focus:border-white/40 focus:outline-none focus:ring-2 focus:ring-white/20"
                    />
                    <button
                      type="button"
                      onClick={handleModify}
                      disabled={isRefining || !modifyInstruction.trim()}
                      className="inline-flex items-center justify-center rounded-xl bg-white/90 px-4 py-2 text-sm font-medium text-[#0f172a] transition-transform duration-300 ease-out hover:-translate-y-0.5 hover:scale-[1.02] hover:bg-white disabled:translate-y-0 disabled:scale-100 disabled:cursor-not-allowed disabled:bg-[var(--surface-card-soft)] disabled:text-muted"
                    >
                      <span className="flex items-center gap-2">
                        <span>{isRefining ? "Modifying..." : "Apply Modification"}</span>
                        {isRefining ? <ThinkingIndicator color="white" /> : null}
                      </span>
                    </button>
                  </div>
                )}
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
          ) : null
        }
      </main>

      {/* Footer */}
      <footer className="mx-auto w-full max-w-5xl border-t border-[var(--surface-border)] px-6 py-8">
        <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold uppercase tracking-[0.3em] text-muted">
              PromptTriage
            </span>
            <span className="text-xs text-muted/50">•</span>
            <span className="text-xs text-muted/70">RAG-Powered Prompt Engineering</span>
          </div>
          <div className="flex items-center gap-4">
            <a
              href="https://github.com/Kaelux Technologies/PromptTriage"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-muted transition hover:text-soft"
            >
              GitHub
            </a>
            <span className="text-xs text-muted/30">|</span>
            <span className="text-xs text-muted/50">
              © {new Date().getFullYear()} Kaelux Technologies
            </span>
          </div>
        </div>
      </footer>
    </div >
  );
}
