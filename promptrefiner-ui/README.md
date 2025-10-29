# PromptRefiner

PromptRefiner is a Next.js web application that turns rough ideas into polished, AI-ready prompts. It uses Google Gemini to critique the initial prompt, asks tailored follow-up questions, and generates a refined prompt optimized for the model you plan to use.

## Features

- 🔍 **Prompt analysis** – Gemini highlights gaps, missing context, and potential risks in the initial prompt and synthesizes a structured blueprint.
- ❓ **Dynamic follow-up questions** – Each prompt receives 2–5 custom questions to gather the missing information.
- 🛠️ **AI-ready prompt generation** – Produces a final prompt tailored to the target AI model, tone, and output requirements.
- ✅ **Quality guardrails** – Provides assumptions, change summaries, and evaluation criteria to help you vet model responses.
- 📚 **Few-shot metaprompting** – Analyzer and refiner calls load curated examples plus XML-tagged inputs to keep Gemini on-spec.
- 🌐 **Web context assist** – Optional Firecrawl-powered search enriches the blueprint with fresh facts when you enable it in the UI.
- 🔄 **One-click rewrite** – Don’t love the output? Tap “Re-write with new angle” to generate an alternate refinement – no need to re-answer clarifying questions.

## Requirements

- Node.js 18.17+ (Next.js 15 tooling prefers Node 20+, but the project currently runs on Node 18.19.1).
- A Google Gemini API key. You can create one in the [Google AI Studio](https://makersuite.google.com/app/apikey).
- (Optional) A [Firecrawl](https://firecrawl.dev/) API key if you want web-enriched analyses.

## Getting started

1. Install dependencies:

   ```bash
   npm install
   ```

2. Configure your environment variables:

   ```bash
   cp .env.example .env.local
   ```

   Update `.env.local` with your `GOOGLE_GEMINI_API_KEY`. Optionally add `FIRECRAWL_API_KEY` if you plan to enable web search, and override `GEMINI_MODEL` if you want to use a different Gemini model variant.

3. Start the development server:

   ```bash
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) and begin refining prompts.

## Project structure

- `src/app/page.tsx` – Main UI flow for analysis, question answering, and refinement.
- `src/app/api/analyze/route.ts` – Calls Gemini to critique the prompt and produce follow-up questions + blueprint JSON.
- `src/app/api/refine/route.ts` – Combines the original prompt, blueprint, and answers to generate the final prompt.
- `src/lib/gemini.ts` – Gemini client helper and JSON parsing utility.
- `src/types/prompt.ts` – Shared TypeScript interfaces for request/response payloads.
- `src/prompts/metaprompt.ts` – System prompts, few-shot exemplars, and versioning for analyzer/refiner calls.

## Prompt orchestration

- Analyzer responses include a `blueprint` object (intent, audience, success criteria, constraints, risks, evaluation checklist). The UI surfaces this so users see what Gemini inferred, and the refiner call reuses it for consistency.
- The refiner output always returns a markdown prompt with nine sections, plus usage guidance, change summary, assumptions, and evaluation checklist to close the loop.
- Few-shot pairs cover both creative build and analytical memo scenarios. Add more examples (see `examples.md` in the repo root) to broaden coverage.
- When Firecrawl search is enabled, the analyzer prompt receives an `<external_context>` block with cited snippets; the UI keeps those sources visible for transparency and we pass them to the refiner so instructions stay grounded.
- The target model selector offers high-level families (OpenAI GPT, Claude Sonnet/Opus/Haiku, Gemini Pro/Flash, Grok, Mistral) plus a “None / Not sure yet” fallback so the blueprint can adapt when users are undecided.
- All prompts share the `PROMPT_VERSION` tag—bump it when iterating on prompt design so you can trace which version generated a result.

## Next steps & ideas

- Add authentication so users can save prompt iterations.
- Store prompt histories and refinements for later reuse.
- Support additional LLM providers alongside Gemini by abstracting the refinement pipeline.
- Layer in automated tests for the API routes with mocked Gemini responses.
- Allow users to download the blueprint JSON and refined prompt as reusable templates.
- Add telemetry to compare prompt versions (A/B tests) and surface the highest performing metaprompt variants.

## Scripts

- `npm run dev` – Start the Next.js development server with Turbopack.
- `npm run lint` – Run ESLint with the Next.js configuration.
- `npm run build` – Create a production build.
- `npm run start` – Run the production server after building.

Happy prompting! 🎯
