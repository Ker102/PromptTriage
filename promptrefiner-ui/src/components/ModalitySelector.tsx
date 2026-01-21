"use client";

import { useState } from "react";

// Modality types
export type Modality = "text" | "image" | "video" | "system";

// Models organized by modality
export const MODALITY_CONFIG = {
    text: {
        label: "Text Generation",
        icon: "💬",
        description: "Chat, completions, reasoning",
        models: [
            "None / Not sure yet",
            "OpenAI GPT-4o",
            "OpenAI GPT-4 Turbo",
            "OpenAI O1",
            "OpenAI O3",
            "Anthropic Claude 4 Sonnet",
            "Anthropic Claude 4 Opus",
            "Anthropic Claude Haiku",
            "Google Gemini 2.0 Pro",
            "Google Gemini 2.0 Flash",
            "xAI Grok",
            "Mistral Large",
            "DeepSeek V3",
            "Meta Llama 3.3",
        ],
    },
    image: {
        label: "Image Generation",
        icon: "🎨",
        description: "Text-to-image, img2img, editing",
        models: [
            "None / Not sure yet",
            "OpenAI DALL-E 3",
            "Midjourney v6.1",
            "Stable Diffusion XL",
            "Stable Diffusion 3.5",
            "FLUX.1 Pro",
            "FLUX.1 Dev",
            "Ideogram 2.0",
            "Google Imagen 3",
            "Leonardo AI",
            "Adobe Firefly",
        ],
    },
    video: {
        label: "Video Generation",
        icon: "🎬",
        description: "Text-to-video, img2video",
        models: [
            "None / Not sure yet",
            "Runway Gen-3 Alpha",
            "Pika 2.0",
            "Kling AI",
            "Luma Dream Machine",
            "OpenAI Sora",
            "Google Veo 2",
            "Minimax Video-01",
            "Haiper 2.0",
        ],
    },
    system: {
        label: "System Prompt",
        icon: "⚙️",
        description: "Create AI agent prompts",
        models: [
            "Any AI Model",
            "Claude (Anthropic)",
            "GPT-4 (OpenAI)",
            "Gemini (Google)",
            "Cursor IDE",
            "Coding Agent",
            "Research Agent",
            "Writing Assistant",
        ],
    },
} as const;

export type ModalityModel = typeof MODALITY_CONFIG[Modality]["models"][number];

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
            <div className="flex gap-2">
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
                                // Reset to first model when switching modality
                                onModelChange(MODALITY_CONFIG[mod].models[0]);
                            }}
                            className={`flex-1 rounded-xl px-4 py-3 text-center transition-all duration-300 ${isActive
                                ? "bg-gradient-to-r from-cyan-500/20 to-emerald-500/20 border-2 border-cyan-400/60 text-[var(--foreground)] shadow-[0_0_20px_rgba(34,211,238,0.15)]"
                                : "border border-[var(--surface-border)] bg-[var(--surface-card)] text-muted hover:border-[rgba(148,163,184,0.5)] hover:text-soft"
                                } disabled:cursor-not-allowed disabled:opacity-50`}
                        >
                            <span className="text-xl">{cfg.icon}</span>
                            <span className="mt-1 block text-sm font-medium">{cfg.label}</span>
                            <span className="block text-xs text-muted">{cfg.description}</span>
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
                    className="w-full rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-card-strong)] px-4 py-2.5 text-base text-[var(--foreground)] placeholder:text-muted transition-all duration-300 ease-out focus:-translate-y-0.5 focus:scale-[1.01] focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 disabled:cursor-not-allowed disabled:opacity-50"
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
