import { NextResponse } from "next/server";
import { getGeminiModel, extractJsonFromText } from "@/lib/gemini";
import type {
  PromptRefinementResult,
  RefineRequestPayload,
} from "@/types/prompt";

const REFINEMENT_INSTRUCTIONS = `
You are an elite AI prompt engineer.
Craft a refined, ready-to-use prompt using the provided information.

Return a JSON object with the structure:
{
  "refinedPrompt": string,           // the improved prompt formatted for direct use
  "guidance": string,                // tips on how to apply or adapt the prompt
  "assumptions": string[],           // list any assumptions you had to make
  "evaluationCriteria": string[]     // checklist to verify responses from the target AI model
}

Guidelines:
- Respect the user's desired tone and output requirements when provided.
- Ensure the refined prompt includes all critical context and constraints.
- Keep the language clear and free of ambiguity.
- Never include markdown fences or commentary outside the JSON payload.
`.trim();

export async function POST(req: Request) {
  try {
    const body = (await req.json()) as RefineRequestPayload;
    const prompt = body.prompt?.trim();
    const targetModel = body.targetModel?.trim();
    const context = body.context?.trim();
    const tone = body.tone?.trim();
    const outputRequirements = body.outputRequirements?.trim();
    const questions = body.questions ?? [];
    const answers = body.answers ?? {};

    if (!prompt) {
      return NextResponse.json(
        { error: "Prompt text is required." },
        { status: 400 },
      );
    }

    if (!targetModel) {
      return NextResponse.json(
        { error: "Target model is required." },
        { status: 400 },
      );
    }

    if (!questions.length) {
      return NextResponse.json(
        {
          error:
            "Questions from the analysis phase are required to refine the prompt.",
        },
        { status: 400 },
      );
    }

    const model = getGeminiModel();

    const formattedQnA = questions
      .map((question) => {
        const answer = answers[question.id];
        return `Question (${question.id}): ${question.question}\nAnswer: ${
          answer ? answer.trim() : "[no answer supplied]"
        }`;
      })
      .join("\n\n");

    const userPrompt = [
      REFINEMENT_INSTRUCTIONS,
      "\n---\n",
      `Target model: ${targetModel}`,
      context ? `Additional context: ${context}` : "No extra context supplied.",
      tone ? `Desired tone: ${tone}` : "Tone: not specified.",
      outputRequirements
        ? `Output requirements: ${outputRequirements}`
        : "Output requirements: not specified.",
      "Original prompt:",
      prompt,
      "\nFollow-up answers:",
      formattedQnA,
    ].join("\n");

    const result = await model.generateContent({
      contents: [
        {
          role: "user",
          parts: [{ text: userPrompt }],
        },
      ],
      generationConfig: {
        temperature: 0.4,
        topP: 0.9,
        responseMimeType: "application/json",
      },
    });

    const rawText = result.response.text();
    const parsed = extractJsonFromText<PromptRefinementResult>(rawText);

    if (!parsed.refinedPrompt) {
      return NextResponse.json(
        { error: "The language model did not return a refined prompt." },
        { status: 502 },
      );
    }

    return NextResponse.json(parsed);
  } catch (error) {
    if (error instanceof SyntaxError) {
      return NextResponse.json(
        { error: "Failed to parse model response into JSON." },
        { status: 502 },
      );
    }

    const message =
      error instanceof Error ? error.message : "Unknown error occurred.";

    return NextResponse.json(
      { error: `Prompt refinement failed: ${message}` },
      { status: 500 },
    );
  }
}
