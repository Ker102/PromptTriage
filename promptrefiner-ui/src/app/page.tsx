'use client';

import { FormEvent, useMemo, useState } from "react";
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

export default function Home() {
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
    setForm((prev) => ({ ...prev, useWebSearch: value }));
  };

  const handleAnalyze = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

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
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <main className="mx-auto flex w-full max-w-5xl flex-col gap-10 px-6 py-12">
        <header className="space-y-3">
          <p className="text-sm uppercase tracking-[0.3em] text-slate-400">
            promptrefiner
          </p>
          <h1 className="text-4xl font-semibold text-white md:text-5xl">
            Turn rough ideas into AI-ready prompts.
          </h1>
          <p className="max-w-3xl text-lg text-slate-300">
            Paste the prompt you&apos;re working on, select the target model,
            and let Gemini highlight the gaps, ask clarifying questions, and
            craft the final optimized prompt for you.
          </p>
        </header>

        <form
          onSubmit={handleAnalyze}
          className="space-y-6 rounded-3xl border border-slate-800 bg-slate-900/60 p-8 shadow-xl shadow-slate-950/40 backdrop-blur"
        >
          <div className="space-y-2">
            <label
              htmlFor="prompt"
              className="text-sm font-medium text-slate-200"
            >
              Prompt to refine
            </label>
            <textarea
              id="prompt"
              name="prompt"
              rows={8}
              required
              placeholder="Describe the task you want an AI to complete..."
              className="w-full rounded-2xl border border-slate-800 bg-slate-950/70 p-4 text-base text-slate-100 placeholder:text-slate-500 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/30"
              value={form.prompt}
              onChange={(event) => handleFormChange("prompt", event.target.value)}
            />
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-2">
              <label
                htmlFor="targetModel"
                className="text-sm font-medium text-slate-200"
              >
                Target AI model
              </label>
              <div className="flex gap-3">
                <select
                  id="targetModel"
                  name="targetModel"
                  className="flex-1 rounded-2xl border border-slate-800 bg-slate-950/70 px-4 py-2.5 text-base text-slate-100 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/30"
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
              <p className="text-sm text-slate-500">
                Tailor the prompt format and structure to the model you plan to
                use, or pick &quot;None / Not sure yet&quot; if you&apos;re undecided.
              </p>
            </div>

            <div className="space-y-2">
              <label
                htmlFor="context"
                className="text-sm font-medium text-slate-200"
              >
                Extra context (optional)
              </label>
              <textarea
                id="context"
                name="context"
                rows={4}
                placeholder="Domain knowledge, constraints, success metrics, or any background the model should know."
                className="w-full rounded-2xl border border-slate-800 bg-slate-950/70 p-3 text-base text-slate-100 placeholder:text-slate-500 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/30"
                value={form.context}
                onChange={(event) =>
                  handleFormChange("context", event.target.value)
                }
              />
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-2">
              <label htmlFor="tone" className="text-sm font-medium text-slate-200">
                Desired tone (optional)
              </label>
              <input
                id="tone"
                name="tone"
                type="text"
                placeholder="e.g. friendly, expert, concise, marketing-savvy"
                className="w-full rounded-2xl border border-slate-800 bg-slate-950/70 px-4 py-2.5 text-base text-slate-100 placeholder:text-slate-500 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/30"
                value={form.tone}
                onChange={(event) => handleFormChange("tone", event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <label
                htmlFor="outputRequirements"
                className="text-sm font-medium text-slate-200"
              >
                Output requirements (optional)
              </label>
              <input
                id="outputRequirements"
                name="outputRequirements"
                type="text"
                placeholder="Formatting, length, structure, evaluation criteria..."
                className="w-full rounded-2xl border border-slate-800 bg-slate-950/70 px-4 py-2.5 text-base text-slate-100 placeholder:text-slate-500 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/30"
                value={form.outputRequirements}
                onChange={(event) =>
                  handleFormChange("outputRequirements", event.target.value)
                }
              />
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
            <label
              htmlFor="useWebSearch"
              className="flex items-center gap-3 text-sm font-medium text-slate-200"
            >
              <input
                id="useWebSearch"
                name="useWebSearch"
                type="checkbox"
                className="h-4 w-4 rounded border-slate-700 bg-slate-900 text-cyan-400 focus:ring-cyan-500/50"
                checked={form.useWebSearch}
                onChange={(event) => handleWebSearchToggle(event.target.checked)}
              />
              Enrich analysis with web search (Firecrawl)
            </label>
            <p className="mt-2 text-xs text-slate-400">
              Pulls supporting facts from the web to help Gemini identify missing context.
              Requires a valid FIRECRAWL_API_KEY.
            </p>
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
              className="inline-flex items-center justify-center rounded-2xl bg-cyan-500 px-6 py-3 text-base font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
            >
              {isAnalyzing ? "Analyzing prompt..." : "Analyze prompt"}
            </button>
            <button
              type="button"
              onClick={handleReset}
              className="inline-flex items-center justify-center rounded-2xl border border-slate-700 px-6 py-3 text-base font-semibold text-slate-200 transition hover:border-slate-500 hover:text-white"
            >
              Reset
            </button>
          </div>
        </form>

        {analysis ? (
          <section className="space-y-8 rounded-3xl border border-slate-800 bg-slate-900/40 p-8">
            <header className="space-y-2">
              <p className="text-xs uppercase tracking-[0.3em] text-cyan-300">
                phase 02
              </p>
              <h2 className="text-2xl font-semibold text-white md:text-3xl">
                Gemini&apos;s take on your prompt
              </h2>
              <p className="text-slate-300">
                Review the critique and provide answers so we can tailor the
                final prompt perfectly for {form.targetModel}.
              </p>
            </header>

            <div className="grid gap-6 md:grid-cols-[2fr,3fr]">
              <div className="space-y-4 rounded-2xl border border-slate-800 bg-slate-950/40 p-6">
                <h3 className="text-lg font-semibold text-white">
                  Strengths & gaps
                </h3>
                <p className="text-slate-300">{analysis.analysis}</p>
                <div className="space-y-2">
                  <p className="text-sm font-medium text-slate-200">
                    Missing details to address
                  </p>
                  <ul className="list-disc space-y-2 pl-5 text-sm text-slate-300">
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

                {blueprint ? (
                  <div className="space-y-4 rounded-2xl border border-slate-800 bg-slate-950/60 p-5">
                    <h4 className="text-base font-semibold text-white">
                      Blueprint summary
                    </h4>
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="space-y-1">
                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                          Intent
                        </p>
                        <p className="text-sm text-slate-200">
                          {blueprint.intent}
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                          Audience
                        </p>
                        <p className="text-sm text-slate-200">
                          {blueprint.audience}
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                          Tone
                        </p>
                        <p className="text-sm text-slate-200">
                          {blueprint.tone}
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                          Output format
                        </p>
                        <p className="text-sm text-slate-200">
                          {blueprint.outputFormat}
                        </p>
                      </div>
                    </div>

                    <div className="grid gap-6 md:grid-cols-2">
                      <div className="space-y-2">
                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                          Success criteria
                        </p>
                        <ul className="list-disc space-y-2 pl-5 text-sm text-slate-300">
                          {blueprint.successCriteria.map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                      </div>
                      <div className="space-y-2">
                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                          Required inputs
                        </p>
                        <ul className="list-disc space-y-2 pl-5 text-sm text-slate-300">
                          {blueprint.requiredInputs.map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                        Domain context
                      </p>
                      <ul className="list-disc space-y-2 pl-5 text-sm text-slate-300">
                        {blueprint.domainContext.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="grid gap-6 md:grid-cols-2">
                      <div className="space-y-2">
                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                          Constraints & guardrails
                        </p>
                        <ul className="list-disc space-y-2 pl-5 text-sm text-slate-300">
                          {blueprint.constraints.map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                      </div>
                      <div className="space-y-2">
                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                          Risks to watch
                        </p>
                        <ul className="list-disc space-y-2 pl-5 text-sm text-slate-300">
                          {blueprint.risks.map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                        Evaluation checklist
                      </p>
                      <ul className="list-disc space-y-2 pl-5 text-sm text-slate-300">
                        {blueprint.evaluationChecklist.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ) : null}

                {analysis.externalContext?.length ? (
                  <div className="space-y-2 rounded-2xl border border-sky-500/20 bg-sky-500/5 p-5">
                    <p className="text-sm font-semibold text-sky-100">
                      Supporting sources
                    </p>
                    <ul className="space-y-3 text-xs text-sky-50/90">
                      {analysis.externalContext.map((item) => (
                        <li key={item.url} className="space-y-1">
                          <a
                            href={item.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-medium text-sky-200 underline underline-offset-2 hover:text-sky-100"
                          >
                            {item.title}
                          </a>
                          <p className="leading-relaxed text-slate-200">
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
                className="space-y-6 rounded-2xl border border-slate-800 bg-slate-950/30 p-6"
              >
                <h3 className="text-lg font-semibold text-white">
                  Clarifying questions
                </h3>
                <div className="space-y-6">
                  {analysis.questions.map((question) => (
                    <div key={question.id} className="space-y-2">
                      <label
                        htmlFor={`answer-${question.id}`}
                        className="text-sm font-medium text-slate-200"
                      >
                        {question.question}
                      </label>
                      {question.purpose ? (
                        <p className="text-xs text-slate-400">
                          Why it matters: {question.purpose}
                        </p>
                      ) : null}
                      <textarea
                        id={`answer-${question.id}`}
                        name={question.id}
                        rows={3}
                        required
                        className="w-full rounded-2xl border border-slate-800 bg-slate-950/70 p-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/30"
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
                  className="inline-flex w-full items-center justify-center rounded-2xl bg-emerald-500 px-6 py-3 text-base font-semibold text-emerald-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
                >
                  {isRefining
                    ? "Generating refined prompt..."
                    : unansweredQuestions
                      ? "Answer all questions to continue"
                      : "Generate refined prompt"}
                </button>
              </form>
            </div>
          </section>
        ) : null}

        {refinement ? (
          <section className="space-y-6 rounded-3xl border border-slate-800 bg-slate-900/50 p-8">
            <header className="space-y-2">
              <p className="text-xs uppercase tracking-[0.3em] text-emerald-300">
                phase 03
              </p>
              <h2 className="text-2xl font-semibold text-white md:text-3xl">
                Your AI-ready prompt
              </h2>
              <p className="text-slate-300">
                Copy it straight into {form.targetModel} or tweak it if you need
                a slightly different angle.
              </p>
            </header>

            <div className="flex flex-col gap-4 rounded-2xl border border-slate-800 bg-slate-950/40 p-6">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h3 className="text-lg font-semibold text-white">
                  Refined prompt
                </h3>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={handleRewrite}
                    disabled={isRefining || unansweredQuestions}
                    className="inline-flex items-center justify-center rounded-xl border border-emerald-500/40 bg-emerald-500/10 px-4 py-2 text-sm font-medium text-emerald-100 transition hover:border-emerald-400 hover:bg-emerald-400/20 disabled:cursor-not-allowed disabled:border-slate-600 disabled:bg-slate-800 disabled:text-slate-500"
                  >
                    {isRefining ? "Rewriting..." : "Re-write with new angle"}
                  </button>
                  <button
                    type="button"
                    onClick={handleCopy}
                    className="inline-flex items-center justify-center rounded-xl border border-slate-700 px-4 py-2 text-sm font-medium text-slate-200 transition hover:border-slate-500 hover:text-white"
                  >
                    {copied ? "Copied!" : "Copy to clipboard"}
                  </button>
                </div>
              </div>
              <pre className="whitespace-pre-wrap rounded-2xl bg-slate-950/70 p-4 text-slate-100">
                {refinement.refinedPrompt}
              </pre>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
              <div className="space-y-2 rounded-2xl border border-cyan-500/30 bg-cyan-500/10 p-6">
                <h3 className="text-lg font-semibold text-cyan-100">
                  Usage guidance
                </h3>
                <p className="text-sm text-cyan-50/90">{refinement.guidance}</p>
              </div>
              <div className="space-y-2 rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-6">
                <h3 className="text-lg font-semibold text-emerald-100">
                  Change summary
                </h3>
                <ul className="list-disc space-y-1 pl-5 text-sm text-emerald-50/90">
                  {refinement.changeSummary.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>

            {refinement.assumptions.length ? (
              <div className="space-y-2">
                <h3 className="text-sm font-semibold text-slate-200">
                  Assumptions we made
                </h3>
                <ul className="list-disc space-y-2 rounded-2xl border border-slate-800 bg-slate-950/40 p-5 pl-8 text-sm text-slate-300">
                  {refinement.assumptions.map((assumption) => (
                    <li key={assumption}>{assumption}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            {refinement.evaluationCriteria.length ? (
              <div className="space-y-2">
                <h3 className="text-sm font-semibold text-slate-200">
                  Evaluate the AI&apos;s response with these checkpoints
                </h3>
                <ul className="list-disc space-y-2 rounded-2xl border border-slate-800 bg-slate-950/40 p-5 pl-8 text-sm text-slate-300">
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
