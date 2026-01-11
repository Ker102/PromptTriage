"use client";

import { useState, useRef, useEffect } from "react";

export const OUTPUT_FORMAT_OPTIONS = [
    { id: "json", label: "JSON", description: "Structured JSON output" },
    { id: "markdown", label: "Markdown", description: "Headers, lists, formatting" },
    { id: "plain-text", label: "Plain Text", description: "Simple unformatted" },
    { id: "code-block", label: "Code Block", description: "Wrapped in code fences" },
    { id: "step-by-step", label: "Step-by-Step", description: "Numbered instructions" },
    { id: "bullet-points", label: "Bullet Points", description: "List format" },
    { id: "table", label: "Table", description: "Tabular data" },
    { id: "xml", label: "XML", description: "XML structured output" },
] as const;

export type OutputFormatId = (typeof OUTPUT_FORMAT_OPTIONS)[number]["id"];

interface OutputFormatSelectorProps {
    selected: OutputFormatId[];
    onChange: (selected: OutputFormatId[]) => void;
    disabled?: boolean;
}

export function OutputFormatSelector({
    selected,
    onChange,
    disabled = false,
}: OutputFormatSelectorProps) {
    const [isOpen, setIsOpen] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };

        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const toggleOption = (id: OutputFormatId) => {
        if (selected.includes(id)) {
            onChange(selected.filter((s) => s !== id));
        } else {
            onChange([...selected, id]);
        }
    };

    const removeOption = (id: OutputFormatId, e: React.MouseEvent) => {
        e.stopPropagation();
        onChange(selected.filter((s) => s !== id));
    };

    const selectedLabels = OUTPUT_FORMAT_OPTIONS.filter((opt) =>
        selected.includes(opt.id)
    );

    return (
        <div ref={containerRef} className="relative">
            {/* Trigger */}
            <button
                type="button"
                disabled={disabled}
                onClick={() => setIsOpen(!isOpen)}
                className="w-full rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-card-strong)] px-4 py-2.5 text-left text-base text-[var(--foreground)] transition-all duration-300 ease-out focus:-translate-y-0.5 focus:scale-[1.01] focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 disabled:cursor-not-allowed disabled:opacity-50"
            >
                {selectedLabels.length === 0 ? (
                    <span className="text-muted">Select output formats...</span>
                ) : (
                    <div className="flex flex-wrap gap-1.5">
                        {selectedLabels.map((opt) => (
                            <span
                                key={opt.id}
                                className="inline-flex items-center gap-1 rounded-full bg-cyan-500/20 px-2.5 py-0.5 text-xs font-medium text-cyan-300"
                            >
                                {opt.label}
                                <button
                                    type="button"
                                    onClick={(e) => removeOption(opt.id, e)}
                                    className="ml-0.5 rounded-full p-0.5 hover:bg-cyan-500/30 focus:outline-none"
                                    aria-label={`Remove ${opt.label}`}
                                >
                                    <svg
                                        className="h-3 w-3"
                                        viewBox="0 0 20 20"
                                        fill="currentColor"
                                    >
                                        <path
                                            fillRule="evenodd"
                                            d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                                            clipRule="evenodd"
                                        />
                                    </svg>
                                </button>
                            </span>
                        ))}
                    </div>
                )}
                {/* Dropdown arrow */}
                <span className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2">
                    <svg
                        className={`h-4 w-4 text-muted transition-transform duration-200 ${isOpen ? "rotate-180" : ""
                            }`}
                        viewBox="0 0 20 20"
                        fill="currentColor"
                    >
                        <path
                            fillRule="evenodd"
                            d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                            clipRule="evenodd"
                        />
                    </svg>
                </span>
            </button>

            {/* Dropdown */}
            {isOpen && !disabled && (
                <div className="absolute z-50 mt-2 w-full rounded-xl border border-[var(--surface-border)] bg-[var(--surface-card)] p-2 shadow-xl shadow-slate-950/40">
                    {OUTPUT_FORMAT_OPTIONS.map((option) => {
                        const isSelected = selected.includes(option.id);
                        return (
                            <button
                                key={option.id}
                                type="button"
                                onClick={() => toggleOption(option.id)}
                                className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left transition-colors duration-150 ${isSelected
                                        ? "bg-cyan-500/10 text-cyan-300"
                                        : "text-soft hover:bg-[var(--surface-card-soft)]"
                                    }`}
                            >
                                <span
                                    className={`flex h-4 w-4 items-center justify-center rounded border ${isSelected
                                            ? "border-cyan-400 bg-cyan-500"
                                            : "border-[var(--surface-border)] bg-transparent"
                                        }`}
                                >
                                    {isSelected && (
                                        <svg
                                            className="h-3 w-3 text-slate-900"
                                            viewBox="0 0 20 20"
                                            fill="currentColor"
                                        >
                                            <path
                                                fillRule="evenodd"
                                                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                                clipRule="evenodd"
                                            />
                                        </svg>
                                    )}
                                </span>
                                <div>
                                    <p className="text-sm font-medium">{option.label}</p>
                                    <p className="text-xs text-muted">{option.description}</p>
                                </div>
                            </button>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
