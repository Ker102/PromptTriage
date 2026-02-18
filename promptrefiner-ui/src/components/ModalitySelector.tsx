"use client";

import type { ReactNode } from "react";
import { MessageSquare, Image as ImageIcon, Film, Settings } from "lucide-react";

// Modality types
export type Modality = "text" | "image" | "video" | "system";

// Models organized by modality — use generic family names, not specific versions
export const MODALITY_CONFIG: Record<Modality, { label: string; icon: ReactNode; description: string; models: readonly string[] }> = {
    text: {
        label: "Text Generation",
        icon: <MessageSquare className="h-5 w-5" />,
        description: "Chat, completions, reasoning",
        models: [
            "None / Not sure yet",
            "OpenAI (GPT)",
            "OpenAI (o-series reasoning)",
            "Anthropic (Claude)",
            "Google (Gemini)",
            "xAI (Grok)",
            "Mistral",
            "DeepSeek",
            "Meta (Llama)",
            "Qwen (Alibaba)",
            "Cohere (Command)",
        ],
    },
    image: {
        label: "Image Generation",
        icon: <ImageIcon className="h-5 w-5" />,
        description: "Text-to-image, img2img, editing",
        models: [
            "None / Not sure yet",
            "OpenAI (DALL-E / GPT Image)",
            "Midjourney",
            "Stable Diffusion (Stability AI)",
            "FLUX (Black Forest Labs)",
            "Ideogram",
            "Google (Imagen)",
            "Leonardo AI",
            "Adobe Firefly",
        ],
    },
    video: {
        label: "Video Generation",
        icon: <Film className="h-5 w-5" />,
        description: "Text-to-video, img2video",
        models: [
            "None / Not sure yet",
            "Runway (Gen series)",
            "Pika",
            "Kling AI (Kuaishou)",
            "Luma (Dream Machine)",
            "OpenAI (Sora)",
            "Google (Veo)",
            "Minimax (Video)",
            "Wan (Alibaba)",
        ],
    },
    system: {
        label: "System Prompt",
        icon: <Settings className="h-5 w-5" />,
        description: "Create AI agent prompts",
        models: [
            "Any AI Model",
            "Claude (Anthropic)",
            "ChatGPT / GPT (OpenAI)",
            "Gemini (Google)",
            "Cursor IDE",
            "Coding Agent",
            "Research Agent",
            "Writing Assistant",
        ],
    },
};

export type ModalityModel = string;

interface ModalitySelectorProps {
    modality: Modality;
    model: string;
    onModalityChange: (modality: Modality) => void;
    onModelChange: (model: string) => void;
    disabled?: boolean;
}

export function ModalitySelector({
    modality,
    model,
    onModalityChange,
    onModelChange,
    disabled = false,
}: ModalitySelectorProps) {
    const config = MODALITY_CONFIG[modality];

    return (
        <div className="space-y-4">
            {/* Modality Tabs */}
            <div className="grid grid-cols-2 gap-2 md:flex">
                {(Object.keys(MODALITY_CONFIG) as Modality[]).map((mod) => {
                    const cfg = MODALITY_CONFIG[mod];
                    const isActive = modality === mod;

                    return (
                        <button
                            key={mod}
                            type="button"
                            disabled={disabled}
                            onClick={() => {
                                onModalityChange(mod);
                                onModelChange(MODALITY_CONFIG[mod].models[0]);
                            }}
                            className={`md:flex-1 rounded-xl px-3 py-2 md:px-4 md:py-3 text-center transition-all duration-300 ${isActive
                                ? "bg-white/10 border-2 border-white/30 text-[var(--foreground)] shadow-[0_0_15px_rgba(255,255,255,0.06)]"
                                : "border border-[var(--surface-border)] bg-[var(--surface-card)] text-muted hover:border-[rgba(148,163,184,0.5)] hover:text-soft"
                                } disabled:cursor-not-allowed disabled:opacity-50`}
                        >
                            <span className="flex items-center justify-center">{cfg.icon}</span>
                            <span className="mt-1 block text-sm font-medium">{cfg.label}</span>
                            <span className="hidden md:block text-xs text-muted">{cfg.description}</span>
                        </button>
                    );
                })}
            </div>

            {/* Model Dropdown */}
            <div className="space-y-2">
                <label
                    htmlFor="targetModel"
                    className="text-sm font-medium text-soft"
                >
                    Target {config.label.split(" ")[0]} model
                </label>
                <select
                    id="targetModel"
                    name="targetModel"
                    disabled={disabled}
                    className="w-full rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-card-strong)] px-4 py-2.5 text-base text-[var(--foreground)] placeholder:text-muted transition-all duration-300 ease-out focus:-translate-y-0.5 focus:scale-[1.01] focus:border-white/40 focus:outline-none focus:ring-2 focus:ring-white/20 disabled:cursor-not-allowed disabled:opacity-50"
                    value={model}
                    onChange={(e) => onModelChange(e.target.value)}
                >
                    {config.models.map((m) => (
                        <option key={m} value={m}>
                            {m}
                        </option>
                    ))}
                </select>
                <p className="text-sm text-muted">
                    {modality === "text" &&
                        "Tailor the prompt format and structure to the model you plan to use."}
                    {modality === "image" &&
                        "Different image models have varying prompt styles (descriptive, tags, negative prompts)."}
                    {modality === "video" &&
                        "Video models need motion cues, camera angles, and duration hints."}
                    {modality === "system" &&
                        "Create comprehensive system prompts for AI agents, assistants, and tools."}
                </p>
            </div>
        </div>
    );
}
