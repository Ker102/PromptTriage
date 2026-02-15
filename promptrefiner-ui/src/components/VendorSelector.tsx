"use client";

export type VendorId = "none" | "anthropic" | "openai" | "google";

export const VENDOR_OPTIONS: {
    id: VendorId;
    label: string;
    hint: string;
    icon: string;
}[] = [
        {
            id: "none",
            label: "Any (Default)",
            hint: "No vendor preference",
            icon: "🌐",
        },
        {
            id: "anthropic",
            label: "Claude (Anthropic)",
            hint: "XML sections, detailed identity blocks, thinking patterns",
            icon: "🟣",
        },
        {
            id: "openai",
            label: "GPT / O-Series (OpenAI)",
            hint: "Markdown structure, tool schemas, concise headers",
            icon: "🟢",
        },
        {
            id: "google",
            label: "Gemini (Google)",
            hint: "Hybrid XML/Markdown, grounded responses, multimodal",
            icon: "🔵",
        },
    ];

interface VendorSelectorProps {
    selected: VendorId;
    onChange: (vendor: VendorId) => void;
    disabled?: boolean;
}

export function VendorSelector({
    selected,
    onChange,
    disabled = false,
}: VendorSelectorProps) {
    return (
        <div className="space-y-2">
            <div className="flex gap-2 flex-wrap">
                {VENDOR_OPTIONS.map((vendor) => {
                    const isActive = selected === vendor.id;
                    return (
                        <button
                            key={vendor.id}
                            type="button"
                            disabled={disabled}
                            onClick={() => onChange(vendor.id)}
                            className={`flex items-center gap-2 rounded-xl px-3 py-2 text-sm transition-all duration-300 ${isActive
                                    ? "bg-white/10 border-2 border-white/30 text-[var(--foreground)] shadow-[0_0_15px_rgba(255,255,255,0.06)]"
                                    : "border border-[var(--surface-border)] bg-[var(--surface-card)] text-muted hover:border-[rgba(148,163,184,0.5)] hover:text-soft"
                                } disabled:cursor-not-allowed disabled:opacity-50`}
                        >
                            <span className="text-base">{vendor.icon}</span>
                            <span className="font-medium">{vendor.label}</span>
                        </button>
                    );
                })}
            </div>
            {selected !== "none" && (
                <p className="text-xs text-muted">
                    {VENDOR_OPTIONS.find((v) => v.id === selected)?.hint}
                </p>
            )}
        </div>
    );
}
