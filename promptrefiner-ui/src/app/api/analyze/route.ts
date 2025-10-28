import { NextResponse } from "next/server";
import { getGeminiModel, extractJsonFromText } from "@/lib/gemini";
import type {
  AnalyzeRequestPayload,
  PromptAnalysisResult,
} from "@/types/prompt";

const ANALYSIS_INSTRUCTIONS = `
You are an expert AI prompt engineer that helps users improve their prompts.

Return a strict JSON object with the following shape:
{
  "analysis": string,               // friendly overview of current prompt quality
  "improvementAreas": string[],     // bullet points describing missing detail or ambiguity
  "questions": [                    // between 2 and 4 targeted follow-up questions
    {
      "id": string,                 // short snake_case identifier
      "question": string,           // the question to ask the user
      "purpose": string             // short reason the question matters
    }
  ],
  "overallConfidence": string       // how ready the prompt is for production use
}

Guidelines:
- Make questions specific to the supplied prompt and target model.
- Avoid yes/no questions unless absolutely necessary.
- Focus on gaps in context, constraints, tone, or expected outputs.
- Never include markdown or additional prose outside of the JSON payload.
`.trim();

export async function POST(req: Request) {
  try {
    const body = (await req.json()) as AnalyzeRequestPayload;
    const prompt = body.prompt?.trim();
    const targetModel = body.targetModel?.trim();
    const context = body.context?.trim();

    if (!prompt) {
      return NextResponse.json(
        { error: "Prompt text is required." },
        { status: 400 },
      );
    }

    if (!targetModel) {
      return NextResponse.json(
        { error: "Target model is required so we can tailor the refinement." },
        { status: 400 },
      );
    }

    const model = getGeminiModel();

    const userPrompt = [
      ANALYSIS_INSTRUCTIONS,
      "\n---\n",
      `Target model: ${targetModel}`,
      context ? `Additional context: ${context}` : "No extra context supplied.",
      "Original prompt:",
      prompt,
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
    const parsed = extractJsonFromText<PromptAnalysisResult>(rawText);

    if (!Array.isArray(parsed.questions) || parsed.questions.length === 0) {
      return NextResponse.json(
        { error: "The language model did not return any follow-up questions." },
        { status: 502 },
      );
    }

    return NextResponse.json(parsed);
  } catch (error) {
    if (error instanceof SyntaxError) {
      return NextResponse.json(
        {
          error:
            "Failed to interpret the model output. Please try again or adjust your prompt.",
        },
        { status: 502 },
      );
    }

    const message =
      error instanceof Error ? error.message : "Unknown error occurred.";

    return NextResponse.json(
      { error: `Prompt analysis failed: ${message}` },
      { status: 500 },
    );
  }
}
