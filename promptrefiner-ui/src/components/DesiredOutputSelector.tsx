"use client";

// Options for what format the TARGET model should produce
export const DESIRED_OUTPUT_OPTIONS = [
    { id: "markdown", label: "Markdown", description: "Formatted text with headers, lists, emphasis" },
    { id: "code", label: "Code", description: "Executable code with syntax highlighting" },
    { id: "json", label: "JSON", description: "Structured JSON data" },
    { id: "xml", label: "XML", description: "Structured XML data" },
    { id: "plain-text", label: "Plain Text", description: "Unformatted text" },
    { id: "technical-doc", label: "Technical Doc", description: "Documentation with examples" },
    { id: "step-by-step", label: "Step-by-Step Guide", description: "Numbered instructions" },
] as const;

export type DesiredOutputId = typeof DESIRED_OUTPUT_OPTIONS[number]["id"];

interface DesiredOutputSelectorProps {
    selected: DesiredOutputId | null;
    onChange: (selected: DesiredOutputId | null) => void;
    disabled?: boolean;
}

export function DesiredOutputSelector({
    selected,
    onChange,
    disabled = false,
}: DesiredOutputSelectorProps) {
    return (
        <div className="space-y-2">
            <select
                id="desiredOutput"
                name="desiredOutput"
                disabled={disabled}
                className="w-full rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-card-strong)] px-4 py-2.5 text-base text-[var(--foreground)] transition-all duration-300 ease-out focus:-translate-y-0.5 focus:scale-[1.01] focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 disabled:cursor-not-allowed disabled:opacity-50"
                value={selected ?? ""}
                onChange={(e) => onChange(e.target.value === "" ? null : (e.target.value as DesiredOutputId))}
            >
                <option value="">Not specified</option>
                {DESIRED_OUTPUT_OPTIONS.map((option) => (
                    <option key={option.id} value={option.id}>
                        {option.label} - {option.description}
                    </option>
                ))}
            </select>
            <p className="text-xs text-muted">
                Specifies what format the target AI model should produce when given the refined prompt.
            </p>
        </div>
    );
}
