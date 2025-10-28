# PromptRefiner

PromptRefiner is a Next.js web application that turns rough ideas into polished, AI-ready prompts. It uses Google Gemini to critique the initial prompt, asks tailored follow-up questions, and generates a refined prompt optimized for the model you plan to use.

## Features

- 🔍 **Prompt analysis** – Gemini highlights gaps, missing context, and potential risks in the initial prompt.
- ❓ **Dynamic follow-up questions** – Each prompt receives 2–4 custom questions to gather the missing information.
- 🛠️ **AI-ready prompt generation** – Produces a final prompt tailored to the target AI model, tone, and output requirements.
- ✅ **Quality guardrails** – Provides assumptions and evaluation criteria to help you vet model responses.

## Requirements

- Node.js 18.17+ (Next.js 15 tooling prefers Node 20+, but the project currently runs on Node 18.19.1).
- A Google Gemini API key. You can create one in the [Google AI Studio](https://makersuite.google.com/app/apikey).

## Getting started

1. Install dependencies:

   ```bash
   npm install
   ```

2. Configure your environment variables:

   ```bash
   cp .env.example .env.local
   ```

   Update `.env.local` with your `GOOGLE_GEMINI_API_KEY`. Optionally override `GEMINI_MODEL` if you want to use a different Gemini model variant.

3. Start the development server:

   ```bash
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) and begin refining prompts.

## Project structure

- `src/app/page.tsx` – Main UI flow for analysis, question answering, and refinement.
- `src/app/api/analyze/route.ts` – Calls Gemini to critique the prompt and produce follow-up questions.
- `src/app/api/refine/route.ts` – Combines the original prompt+answers to generate the final prompt.
- `src/lib/gemini.ts` – Gemini client helper and JSON parsing utility.
- `src/types/prompt.ts` – Shared TypeScript interfaces for request/response payloads.

## Next steps & ideas

- Add authentication so users can save prompt iterations.
- Store prompt histories and refinements for later reuse.
- Support additional LLM providers alongside Gemini by abstracting the refinement pipeline.
- Layer in automated tests for the API routes with mocked Gemini responses.

## Scripts

- `npm run dev` – Start the Next.js development server with Turbopack.
- `npm run lint` – Run ESLint with the Next.js configuration.
- `npm run build` – Create a production build.
- `npm run start` – Run the production server after building.

Happy prompting! 🎯
