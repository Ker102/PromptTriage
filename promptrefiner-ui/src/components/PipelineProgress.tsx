"use client";

import { useEffect, useState } from "react";

interface PipelineStep {
    label: string;
    icon: string;
    durationMs: number;
}

const ANALYZE_STEPS: PipelineStep[] = [
    { label: "Authenticating", icon: "🔑", durationMs: 800 },
    { label: "Parsing input", icon: "📝", durationMs: 600 },
    { label: "Selecting model", icon: "🧠", durationMs: 400 },
    { label: "Searching knowledge base", icon: "🔍", durationMs: 2000 },
    { label: "Fetching live docs", icon: "📚", durationMs: 1500 },
    { label: "Building prompt context", icon: "🧩", durationMs: 800 },
    { label: "Generating analysis", icon: "✨", durationMs: 8000 },
    { label: "Validating response", icon: "✅", durationMs: 500 },
];

const REFINE_STEPS: PipelineStep[] = [
    { label: "Authenticating", icon: "🔑", durationMs: 600 },
    { label: "Validating blueprint", icon: "📋", durationMs: 500 },
    { label: "Assembling context", icon: "🧩", durationMs: 1000 },
    { label: "Refining prompt", icon: "✨", durationMs: 10000 },
    { label: "Validating output", icon: "✅", durationMs: 500 },
];

interface PipelineProgressProps {
    /** Which pipeline is running */
    mode: "analyze" | "refine";
    /** Whether thinking mode is enabled (shows a badge) */
    thinkingMode?: boolean;
}

export default function PipelineProgress({
    mode,
    thinkingMode = false,
}: PipelineProgressProps) {
    const steps = mode === "analyze" ? ANALYZE_STEPS : REFINE_STEPS;
    const [activeStep, setActiveStep] = useState(0);

    useEffect(() => {
        let timeoutId: NodeJS.Timeout;

        const advanceStep = (currentStep: number) => {
            if (currentStep >= steps.length - 1) {
                // Stay on last step — it loops with a pulse animation
                return;
            }

            timeoutId = setTimeout(() => {
                setActiveStep(currentStep + 1);
                advanceStep(currentStep + 1);
            }, steps[currentStep].durationMs);
        };

        advanceStep(0);
        return () => clearTimeout(timeoutId);
    }, [steps]);

    return (
        <div className="space-y-3 rounded-2xl border border-cyan-500/20 bg-gradient-to-br from-cyan-500/5 via-transparent to-transparent p-5 backdrop-blur-sm">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <span className="relative flex h-2.5 w-2.5">
                        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-cyan-400 opacity-75" />
                        <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-cyan-500" />
                    </span>
                    <span className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">
                        {mode === "analyze" ? "Analyzing" : "Refining"}
                    </span>
                </div>
                {thinkingMode && (
                    <span className="rounded-full bg-purple-500/20 px-2 py-0.5 text-xs font-medium text-purple-300">
                        🧠 Deep Thinking
                    </span>
                )}
            </div>

            {/* Steps */}
            <div className="space-y-1.5">
                {steps.map((step, index) => {
                    const isActive = index === activeStep;
                    const isComplete = index < activeStep;
                    const isPending = index > activeStep;

                    return (
                        <div
                            key={step.label}
                            className={`flex items-center gap-2.5 rounded-lg px-3 py-1.5 text-sm transition-all duration-500 ${isActive
                                    ? "bg-cyan-500/10 text-cyan-200"
                                    : isComplete
                                        ? "text-slate-500"
                                        : "text-slate-600/50"
                                }`}
                        >
                            {/* Icon / checkmark */}
                            <span
                                className={`w-5 text-center transition-all duration-300 ${isComplete ? "scale-90 opacity-60" : isActive ? "animate-pulse" : "opacity-30"
                                    }`}
                            >
                                {isComplete ? "✓" : step.icon}
                            </span>

                            {/* Label */}
                            <span
                                className={`flex-1 transition-all duration-300 ${isActive ? "font-medium" : isComplete ? "line-through decoration-slate-600/50" : ""
                                    }`}
                            >
                                {step.label}
                            </span>

                            {/* Active indicator */}
                            {isActive && (
                                <span className="inline-flex items-center gap-[3px]">
                                    {Array.from({ length: 3 }).map((_, i) => (
                                        <span
                                            key={i}
                                            className="h-1 w-1 rounded-full bg-cyan-400 animate-dotPulse shadow-[0_0_6px_rgba(34,211,238,0.5)]"
                                            style={{ animationDelay: `${i * 0.18}s` }}
                                        />
                                    ))}
                                </span>
                            )}

                            {/* Pending dimness handled by class already */}
                            {isPending && null}
                        </div>
                    );
                })}
            </div>

            {/* Elapsed time */}
            <ElapsedTime />
        </div>
    );
}

function ElapsedTime() {
    const [elapsed, setElapsed] = useState(0);

    useEffect(() => {
        const interval = setInterval(() => {
            setElapsed((prev) => prev + 1);
        }, 1000);
        return () => clearInterval(interval);
    }, []);

    return (
        <p className="text-right text-xs text-slate-500/70">
            {elapsed}s elapsed
        </p>
    );
}
