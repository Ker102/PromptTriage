'use client';

import { FormEvent, useMemo, useState } from "react";
import type {
  PromptAnalysisResult,
  PromptRefinementResult,
} from "@/types/prompt";

type RefinementStage = "collect" | "analyzed" | "refined";
type PendingAction = "analyze" | "refine" | null;

const MODEL_PRESETS = [
  "openai/gpt-4o-mini",
  "openai/gpt-4.1",
  "anthropic/claude-3.5-sonnet",
  "google/gemini-1.5-pro",
  "mistral/large-latest",
] as const;

const INITIAL_FORM = {
  prompt: "",
  targetModel: MODEL_PRESETS[0],
  context: "",
  tone: "",
  outputRequirements: "",
};

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

  const isAnalyzing = pendingAction === "analyze";
  const isRefining = pendingAction === "refine";

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
        }),
      });

      if (!response.ok) {
        const { error: message } = await response.json();
        throw new Error(message ?? "Analysis request failed.");
      }

      const payload = (await response.json()) as PromptAnalysisResult;

      setAnalysis(payload);
      setAnswers(
        payload.questions.reduce<Record<string, string>>((acc, question) => {
          acc[question.id] = "";
          return acc;
        }, {}),
      );
      setStage("analyzed");
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Unable to analyze prompt.";
      setError(message);
      setStage("collect");
    } finally {
      setPendingAction(null);
    }
  };

  const handleRefine = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!analysis) {
      return;
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
        }),
      });

      if (!response.ok) {
        const { error: message } = await response.json();
        throw new Error(message ?? "Refinement request failed.");
      }

      const payload = (await response.json()) as PromptRefinementResult;

      setRefinement(payload);
      setStage("refined");
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Unable to refine prompt.";
      setError(message);
    } finally {
      setPendingAction(null);
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
                use.
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
                <button
                  type="button"
                  onClick={handleCopy}
                  className="inline-flex items-center justify-center rounded-xl border border-slate-700 px-4 py-2 text-sm font-medium text-slate-200 transition hover:border-slate-500 hover:text-white"
                >
                  {copied ? "Copied!" : "Copy to clipboard"}
                </button>
              </div>
              <pre className="whitespace-pre-wrap rounded-2xl bg-slate-950/70 p-4 text-slate-100">
                {refinement.refinedPrompt}
              </pre>
            </div>

            {refinement.guidance ? (
              <div className="space-y-2 rounded-2xl border border-cyan-500/30 bg-cyan-500/10 p-6">
                <h3 className="text-lg font-semibold text-cyan-100">
                  Usage guidance
                </h3>
                <p className="text-sm text-cyan-50/90">{refinement.guidance}</p>
              </div>
            ) : null}

            {refinement.assumptions?.length ? (
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

            {refinement.evaluationCriteria?.length ? (
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
