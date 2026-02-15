"use client";

import { useEffect, useState } from "react";
import {
    Lock,
    FileInput,
    Brain,
    Search,
    BookOpen,
    Puzzle,
    Sparkles,
    CheckCircle2,
    ClipboardList,
} from "lucide-react";
import type { ReactNode } from "react";

interface PipelineStep {
    label: string;
    icon: ReactNode;
    durationMs: number;
}

const ANALYZE_STEPS: PipelineStep[] = [
    { label: "Authenticating", icon: <Lock className="h-3.5 w-3.5" />, durationMs: 800 },
    { label: "Parsing input", icon: <FileInput className="h-3.5 w-3.5" />, durationMs: 600 },
    { label: "Selecting model", icon: <Brain className="h-3.5 w-3.5" />, durationMs: 400 },
    { label: "Searching knowledge base", icon: <Search className="h-3.5 w-3.5" />, durationMs: 2000 },
    { label: "Fetching live docs", icon: <BookOpen className="h-3.5 w-3.5" />, durationMs: 1500 },
    { label: "Building prompt context", icon: <Puzzle className="h-3.5 w-3.5" />, durationMs: 800 },
    { label: "Generating analysis", icon: <Sparkles className="h-3.5 w-3.5" />, durationMs: 8000 },
    { label: "Validating response", icon: <CheckCircle2 className="h-3.5 w-3.5" />, durationMs: 500 },
];

const REFINE_STEPS: PipelineStep[] = [
    { label: "Authenticating", icon: <Lock className="h-3.5 w-3.5" />, durationMs: 600 },
    { label: "Validating blueprint", icon: <ClipboardList className="h-3.5 w-3.5" />, durationMs: 500 },
    { label: "Assembling context", icon: <Puzzle className="h-3.5 w-3.5" />, durationMs: 1000 },
    { label: "Refining prompt", icon: <Sparkles className="h-3.5 w-3.5" />, durationMs: 10000 },
    { label: "Validating output", icon: <CheckCircle2 className="h-3.5 w-3.5" />, durationMs: 500 },
];

interface PipelineProgressProps {
    mode: "analyze" | "refine";
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
        <div className="space-y-3 rounded-2xl border border-[rgba(148,163,184,0.15)] bg-[var(--surface-card-soft)] p-5 backdrop-blur-sm">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <span className="relative flex h-2.5 w-2.5">
                        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-white/60 opacity-75" />
                        <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-white/80" />
                    </span>
                    <span className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
                        {mode === "analyze" ? "Analyzing" : "Refining"}
                    </span>
                </div>
                {thinkingMode && (
                    <span className="inline-flex items-center gap-1.5 rounded-full border border-[rgba(148,163,184,0.2)] px-2 py-0.5 text-xs font-medium text-slate-400">
                        <Brain className="h-3 w-3" />
                        Deep Thinking
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
                                ? "bg-white/5 text-[var(--foreground)]"
                                : isComplete
                                    ? "text-slate-500"
                                    : "text-slate-600/50"
                                }`}
                        >
                            {/* Icon / checkmark */}
                            <span
                                className={`flex w-5 items-center justify-center transition-all duration-300 ${isComplete ? "scale-90 opacity-60" : isActive ? "animate-pulse" : "opacity-30"
                                    }`}
                            >
                                {isComplete ? <CheckCircle2 className="h-3.5 w-3.5 text-slate-500" /> : step.icon}
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
                                            className="h-1 w-1 rounded-full bg-white/60 animate-dotPulse shadow-[0_0_6px_rgba(255,255,255,0.3)]"
                                            style={{ animationDelay: `${i * 0.18}s` }}
                                        />
                                    ))}
                                </span>
                            )}

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
