import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { getGeminiModel, extractJsonFromText } from "@/lib/gemini";
import {
    SYSTEM_PROMPT_GENERATOR_PROMPT,
    SYSTEM_PROMPT_GENERATOR_FEW_SHOTS,
} from "@/prompts/systemPromptGenerator";
import { PROMPT_VERSION } from "@/prompts/metaprompt";
import { authOptions } from "@/auth";
import { recordUsageOrThrow } from "@/services/usage-limit";

export interface GenerateSystemPromptRequest {
    targetModel: string;
    useCase: string;
    persona?: string;
    constraints?: string;
    tools?: string;
    additionalContext?: string;
}

export interface GeneratedSystemPromptResult {
    systemPrompt: string;
    promptStructure: string[];
    designRationale: string;
    customizationNotes: string[];
    evaluationCriteria: string[];
}

function validateRequestPayload(payload: GenerateSystemPromptRequest): string | null {
    if (!payload.targetModel?.trim()) {
        return "Target model is required.";
    }

    if (!payload.useCase?.trim()) {
        return "Use case description is required.";
    }

    if (payload.useCase.trim().length < 20) {
        return "Please provide a more detailed use case description (at least 20 characters).";
    }

    return null;
}

function validateResult(result: GeneratedSystemPromptResult): string | null {
    if (!result.systemPrompt?.trim()) {
        return "Generated system prompt is empty.";
    }

    if (!Array.isArray(result.promptStructure) || result.promptStructure.length === 0) {
        return "Prompt structure list is empty.";
    }

    if (!result.designRationale?.trim()) {
        return "Design rationale is missing.";
    }

    if (!Array.isArray(result.customizationNotes) || result.customizationNotes.length === 0) {
        return "Customization notes are missing.";
    }

    if (!Array.isArray(result.evaluationCriteria) || result.evaluationCriteria.length === 0) {
        return "Evaluation criteria are missing.";
    }

    return null;
}

export async function POST(req: Request) {
    try {
        const session = await getServerSession(authOptions);
        if (!session) {
            return NextResponse.json(
                { error: "You must be signed in to generate system prompts." },
                { status: 401 },
            );
        }

        const email = session.user?.email;
        if (!email) {
            return NextResponse.json(
                { error: "Unable to resolve your account email." },
                { status: 400 },
            );
        }

        const subscriptionPlan =
            (session.user?.subscriptionPlan as string | undefined)?.toUpperCase() ??
            "FREE";

        const body = (await req.json()) as GenerateSystemPromptRequest;

        const validationError = validateRequestPayload(body);
        if (validationError) {
            return NextResponse.json(
                { error: validationError },
                { status: 400 },
            );
        }

        const targetModel = body.targetModel.trim();
        const useCase = body.useCase.trim();
        const persona = body.persona?.trim() || "";
        const constraints = body.constraints?.trim() || "";
        const tools = body.tools?.trim() || "";
        const additionalContext = body.additionalContext?.trim() || "";

        const model = getGeminiModel();

        try {
            recordUsageOrThrow(email, subscriptionPlan);
        } catch (usageError) {
            const message =
                usageError instanceof Error
                    ? usageError.message
                    : "Usage limit exceeded.";
            return NextResponse.json({ error: message }, { status: 429 });
        }

        // Build the user prompt with structured inputs
        const userPromptParts = [
            `<target_model>${targetModel}</target_model>`,
            `<use_case>${useCase}</use_case>`,
        ];

        if (persona) {
            userPromptParts.push(`<persona>${persona}</persona>`);
        }

        if (constraints) {
            userPromptParts.push(`<constraints>${constraints}</constraints>`);
        }

        if (tools) {
            userPromptParts.push(`<tools>${tools}</tools>`);
        }

        if (additionalContext) {
            userPromptParts.push(`<additional_context>${additionalContext}</additional_context>`);
        }

        const userPrompt = userPromptParts.join("\n");

        // Build few-shot messages
        const fewShotMessages = SYSTEM_PROMPT_GENERATOR_FEW_SHOTS.flatMap(({ user, assistant }) => [
            { role: "user" as const, parts: [{ text: user }] },
            { role: "model" as const, parts: [{ text: assistant }] },
        ]);

        const result = await model.generateContent({
            systemInstruction: {
                role: "system",
                parts: [{ text: SYSTEM_PROMPT_GENERATOR_PROMPT }],
            },
            contents: [
                ...fewShotMessages,
                {
                    role: "user",
                    parts: [{ text: userPrompt }],
                },
            ],
            generationConfig: {
                temperature: 0.5,
                topP: 0.9,
                responseMimeType: "application/json",
            },
        });

        const rawText = result.response.text();
        const parsed = extractJsonFromText<GeneratedSystemPromptResult>(rawText);

        const resultValidationError = validateResult(parsed);
        if (resultValidationError) {
            return NextResponse.json(
                { error: `Invalid generation result: ${resultValidationError}` },
                { status: 502 },
            );
        }

        // Add metadata to the response
        const enriched = {
            ...parsed,
            version: PROMPT_VERSION,
            targetModel,
            useCase,
        };

        return NextResponse.json(enriched);
    } catch (error) {
        if (error instanceof SyntaxError) {
            return NextResponse.json(
                {
                    error:
                        "Failed to interpret the model output. Please try again or adjust your description.",
                },
                { status: 502 },
            );
        }

        const message =
            error instanceof Error ? error.message : "Unknown error occurred.";

        return NextResponse.json(
            { error: `System prompt generation failed: ${message}` },
            { status: 500 },
        );
    }
}
