"use client";

import { useState } from "react";

interface ErrorFeedbackProps {
    /** The error message to display */
    errorMessage: string;
    /** Callback to retry the failed action */
    onRetry?: () => void;
    /** Callback to dismiss the error */
    onDismiss?: () => void;
    /** Context about what the user was doing (form state snapshot) */
    context?: {
        modality?: string;
        targetModel?: string;
        thinkingMode?: boolean;
        action?: "analyze" | "refine" | "modify";
    };
}

export default function ErrorFeedback({
    errorMessage,
    onRetry,
    onDismiss,
    context,
}: ErrorFeedbackProps) {
    const [showFeedbackForm, setShowFeedbackForm] = useState(false);
    const [feedbackText, setFeedbackText] = useState("");
    const [feedbackEmail, setFeedbackEmail] = useState("");
    const [submitState, setSubmitState] = useState<
        "idle" | "sending" | "sent" | "error"
    >("idle");

    const buildGitHubIssueUrl = () => {
        const title = encodeURIComponent(
            `[Bug] ${errorMessage.slice(0, 80)}`
        );
        const body = encodeURIComponent(
            `## Bug Report\n\n**Error:** ${errorMessage}\n\n**Context:**\n- Modality: ${context?.modality ?? "unknown"}\n- Model: ${context?.targetModel ?? "unknown"}\n- Thinking Mode: ${context?.thinkingMode ?? false}\n- Action: ${context?.action ?? "unknown"}\n- Browser: ${typeof navigator !== "undefined" ? navigator.userAgent : "unknown"}\n- Timestamp: ${new Date().toISOString()}\n\n## Steps to Reproduce\n1. \n2. \n\n## Expected Behavior\n\n\n## Additional Notes\n`
        );
        return `https://github.com/Ker102/PromptTriage/issues/new?title=${title}&body=${body}&labels=bug`;
    };

    const handleSubmitFeedback = async () => {
        if (!feedbackText.trim()) return;

        setSubmitState("sending");
        try {
            const response = await fetch("/api/feedback", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    errorMessage,
                    feedback: feedbackText.trim(),
                    email: feedbackEmail.trim() || undefined,
                    context: {
                        ...context,
                        browser:
                            typeof navigator !== "undefined" ? navigator.userAgent : "unknown",
                        timestamp: new Date().toISOString(),
                        url: typeof window !== "undefined" ? window.location.href : "unknown",
                    },
                }),
            });

            if (response.ok) {
                setSubmitState("sent");
                setTimeout(() => {
                    setShowFeedbackForm(false);
                    setSubmitState("idle");
                    setFeedbackText("");
                }, 2500);
            } else {
                setSubmitState("error");
            }
        } catch {
            setSubmitState("error");
        }
    };

    return (
        <div className="rounded-2xl border border-red-500/30 bg-gradient-to-br from-red-500/10 via-red-900/5 to-transparent p-5 backdrop-blur-sm">
            {/* Error Message */}
            <div className="flex items-start gap-3">
                <span className="mt-0.5 text-lg">⚠️</span>
                <div className="flex-1 space-y-1">
                    <p className="text-sm font-semibold text-red-300">
                        Something went wrong
                    </p>
                    <p className="text-sm leading-relaxed text-red-200/80">
                        {errorMessage}
                    </p>
                </div>
                {onDismiss && (
                    <button
                        onClick={onDismiss}
                        className="text-red-400/60 transition-colors hover:text-red-300"
                        aria-label="Dismiss error"
                    >
                        ✕
                    </button>
                )}
            </div>

            {/* Action Buttons */}
            <div className="mt-4 flex flex-wrap items-center gap-2">
                {onRetry && (
                    <button
                        onClick={onRetry}
                        className="inline-flex items-center gap-1.5 rounded-xl bg-cyan-500/20 px-4 py-2 text-sm font-medium text-cyan-300 transition-all hover:bg-cyan-500/30 hover:text-cyan-200"
                    >
                        🔄 Try Again
                    </button>
                )}
                <button
                    onClick={() => setShowFeedbackForm((v) => !v)}
                    className="inline-flex items-center gap-1.5 rounded-xl bg-amber-500/15 px-4 py-2 text-sm font-medium text-amber-300 transition-all hover:bg-amber-500/25 hover:text-amber-200"
                >
                    💬 {showFeedbackForm ? "Hide Feedback" : "Submit Feedback"}
                </button>
                <a
                    href={buildGitHubIssueUrl()}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 rounded-xl border border-slate-600/40 px-4 py-2 text-sm font-medium text-slate-400 transition-all hover:border-slate-500/60 hover:text-slate-300"
                >
                    🐛 Report on GitHub
                </a>
            </div>

            {/* Feedback Form (collapsible) */}
            {showFeedbackForm && (
                <div className="mt-4 space-y-3 rounded-xl border border-amber-500/20 bg-amber-500/5 p-4">
                    <textarea
                        value={feedbackText}
                        onChange={(e) => setFeedbackText(e.target.value)}
                        placeholder="What happened? Any extra details help us fix this faster..."
                        className="w-full resize-none rounded-lg border border-slate-600/40 bg-slate-800/50 p-3 text-sm text-slate-200 placeholder:text-slate-500 focus:border-amber-500/50 focus:outline-none focus:ring-1 focus:ring-amber-500/30"
                        rows={3}
                    />
                    <div className="flex items-center gap-3">
                        <input
                            type="email"
                            value={feedbackEmail}
                            onChange={(e) => setFeedbackEmail(e.target.value)}
                            placeholder="Email (optional, for follow-up)"
                            className="flex-1 rounded-lg border border-slate-600/40 bg-slate-800/50 px-3 py-2 text-sm text-slate-200 placeholder:text-slate-500 focus:border-amber-500/50 focus:outline-none focus:ring-1 focus:ring-amber-500/30"
                        />
                        <button
                            onClick={handleSubmitFeedback}
                            disabled={
                                !feedbackText.trim() || submitState === "sending" || submitState === "sent"
                            }
                            className="inline-flex items-center gap-1.5 rounded-lg bg-amber-500/80 px-4 py-2 text-sm font-semibold text-slate-900 transition-all hover:bg-amber-400 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            {submitState === "idle" && "Send"}
                            {submitState === "sending" && "Sending..."}
                            {submitState === "sent" && "✅ Sent!"}
                            {submitState === "error" && "❌ Retry"}
                        </button>
                    </div>
                    {submitState === "sent" && (
                        <p className="text-xs text-slate-400">
                            Thanks! Your feedback has been submitted.
                        </p>
                    )}
                    {submitState === "error" && (
                        <p className="text-xs text-red-400">
                            Failed to send — you can also{" "}
                            <a
                                href={buildGitHubIssueUrl()}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="underline"
                            >
                                report on GitHub
                            </a>
                            .
                        </p>
                    )}
                </div>
            )}
        </div>
    );
}
