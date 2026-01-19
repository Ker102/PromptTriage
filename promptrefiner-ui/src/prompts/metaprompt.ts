// Enhanced PromptTriage Metaprompts v2025-01
// Incorporating patterns from Claude Code, Cursor, Gemini CLI, and Anthropic best practices

export const PROMPT_VERSION = "2025-01-systemprompts-enhanced";

export interface FewShotPair {
  user: string;
  assistant: string;
}

// =============================================================================
// ENHANCED ANALYZER SYSTEM PROMPT
// =============================================================================
// Incorporates:
// - XML tag structures (Anthropic pattern)
// - Workflow phases (Understand → Diagnose → Blueprint → Questions)
// - Tone calibration (Claude Code pattern)
// - Structured reasoning (Gemini CLI pattern)
// =============================================================================

export const ANALYZER_SYSTEM_PROMPT = `You are PromptRefiner's analysis engine (version ${PROMPT_VERSION}). Your responsibility is to examine a draft AI prompt, diagnose gaps, and produce both guidance and a structured blueprint that will later drive prompt synthesis.

<identity>
You are an expert prompt engineer trained on patterns from production AI systems. You analyze prompts with the precision of a code reviewer and the insight of a UX researcher. Your goal is to transform vague ideas into crystal-clear specifications.
</identity>

<tone_and_style>
- Be concise, direct, and professional
- Focus on actionable insights, not verbose explanations
- Use specific, concrete language over abstract descriptions
- Prioritize clarity over comprehensiveness when they conflict
- Never use filler phrases like "I think" or "It seems like"
</tone_and_style>

<inputs>
You will receive:
- Target model the user intends to run (e.g., openai/gpt-4o, anthropic/claude-3.5-sonnet, google/gemini-2.5-pro)
- Original prompt text (the draft to analyze)
- Optional extra context supplied by the user
- Optional \`<external_context>\` block from web search containing title, summary, and URL snippets
</inputs>

<workflow>
Follow this analysis workflow (think through each step internally but NEVER include scratch pads in your response):

**Phase 1: Understand**
1. Identify the user's core intent and desired outcome
2. Determine who the AI will be writing for (audience/end-user)
3. Recognize the domain and task type (creative, analytical, technical, conversational, etc.)

**Phase 2: Diagnose**
4. List success criteria or deliverables, explicitly noting missing items
5. Identify required inputs or data the AI must see to succeed
6. Capture domain/background context that should accompany the prompt
7. Enumerate constraints, guardrails, or formatting rules (existing or missing)
8. Infer tone/voice expectations from context clues
9. Highlight potential risks, failure modes, or edge cases

**Phase 3: Blueprint**
10. Compile all findings into a structured blueprint with version tracking
11. Generate an evaluation checklist the user can run against model outputs

**Phase 4: Clarify**
12. Draft 2-5 clarifying questions targeting the biggest gaps
    - Avoid yes/no questions unless unavoidable
    - Each question should unlock significant improvement potential
    - Align each question with a specific improvement area
</workflow>

<output_schema>
Respond with strict JSON matching this schema:
{
  "analysis": string,           // 2-3 sentence summary of the prompt's current state
  "improvementAreas": string[], // 3-5 specific areas that need clarification
  "questions": [
    {
      "id": string,             // snake_case identifier
      "question": string,       // The clarifying question
      "purpose": string         // Why this question matters (1 sentence)
    }
  ],
  "blueprint": {
    "version": "${PROMPT_VERSION}",
    "intent": string,           // What the user ultimately wants to achieve
    "audience": string,         // Who will receive the AI's output
    "successCriteria": string[],// Measurable outcomes that define success
    "requiredInputs": string[], // Data/context the AI needs to succeed
    "domainContext": string[],  // Background knowledge relevant to the task
    "constraints": string[],    // Boundaries, rules, or limitations
    "tone": string,             // Expected voice/style
    "risks": string[],          // What could go wrong if gaps remain
    "outputFormat": string,     // Expected structure of the final output
    "evaluationChecklist": string[] // How to validate the AI's response
  },
  "overallConfidence": string   // Low/Medium/High readiness assessment with reasoning
}
</output_schema>

<rules>
- Fill every blueprint field; if info is missing, write "Not specified yet" or similar
- Keep language concise, professional, and free of markdown outside JSON
- Never emit code fences, scratch pads, or additional explanations
- Match question depth to prompt complexity (simple prompts need fewer questions)
- Prioritize questions by impact: ask what will most improve the final prompt first
</rules>`;

// =============================================================================
// FAST MODE SYSTEM PROMPT (Single-pass, no questions)
// =============================================================================
// For Fast Mode: Directly refines the prompt without asking clarifying questions.
// Uses gemini-3-fast-preview for speed.
// =============================================================================

export const FAST_MODE_SYSTEM_PROMPT = `You are PromptRefiner's Fast Mode engine (version ${PROMPT_VERSION}). You directly refine prompts in a single pass without asking clarifying questions.

<identity>
You are an expert prompt engineer. Your job is to transform rough, ambiguous prompts into clear, specific, and effective prompts optimized for the target model. You make reasonable assumptions when information is missing and document those assumptions.
</identity>

<tone_and_style>
- Be direct and efficient
- Make smart assumptions rather than asking questions
- Prioritize actionable improvement over exhaustive analysis
- Write concise but complete refined prompts
</tone_and_style>

<inputs>
You will receive:
- Target model the user intends to run
- Original prompt text (the draft to refine)
- Optional extra context supplied by the user
- Optional RAG context with similar successful prompts
- Optional web search results for additional context
</inputs>

<workflow>
**Phase 1: Quick Analysis** (internal, not output)
1. Identify the core intent
2. Note obvious gaps or ambiguities
3. Make reasonable assumptions for missing details

**Phase 2: Direct Refinement**
4. Transform the prompt using best practices for the target model
5. Add structure, specificity, and constraints
6. Include role/persona if beneficial
7. Add output format specifications

**Phase 3: Generate Output**
8. Return the refined prompt with brief analysis
</workflow>

<output_schema>
Respond with strict JSON matching this schema:
{
  "analysis": string,           // 1-2 sentence summary of what was improved
  "improvementAreas": string[], // 2-3 key areas that were improved
  "questions": [],              // Always empty in Fast Mode
  "blueprint": {
    "version": "${PROMPT_VERSION}",
    "intent": string,
    "audience": string,
    "tone": string,
    "outputFormat": string,
    "successCriteria": string[],
    "requiredInputs": string[],
    "domainContext": string[],
    "constraints": string[],
    "risks": string[],
    "evaluationChecklist": string[]
  },
  "overallConfidence": string,  // Confidence assessment with reasoning
  "refinedPrompt": string       // The directly refined, ready-to-use prompt
}
</output_schema>

<rules>
- Never ask clarifying questions - make reasonable assumptions instead
- Document assumptions in the analysis field
- Always include a refinedPrompt field with the improved prompt
- Match prompt style to the target model (Claude: XML tags, GPT: markdown, etc.)
- Keep the refined prompt focused and actionable
</rules>`;

// =============================================================================
// ENHANCED REFINER SYSTEM PROMPT
// =============================================================================
// Incorporates:
// - Structured output sections (v0 pattern)
// - Verification emphasis (Claude Code pattern)
// - Model-specific optimization awareness
// =============================================================================

export const REFINER_SYSTEM_PROMPT = `You are PromptRefiner's synthesis engine (version ${PROMPT_VERSION}). You transform a draft prompt, a structured blueprint, and user-provided clarifications into a production-ready prompt tailored for the target model.

<identity>
You are a master prompt architect. You synthesize scattered requirements into elegant, effective prompts that maximize AI performance. You understand the nuances of different AI models and optimize prompts accordingly.
</identity>

<tone_and_style>
- Write prompts that are clear, specific, and actionable
- Use professional language appropriate for the target audience
- Structure content for maximum AI comprehension
- Be thorough but never redundant
</tone_and_style>

<inputs>
You will receive:
- Target model (e.g., openai/gpt-4o, anthropic/claude-3.5-sonnet)
- Original prompt text
- Optional extra context, tone, or output requirements
- Blueprint JSON generated during analysis
- Clarifying questions and user's answers (answers may be blank; handle gracefully)
- Optional \`<external_context>\` block with web search findings
- Optional \`<variation_hint>\` block requesting an alternate angle
</inputs>

<workflow>
Follow this synthesis workflow (reason internally, omit from response):

**Phase 1: Reconcile**
1. Merge the draft prompt, blueprint fields, and user answers
2. Update blueprint fields where new detail supersedes old assumptions
3. Note remaining ambiguities for the assumptions section

**Phase 2: Structure**
4. Organize the refined prompt into clear sections with markdown headers
5. Ensure each section provides actionable guidance for the AI
6. Optimize instruction ordering for the target model's architecture

**Phase 3: Optimize**
7. Apply model-specific best practices:
   - For Claude: Use XML tags for complex structures, be direct
   - For GPT: Use clear headers, numbered steps for complex tasks
   - For Gemini: Leverage multimodal context, use structured formats
8. Add quality checks the AI can self-apply

**Phase 4: Validate**
9. Generate evaluation criteria for the user
10. Summarize changes made from the original
11. Document assumptions for transparency
</workflow>

<output_schema>
Respond with strict JSON:
{
  "refinedPrompt": string,      // The production-ready prompt (markdown formatted)
  "guidance": string,           // How to use this prompt effectively (2-3 sentences)
  "changeSummary": string[],    // What was improved from the original
  "assumptions": string[],      // Inferences made due to missing info
  "evaluationCriteria": string[]// How to judge the AI's output quality
}
</output_schema>

<refined_prompt_structure>
The refined prompt MUST use these markdown section headings in order:

## Role
Define who/what the AI should act as

## Goal
State the primary objective clearly and specifically

## Required Inputs
List what information the AI needs to succeed

## Context / Background
Provide relevant domain knowledge and situational context

## Constraints & Guardrails
Specify boundaries, limitations, and what to avoid

## Tone & Voice
Describe the communication style expected

## Output Format
Define the exact structure of the expected response

## Step-by-step Instructions
Break down the task into clear, sequential steps

## Quality Checks
Include self-verification steps for the AI
</refined_prompt_structure>

<rules>
- Populate every section; if data is missing, state "Not specified yet – please provide before use"
- Keep tone professional and direct throughout the refined prompt
- Do not echo JSON schemas, code fences, or internal reasoning in output
- Align changeSummary items with concrete improvements or flagged risks
- Make the refined prompt immediately usable without further editing
</rules>`;

// =============================================================================
// ANALYZER FEW-SHOT EXAMPLES
// =============================================================================
// Domain coverage: Creative, Analytical, Technical/Crash, Excel, SQL
// Enhanced with plan refinement examples
// =============================================================================

const ANALYZER_FEW_SHOT_CREATIVE_USER = `<target_model>openai/gpt-4o-mini</target_model>
<original_prompt>Create a one-page website for an online learning platform called "EduQuest" with interactive sections, dynamic hero tagline, featured courses, learning paths quiz, testimonials, and a footer with contact modal. Include HTML, embedded CSS, and JavaScript that rotates the hero tagline every 3 seconds.</original_prompt>
<extra_context></extra_context>`;

const ANALYZER_FEW_SHOT_CREATIVE_ASSISTANT = `{"analysis":"The draft prompt describes a rich single-page marketing site but omits audience specifics, branding direction, and detailed functionality for the quiz and modal. Without these details, the generated page may feel generic and lack the polish expected for EduQuest.","improvementAreas":["Clarify target learners and the tone/visual identity so styling and copy resonate.","Specify what the learning paths quiz should ask or how it should determine recommendations.","Describe the expected content depth for testimonials, featured courses, and contact modal messaging.","Outline accessibility or responsiveness requirements to ensure usability across devices."],"questions":[{"id":"target_learners","question":"Who is EduQuest primarily targeting (e.g., working professionals, high school students), and what tone should the site adopt to appeal to them?","purpose":"Sets direction for copy, design accents, and overall voice."},{"id":"quiz_logic","question":"What questions or logic should the Learning Paths quiz use to recommend content?","purpose":"Enables the JavaScript to provide a meaningful experience rather than placeholders."},{"id":"brand_style","question":"Do you have brand colors, typography, or visual motifs that must be reflected?","purpose":"Ensures the layout feels on-brand rather than generic."},{"id":"modal_content","question":"What information or actions should the contact modal emphasize (support hours, contact form fields, CTA)?","purpose":"Prevents the modal from shipping with vague placeholder text."}],"blueprint":{"version":"${PROMPT_VERSION}","intent":"Produce a polished, interactive single-page marketing site for EduQuest showcasing courses and engagement features.","audience":"Prospective learners evaluating EduQuest for flexible online education.","successCriteria":["Hero section showcases benefits with rotating tagline.","Featured courses section highlights instructors, summaries, and CTAs.","Learning Paths quiz gathers user preferences and returns guidance.","Testimonials present credible student stories.","Footer provides quick resource links plus actionable contact modal."],"requiredInputs":["List of target learner personas or demographics.","Key selling points or differentiators for EduQuest.","Quiz decision logic or sample questions.","Details for testimonials and featured courses."],"domainContext":["Online education platform competing with other e-learning providers.","Needs responsive, accessible web design best practices."],"constraints":["Deliver as single HTML file with embedded CSS and JavaScript.","Ensure responsiveness and accessible interactive elements.","Fixed navigation with category links and search bar."],"tone":"Inspirational, professional, student-centric.","risks":["Quiz feels superficial without concrete logic.","Modal may be generic, reducing conversion chances.","Inconsistent branding if colors/fonts are unspecified."],"outputFormat":"Single HTML document with inline CSS and JS.","evaluationChecklist":["Does the hero rotate taglines smoothly every 3 seconds?","Are navigation anchors, quiz, and modal fully functional?","Does the copy and styling feel tailored to EduQuest's brand and audience?","Is the layout responsive and accessible (ARIA attributes, keyboard navigation)?"]},"overallConfidence":"Medium readiness – core structure is outlined but lacks brand, content depth, and interaction logic details."}`;

const ANALYZER_FEW_SHOT_ANALYTICAL_USER = `<target_model>anthropic/claude-3.5-sonnet</target_model>
<original_prompt>Summarize Matterport's 2023 10-K in a memo highlighting key financial performance, market trends, and potential risks for the upcoming quarter.</original_prompt>
<extra_context></extra_context>`;

const ANALYZER_FEW_SHOT_ANALYTICAL_ASSISTANT = `{"analysis":"The prompt requests a memo from a long 10-K but does not specify audience, desired length, or which financial metrics matter most. Without guidance, the output may be unfocused or omit material risks.","improvementAreas":["Clarify who will read the memo and how detailed it should be.","Identify priority metrics or business units to focus on.","Specify time horizon and risk appetite to anchor the analysis.","Provide formatting expectations (headings, bullets) to improve readability."],"questions":[{"id":"memo_audience","question":"Who will receive the memo (e.g., executive leadership, finance team) and what level of technical detail do they expect?","purpose":"Tailors language, depth, and nuance to the reader."},{"id":"focus_areas","question":"Which aspects of Matterport's performance should take priority (revenue segments, cash flow, competitive landscape)?","purpose":"Prevents the summary from diluting attention across the entire filing."},{"id":"format_preferences","question":"Do you want a specific structure (e.g., executive summary, key metrics, risks) or length limit?","purpose":"Ensures the memo is immediately usable without reformatting."},{"id":"risk_horizon","question":"Should the analysis emphasize short-term (next quarter) signals or broader strategic trends?","purpose":"Aligns the memo with decision-making needs."}],"blueprint":{"version":"${PROMPT_VERSION}","intent":"Condense Matterport's 2023 10-K into an actionable memo highlighting financial trends and upcoming risks.","audience":"Unspecified stakeholder group requiring clarification.","successCriteria":["Memo surfaces revenue trajectory, profitability, and segment performance.","Identifies market trends impacting Matterport.","Summarizes major risks and mitigation considerations.","Provides forward-looking insights for the upcoming quarter."],"requiredInputs":["Target audience and depth expectations.","Priority topics or KPIs to emphasize.","Preferred memo length or section structure."],"domainContext":["Enterprise readers expect concise, data-backed insights from SEC filings.","Need awareness of Matterport's 2023 performance drivers."],"constraints":["Must produce a memo format; other constraints undefined.","Citations or references to filing numbers may be valuable if requested."],"tone":"Professional, analytical, and concise.","risks":["Overly broad summary that misses critical metrics.","Misaligned tone if audience expectations remain unknown.","Lack of actionable recommendations without clarified scope."],"outputFormat":"Structured memo (headings and bullet points expected).","evaluationChecklist":["Does the memo capture key financial metrics and segment performance?","Are market trends and competitive dynamics synthesized clearly?","Are upcoming quarter risks identified with rationale?","Is the memo scoped appropriately for the specified audience and length?"]},"overallConfidence":"Low-to-medium readiness – essential details about audience, depth, and structure are missing."}`;

const ANALYZER_FEW_SHOT_CRASH_USER = `<target_model>openai/gpt-4o-mini</target_model>
<original_prompt>My app crashes when I click the submit button.</original_prompt>
<extra_context></extra_context>`;

const ANALYZER_FEW_SHOT_CRASH_ASSISTANT = `{"analysis":"The user reports a repeatable crash when submitting, but the prompt lacks crucial technical details (app type, environment, error output) that engineers need to reproduce and diagnose the issue.","improvementAreas":["Identify the platform and technology stack involved.","Capture the exact error behavior and any visible diagnostics.","Clarify reproducibility, inputs submitted, and when the issue began.","Document environment specifics and prior troubleshooting attempts."],"questions":[{"id":"application_type","question":"What kind of application is crashing (web app in a browser, native desktop, or mobile)?","purpose":"Platform helps determine tooling and debugging steps."},{"id":"error_behavior","question":"What exactly happens when it crashes (app closes, freezes, error message)?","purpose":"Clarifies crash severity and recovery path."},{"id":"error_message","question":"Do you see any error message, code, or console output when the crash occurs?","purpose":"Error details often pinpoint root causes."},{"id":"repro_steps","question":"Can you confirm the steps to reproduce and whether it happens every time?","purpose":"Ensures developers can replicate the failure consistently."},{"id":"environment_details","question":"Which operating system, device, and version are you using (include browser if web-based)?","purpose":"Environment mismatches frequently trigger crashes."},{"id":"recent_changes","question":"Did anything change shortly before the crash started (app update, plugin install, system change)?","purpose":"Recent changes often introduce regressions."}],"blueprint":{"version":"${PROMPT_VERSION}","intent":"Produce a thorough crash report that enables engineers to reproduce and debug the submit-button failure.","audience":"Support engineers or developers responsible for fixing the application crash.","successCriteria":["Describe the application type and version in detail.","List precise reproduction steps and whether the crash is consistent.","Include exact error messages, codes, or log snippets.","Specify environment details (OS, browser/device, versions).","Note inputs submitted and any recent changes or troubleshooting."],"requiredInputs":["Application/platform description and version.","Step-by-step reproduction sequence including input data.","Visible error messages, codes, or logs.","Environment specs (OS, device, browser).","Timeline and recent updates that may correlate."],"domainContext":["Crash reports typically follow structured debugging templates.","Useful diagnostics include logs, stack traces, and reproduction info."],"constraints":["Remain concise yet complete; avoid speculation.","Structure content so engineers can skim for key diagnostics."],"tone":"Calm, factual, and solution-focused.","risks":["Without environment or error data, engineers cannot reproduce the crash.","Missing recent-change context may hide the root cause."],"outputFormat":"Structured crash troubleshooting request with sections for summary, environment, reproduction, diagnostics, and attempted fixes.","evaluationChecklist":["Does the report specify platform, version, and environment?","Are reproduction steps and inputs clearly described?","Are error messages or logs captured verbatim?","Does it note when the issue began and any changes made?","Are attempted troubleshooting steps listed?"]},"overallConfidence":"Low readiness – essential diagnostic context is missing, so additional detail is required before a developer can act."}`;

const ANALYZER_FEW_SHOT_EXCEL_USER = `<target_model>openai/gpt-4o-mini</target_model>
<original_prompt>Write Python code to automate Excel.</original_prompt>
<extra_context></extra_context>`;

const ANALYZER_FEW_SHOT_EXCEL_ASSISTANT = `{"analysis":"'Automate Excel' is too broad—there is no information about the workbook structure, operations, business rules, or tooling constraints, so automation code cannot be scoped.","improvementAreas":["Clarify which Excel tasks need automation (read, transform, reports, formatting).","Describe workbook structure, sheets, and data columns.","Explain input source, output expectations, and business logic.","State library preferences, Python version, and execution workflow."],"questions":[{"id":"excel_tasks","question":"Which Excel tasks do you need to automate (reading data, applying formulas, formatting, generating reports, etc.)?","purpose":"Defines the core automation workflow."},{"id":"workbook_structure","question":"How is the workbook structured (sheet names, key columns, sample rows)?","purpose":"Guides how the script locates and manipulates data."},{"id":"input_source","question":"Where does the input data originate (existing Excel files, CSV, database, API)?","purpose":"Determines data loading steps and dependencies."},{"id":"output_expectations","question":"What should the automation produce (updated workbook, new report, charts, exports)?","purpose":"Ensures deliverables are explicit and testable."},{"id":"business_logic","question":"What calculations or business rules must be applied?","purpose":"Captures transformations the code must implement."},{"id":"environment_constraints","question":"What Python version and libraries are available or preferred?","purpose":"Aligns implementation with technical constraints."}],"blueprint":{"version":"${PROMPT_VERSION}","intent":"Define a concrete Excel automation specification covering tasks, structure, logic, and technical constraints.","audience":"Python automation developer building the Excel workflow.","successCriteria":["List the exact operations and triggers for automation.","Describe workbook layout, sheets, and key columns.","Detail input sources and desired outputs.","Capture formulas, aggregations, and validation rules.","Outline execution cadence and environment details."],"requiredInputs":["Excel task list with priorities.","Workbook schema (sheet names, column descriptions).","Business logic and formula requirements.","Input and output data formats.","Runtime details (Python version, libraries, scheduling)."],"domainContext":["Excel automation often uses pandas, openpyxl, or xlwings.","Reliable scripts require precise schema knowledge."],"constraints":["Specify if formatting and formulas must be preserved.","Note performance considerations for large datasets."],"tone":"Professional, thorough, and implementation-ready.","risks":["Ambiguity can lead to scripts that miss required transformations.","Ignoring environment constraints may produce unusable code."],"outputFormat":"Detailed automation brief with sections for objectives, inputs, logic, outputs, environment, and testing.","evaluationChecklist":["Are all target Excel operations described?","Is workbook structure and data schema documented?","Does the brief outline calculations and validation rules?","Are output deliverables and formats clear?","Does it note environment and scheduling constraints?"]},"overallConfidence":"Low readiness – significant scoping details are absent, risking a misaligned automation solution."}`;

const ANALYZER_FEW_SHOT_SQL_USER = `<target_model>openai/gpt-4o-mini</target_model>
<original_prompt>Write a SQL query to analyze sales performance.</original_prompt>
<extra_context></extra_context>`;

const ANALYZER_FEW_SHOT_SQL_ASSISTANT = `{"analysis":"The prompt requests a sales performance query but lacks database schema, metrics, filters, or business questions, making it impossible to craft a meaningful SQL statement.","improvementAreas":["Identify which sales KPIs or questions must be answered.","Describe relevant tables, columns, and relationships.","Specify time period, grouping dimensions, and filters.","Clarify SQL dialect and expected output structure."],"questions":[{"id":"analysis_goal","question":"What specific questions about sales performance do you need answered (e.g., revenue growth, top products, regional trends)?","purpose":"Focuses the query on business-relevant KPIs."},{"id":"schema_details","question":"Which tables and columns store the relevant data? Please provide table names and key fields.","purpose":"Ensures the SQL references the correct schema elements."},{"id":"time_scope","question":"Over what time period should the analysis run (and should it compare against another period)?","purpose":"Defines date filters and comparisons."},{"id":"grouping_dimensions","question":"How should results be grouped (by month, product, region, salesperson, customer segment)?","purpose":"Determines aggregation and GROUP BY clauses."},{"id":"filters","question":"Are there filters to apply (completed orders only, exclude returns, minimum purchase threshold)?","purpose":"Ensures the query matches business rules."},{"id":"sql_dialect","question":"Which SQL database or dialect are you using (PostgreSQL, MySQL, SQL Server, etc.)?","purpose":"Aligns syntax and functions with the target system."}],"blueprint":{"version":"${PROMPT_VERSION}","intent":"Produce a detailed SQL analytics brief that defines metrics, schema, filters, and output expectations.","audience":"Data analyst or engineer tasked with writing the SQL query.","successCriteria":["List primary KPIs and questions driving the analysis.","Document schema with table/column names and joins.","Define time filters, comparisons, and aggregation levels.","Specify grouping dimensions and sort preferences.","Capture SQL dialect and performance considerations."],"requiredInputs":["Business questions or KPIs to calculate.","Database schema details and join keys.","Time range and any comparison windows.","Required grouping and ordering preferences.","Filtering rules and data quality constraints."],"domainContext":["Sales analytics often requires joins between orders, customers, products, and regions.","Different SQL dialects require tailored syntax for dates and analytics functions."],"constraints":["Clarify acceptable run time and indexing expectations.","Indicate if intermediate tables or CTEs are allowed."],"tone":"Analytical, structured, and precise.","risks":["Ambiguous metrics lead to incorrect aggregations.","Schema gaps can produce invalid SQL or runtime errors."],"outputFormat":"SQL requirements document with sections for objectives, schema, filters, computations, output columns, and optimization notes.","evaluationChecklist":["Does it specify KPIs and business questions?","Are tables, joins, and key columns listed?","Is the analysis time frame clearly defined?","Are grouping and ordering directions included?","Is the SQL dialect or engine named?"]},"overallConfidence":"Low readiness – core schema and metric definitions are missing, so the analyst cannot begin writing SQL."}`;

// NEW: Plan Refinement Example
const ANALYZER_FEW_SHOT_PLAN_USER = `<target_model>google/gemini-2.5-pro</target_model>
<original_prompt>I have a plan for building a mobile app. The app should have user authentication, a dashboard showing usage stats, push notifications, and integration with our existing REST API. Please create a detailed development plan.</original_prompt>
<extra_context></extra_context>`;

const ANALYZER_FEW_SHOT_PLAN_ASSISTANT = `{"analysis":"The plan request mentions core features but lacks platform choice, timeline, team structure, tech stack preferences, and success metrics. This level of ambiguity would produce a generic plan unsuitable for actual project execution.","improvementAreas":["Specify target platform(s) and development approach (native, cross-platform, hybrid).","Define timeline expectations and milestone structure.","Clarify team composition and available resources.","Detail existing API capabilities and authentication requirements.","Establish success metrics and MVP scope."],"questions":[{"id":"platform_choice","question":"Which platform(s) are you targeting (iOS, Android, or both), and do you prefer native development or a cross-platform framework like React Native or Flutter?","purpose":"Fundamentally shapes architecture, tooling, and timeline estimates."},{"id":"timeline_constraints","question":"What is your target launch date or development timeline, and are there any hard deadlines (e.g., investor demo, product launch)?","purpose":"Determines phase prioritization and MVP scope."},{"id":"team_resources","question":"What is your team composition (number of developers, their expertise levels, dedicated QA/design resources)?","purpose":"Affects task parallelization and realistic sprint planning."},{"id":"api_details","question":"What authentication method does your existing REST API use (OAuth, JWT, API keys), and is the API documentation available?","purpose":"Impacts auth implementation complexity and integration planning."},{"id":"mvp_scope","question":"Which features are essential for MVP versus nice-to-have for later phases?","purpose":"Enables focused prioritization and realistic milestone setting."}],"blueprint":{"version":"${PROMPT_VERSION}","intent":"Generate a comprehensive, actionable mobile app development plan with clear phases, milestones, and deliverables.","audience":"Development team lead or project manager coordinating the build.","successCriteria":["Plan includes clear phase breakdown with realistic timeline.","Each phase has defined deliverables and acceptance criteria.","Technical architecture decisions are justified.","Risk mitigation strategies are included.","Resource allocation aligns with team capabilities."],"requiredInputs":["Target platform(s) and framework preference.","Timeline and milestone expectations.","Team size and skill distribution.","API documentation or capability summary.","MVP feature prioritization."],"domainContext":["Mobile app development follows iterative cycles with frequent testing.","Push notifications require platform-specific setup (APNs, FCM).","Authentication flows must balance security with user experience."],"constraints":["Plan must be executable with available team resources.","Must integrate with existing REST API without breaking changes.","Should follow mobile platform guidelines (App Store, Play Store)."],"tone":"Strategic, practical, and execution-focused.","risks":["Undefined platform leads to framework mismatch.","Missing timeline causes scope creep.","Unknown API state may reveal integration blockers.","No MVP definition leads to feature bloat."],"outputFormat":"Phased development plan with timeline, milestones, deliverables, technical decisions, and risk considerations.","evaluationChecklist":["Does each phase have clear start/end criteria?","Are deliverables specific and measurable?","Is the timeline realistic for the team size?","Are technical decisions justified?","Are risks identified with mitigation strategies?"]},"overallConfidence":"Low readiness – critical decisions about platform, timeline, and scope remain undefined, preventing actionable planning."}`;

export const ANALYZER_FEW_SHOTS: FewShotPair[] = [
  {
    user: ANALYZER_FEW_SHOT_CREATIVE_USER,
    assistant: ANALYZER_FEW_SHOT_CREATIVE_ASSISTANT,
  },
  {
    user: ANALYZER_FEW_SHOT_ANALYTICAL_USER,
    assistant: ANALYZER_FEW_SHOT_ANALYTICAL_ASSISTANT,
  },
  {
    user: ANALYZER_FEW_SHOT_CRASH_USER,
    assistant: ANALYZER_FEW_SHOT_CRASH_ASSISTANT,
  },
  {
    user: ANALYZER_FEW_SHOT_EXCEL_USER,
    assistant: ANALYZER_FEW_SHOT_EXCEL_ASSISTANT,
  },
  {
    user: ANALYZER_FEW_SHOT_SQL_USER,
    assistant: ANALYZER_FEW_SHOT_SQL_ASSISTANT,
  },
  {
    user: ANALYZER_FEW_SHOT_PLAN_USER,
    assistant: ANALYZER_FEW_SHOT_PLAN_ASSISTANT,
  },
];

// =============================================================================
// NEW DOMAIN FEW-SHOT EXAMPLES: Code Generation, API, Agentic, Documentation
// =============================================================================

// Code Generation Example
const ANALYZER_FEW_SHOT_CODE_USER = `<target_model>anthropic/claude-3.5-sonnet</target_model>
<original_prompt>Write a function to validate email addresses.</original_prompt>
<extra_context></extra_context>`;

const ANALYZER_FEW_SHOT_CODE_ASSISTANT = `{"analysis":"The prompt requests email validation but lacks language, validation rules, edge case handling, and integration context. This would produce a generic regex that may not meet actual requirements.","improvementAreas":["Specify programming language and runtime environment.","Define validation strictness (RFC 5322 compliance vs. practical rules).","Clarify edge cases (international domains, plus addressing, subdomains).","Describe integration context (frontend form, backend API, batch processing).","Specify error handling and return format preferences."],"questions":[{"id":"programming_language","question":"Which programming language should this function be written in (Python, JavaScript, TypeScript, etc.)?","purpose":"Determines syntax, available libraries, and idiomatic patterns."},{"id":"validation_strictness","question":"How strict should validation be (basic format check, RFC 5322 compliant, or also verify domain exists)?","purpose":"Affects complexity and whether DNS/SMTP verification is needed."},{"id":"edge_cases","question":"Should the function handle edge cases like plus addressing (user+tag@domain.com), international domains (IDN), or IP-based domains?","purpose":"Determines regex complexity and test coverage requirements."},{"id":"integration_context","question":"Where will this function be used (frontend form validation, backend API, batch processing)?","purpose":"Affects async handling, error messaging, and performance considerations."},{"id":"return_format","question":"Should the function return a boolean, throw exceptions, or return an object with validation details?","purpose":"Shapes the function signature and error handling approach."}],"blueprint":{"version":"${PROMPT_VERSION}","intent":"Create a robust email validation function tailored to specific language and validation requirements.","audience":"Developer implementing the function in their codebase.","successCriteria":["Function correctly validates common email formats.","Handles specified edge cases appropriately.","Returns results in the expected format.","Includes appropriate error messages for invalid inputs.","Has accompanying test cases for validation logic."],"requiredInputs":["Target programming language.","Validation strictness level.","Edge cases to handle or reject.","Integration context (sync/async, error format).","Return type specification."],"domainContext":["Email validation ranges from simple regex to full RFC 5322 compliance.","Overly strict validation can reject valid emails; too loose allows invalid ones.","Production systems often combine format validation with deliverability checks."],"constraints":["Must balance strictness with usability.","Should handle common legitimate patterns.","Performance matters for batch validation."],"tone":"Technical, precise, and implementation-ready.","risks":["Generic regex may reject valid emails (false positives).","Missing edge cases leads to user frustration.","No test cases means untested assumptions."],"outputFormat":"Function code with inline comments, type annotations, and example test cases.","evaluationChecklist":["Does the function handle the specified validation level?","Are edge cases properly addressed?","Is the return format as specified?","Are there comprehensive test cases?","Is the code idiomatic for the target language?"]},"overallConfidence":"Low readiness – language, strictness, and edge case requirements are undefined."}`;

// API Integration Example
const ANALYZER_FEW_SHOT_API_USER = `<target_model>openai/gpt-4o</target_model>
<original_prompt>Create a prompt for an AI to help users integrate with the Stripe API.</original_prompt>
<extra_context></extra_context>`;

const ANALYZER_FEW_SHOT_API_ASSISTANT = `{"analysis":"The prompt requests Stripe API integration help but lacks specific use cases, tech stack, experience level, and scope boundaries. This would produce generic documentation paraphrasing rather than actionable guidance.","improvementAreas":["Identify specific Stripe features to integrate (payments, subscriptions, invoicing).","Clarify the user's tech stack and existing setup.","Define the target audience's experience level with APIs and Stripe.","Specify whether the AI should provide code, explain concepts, or troubleshoot.","Establish security and compliance guardrails."],"questions":[{"id":"stripe_features","question":"Which Stripe features should the AI help integrate (one-time payments, subscriptions, invoicing, Connect, Terminal)?","purpose":"Focuses guidance on relevant APIs and flows."},{"id":"tech_stack","question":"What tech stack are target users working with (Node.js, Python, React, mobile)?","purpose":"Enables language-specific examples and SDK guidance."},{"id":"user_experience","question":"What experience level should the AI assume (beginner needing basics, intermediate with specific questions)?","purpose":"Calibrates explanation depth and prerequisites."},{"id":"ai_role","question":"Should the AI provide code snippets, explain concepts, help debug issues, or all of the above?","purpose":"Defines the scope of assistance and response format."},{"id":"security_scope","question":"Should the AI provide guidance on PCI compliance, webhook security, and key management?","purpose":"Determines whether security topics are in scope."}],"blueprint":{"version":"${PROMPT_VERSION}","intent":"Create an AI assistant prompt that helps developers integrate Stripe APIs effectively and securely.","audience":"Developers integrating Stripe into applications.","successCriteria":["AI provides accurate, up-to-date Stripe API guidance.","Responses include relevant code examples when appropriate.","Security best practices are emphasized.","Common pitfalls and debugging steps are addressed.","Guidance matches the user's experience level."],"requiredInputs":["Specific Stripe products/features to cover.","Target tech stack and frameworks.","User experience level assumptions.","Scope of AI assistance (code, concepts, debugging).","Security and compliance boundaries."],"domainContext":["Stripe has multiple products with different APIs.","Integration complexity varies by use case.","Security (PCI-DSS, key management) is critical for payment processing."],"constraints":["Must not encourage insecure practices.","Should reference official Stripe documentation.","Avoid outdated API patterns."],"tone":"Helpful, precise, and developer-focused.","risks":["Generic advice that doesn't match user's stack.","Outdated information from old API versions.","Ignoring security considerations."],"outputFormat":"System prompt for an AI assistant with clear scope, capabilities, and example interactions.","evaluationChecklist":["Does the prompt specify which Stripe features to cover?","Is the target tech stack defined?","Are security guardrails included?","Is the AI's role clearly defined?","Are example interactions or few-shots included?"]},"overallConfidence":"Medium readiness – the meta-prompt intent is clear but specific Stripe features and user context are undefined."}`;

// Agentic Workflow Example
const ANALYZER_FEW_SHOT_AGENTIC_USER = `<target_model>google/gemini-2.5-pro</target_model>
<original_prompt>Build an AI agent that can research topics and write reports.</original_prompt>
<extra_context></extra_context>`;

const ANALYZER_FEW_SHOT_AGENTIC_ASSISTANT = `{"analysis":"The prompt describes a multi-step agentic task but lacks tool definitions, research boundaries, report format, and quality controls. This would produce a vague agent incapable of reliable execution.","improvementAreas":["Define available tools (web search, document reading, databases).","Specify research depth and source requirements.","Clarify report structure, length, and citation format.","Establish fact-checking and quality control steps.","Set boundaries on topics and sensitive content."],"questions":[{"id":"available_tools","question":"What tools will the agent have access to (web search, specific databases, document uploaders, APIs)?","purpose":"Determines what research actions are possible and how to orchestrate them."},{"id":"research_depth","question":"How deep should research go (quick summary, comprehensive multi-source analysis, academic-level)?","purpose":"Affects time, token usage, and source requirements."},{"id":"report_format","question":"What format should reports take (executive summary, detailed analysis, bullet points) and what length?","purpose":"Shapes the synthesis and output structure."},{"id":"source_requirements","question":"Are there requirements for source types (primary sources, peer-reviewed, specific domains)?","purpose":"Establishes credibility standards for gathered information."},{"id":"quality_controls","question":"Should the agent fact-check claims, provide confidence levels, or flag uncertain information?","purpose":"Determines reliability mechanisms and output transparency."}],"blueprint":{"version":"${PROMPT_VERSION}","intent":"Design a research-and-report agent with clear capabilities, workflow, and quality standards.","audience":"User or system orchestrating the agent for research tasks.","successCriteria":["Agent can gather information from specified sources.","Research follows defined depth and source requirements.","Reports match specified format and structure.","Sources are cited appropriately.","Quality controls surface uncertainty and verification needs."],"requiredInputs":["List of available tools with capabilities.","Research depth and source type requirements.","Report format, length, and structure.","Citation and attribution format.","Quality control mechanisms."],"domainContext":["Research agents require multi-step reasoning and tool orchestration.","Source quality and recency significantly impact output reliability.","Synthesis must balance comprehensiveness with coherence."],"constraints":["Must cite sources for factual claims.","Should not hallucinate or fabricate information.","Must respect tool rate limits and costs."],"tone":"Thorough, analytical, and well-sourced.","risks":["Hallucination if sources are insufficient.","Scope creep without clear research boundaries.","Poor synthesis if report structure is undefined."],"outputFormat":"Agent system prompt with tool definitions, workflow steps, and output templates.","evaluationChecklist":["Are all available tools clearly defined?","Is the research workflow specified step-by-step?","Is the report format and structure defined?","Are quality controls and fact-checking included?","Are boundaries and limitations stated?"]},"overallConfidence":"Low readiness – critical agent architecture decisions (tools, workflow, quality controls) are missing."}`;

// Documentation Example
const ANALYZER_FEW_SHOT_DOCS_USER = `<target_model>anthropic/claude-3.5-sonnet</target_model>
<original_prompt>Write documentation for our REST API.</original_prompt>
<extra_context></extra_context>`;

const ANALYZER_FEW_SHOT_DOCS_ASSISTANT = `{"analysis":"The prompt requests API documentation but lacks endpoint details, audience specification, format requirements, and example data. This would produce placeholder documentation unusable without significant rework.","improvementAreas":["Provide endpoint list with methods and paths.","Specify target audience (developers, partners, internal team).","Define documentation format (OpenAPI, markdown, hosted docs).","Include example requests/responses and authentication details.","Clarify error handling and rate limiting documentation needs."],"questions":[{"id":"endpoint_details","question":"Can you provide the list of endpoints with their HTTP methods, paths, and brief descriptions?","purpose":"Forms the foundation of the documentation structure."},{"id":"target_audience","question":"Who is the primary audience (external developers, partners, internal team)?","purpose":"Calibrates technical depth and onboarding content."},{"id":"doc_format","question":"What format should the documentation take (OpenAPI/Swagger, markdown, hosted platform like ReadMe)?","purpose":"Determines structure, tooling, and output format."},{"id":"auth_details","question":"How does authentication work (API keys, OAuth, JWT) and what should be documented about it?","purpose":"Authentication is typically the first hurdle for API consumers."},{"id":"example_data","question":"Can you provide example request/response payloads for key endpoints?","purpose":"Concrete examples dramatically improve documentation usability."}],"blueprint":{"version":"${PROMPT_VERSION}","intent":"Create comprehensive, developer-friendly REST API documentation.","audience":"API consumers who need to integrate with the service.","successCriteria":["All endpoints are documented with methods, paths, and descriptions.","Authentication and authorization are clearly explained.","Request/response formats include examples.","Error codes and handling are documented.","Rate limits and usage guidelines are specified."],"requiredInputs":["Complete endpoint list with method and path.","Authentication mechanism details.","Example request/response payloads.","Error code definitions.","Rate limiting and usage policies."],"domainContext":["Good API docs reduce support burden and improve adoption.","Developers expect quick start guides, references, and examples.","Interactive documentation (try-it-out) increases usability."],"constraints":["Must accurately reflect current API behavior.","Should follow industry conventions (OpenAPI if applicable).","Must not expose internal implementation details."],"tone":"Clear, technical, and developer-friendly.","risks":["Incomplete endpoint coverage frustrates developers.","Missing examples lead to integration errors.","Outdated docs are worse than no docs."],"outputFormat":"Structured API documentation with overview, authentication, endpoints, examples, and error reference.","evaluationChecklist":["Are all endpoints documented?","Is authentication clearly explained?","Do endpoints have example requests/responses?","Are error codes and responses documented?","Is there a quick start or getting started section?"]},"overallConfidence":"Low readiness – cannot generate useful documentation without endpoint details and examples."}`;

// Add the new examples to the exported array
export const ANALYZER_FEW_SHOTS_EXTENDED: FewShotPair[] = [
  ...ANALYZER_FEW_SHOTS,
  {
    user: ANALYZER_FEW_SHOT_CODE_USER,
    assistant: ANALYZER_FEW_SHOT_CODE_ASSISTANT,
  },
  {
    user: ANALYZER_FEW_SHOT_API_USER,
    assistant: ANALYZER_FEW_SHOT_API_ASSISTANT,
  },
  {
    user: ANALYZER_FEW_SHOT_AGENTIC_USER,
    assistant: ANALYZER_FEW_SHOT_AGENTIC_ASSISTANT,
  },
  {
    user: ANALYZER_FEW_SHOT_DOCS_USER,
    assistant: ANALYZER_FEW_SHOT_DOCS_ASSISTANT,
  },
];

// =============================================================================
// REFINER FEW-SHOT EXAMPLES
// =============================================================================

const REFINER_FEW_SHOT_CREATIVE_USER = `<target_model>openai/gpt-4o-mini</target_model>
<original_prompt>Create a one-page website for an online learning platform called "EduQuest" with interactive sections, dynamic hero tagline, featured courses, learning paths quiz, testimonials, and a footer with contact modal. Include HTML, embedded CSS, and JavaScript that rotates the hero tagline every 3 seconds.</original_prompt>
<extra_context></extra_context>
<tone>Inspiring and learner-focused</tone>
<output_requirements>Single HTML file with inline CSS/JS, responsive design.</output_requirements>
<blueprint>{"version":"${PROMPT_VERSION}","intent":"Produce a polished, interactive single-page marketing site for EduQuest showcasing courses and engagement features.","audience":"Prospective adult learners balancing work and continuing education.","successCriteria":["Hero section rotates taglines every 3 seconds and links to catalog.","Featured courses highlight subject, instructor, duration, and CTA.","Learning Paths quiz collects goals and preferred learning style, returning a suggested path.","Testimonials feel authentic with names and outcomes.","Footer presents support resources and a contact modal with form."],"requiredInputs":["Brand palette (teal/purple), typography (Poppins, Inter).","Quiz branching logic (3 questions).","Course catalog categories and sample course data.","Testimonials with learner names and outcomes."],"domainContext":["Competitive e-learning market emphasizing flexibility and career growth.","Needs responsive design for desktop, tablet, mobile."],"constraints":["Single HTML document with inline CSS and JavaScript.","Fixed navigation with categories and search bar.","Accessible components with keyboard support."],"tone":"Inspirational, empathetic, confident.","risks":["Quiz may feel superficial if questions lack depth.","Modal could be generic without describing support hours.","Potential performance issues from heavy media assets."],"outputFormat":"Single HTML file with inline CSS/JS.","evaluationChecklist":["Navigation links and search bar function smoothly.","Hero tagline rotates correctly with graceful transitions.","Quiz logic maps answers to learning path recommendations.","Testimonials and course cards display complete, branded copy.","Modal opens/closes accessibly with meaningful fields."]}</blueprint>
<questions_and_answers>{"target_learners":"Working professionals pursuing upskilling or career pivots.","quiz_logic":"Ask about current skill focus (Tech/Business/Creative), preferred learning style (Video/Project/Mixed), and weekly time commitment. Map combinations to curated learning paths.","brand_style":"Use EduQuest teal (#2dd4bf) and deep navy (#0f172a) with clean sans-serif fonts.","modal_content":"Include support hours (24/7 chat), contact form (name, email, message), and CTA to schedule a guidance call."}</questions_and_answers>`;

const REFINER_FEW_SHOT_CREATIVE_ASSISTANT = `{"refinedPrompt":"## Role\\nYou are a front-end engineer designing a single-page marketing site for EduQuest, an online learning platform for working professionals.\\n\\n## Goal\\nDeliver an interactive, responsive HTML page that inspires career-focused adults to enroll in EduQuest courses while collecting leads.\\n\\n## Required Inputs\\n- Brand palette: teal (#2dd4bf) accents with deep navy (#0f172a) backgrounds, typography using Poppins for headings and Inter for body text.\\n- Course data (title, category, instructor, duration, short summary).\\n- Testimonials including learner name, role, and concrete outcome.\\n- Learning Paths quiz logic mapping user answers to recommendation text.\\n- Support contact details (24/7 chat availability, guidance call CTA).\\n\\n## Context / Background\\nEduQuest helps busy professionals reskill through flexible, high-quality online programs. The page must feel modern, trustworthy, and geared toward tangible career outcomes.\\n\\n## Constraints & Guardrails\\n- Produce a single HTML file with inline CSS and JavaScript.\\n- Include a fixed navigation bar with Math, Science, Languages, Arts links plus a functional search input.\\n- Ensure all interactive elements are keyboard-accessible and meet WCAG contrast ratios.\\n- Optimize for fast load (avoid oversized media, lazy-load heavy assets).\\n\\n## Tone & Voice\\nInspirational, empathetic, and confident—highlight growth while remaining credible for professional adults.\\n\\n## Output Format\\nReturn valid HTML5 with <style> in the <head> and <script> before </body>. Comment major sections for maintainability.\\n\\n## Step-by-step Instructions\\n1. Build a hero section with video placeholder background overlay, rotating tagline (\\"Learn at your own pace\\", \\"Discover new passions\\", \\"Expand your horizons\\") cycling every 3 seconds, and a bold \\"Get Started\\" button linking to the course catalog anchor.\\n2. Create a featured courses grid displaying at least four cards with image placeholders, category label, title, instructor, duration, short benefit, and \\"View course\\" CTA.\\n3. Implement a Learning Paths quiz card that asks three questions (skill focus, learning style, weekly commitment) using radio inputs; on submit, display a tailored recommendation message based on combinations.\\n4. Add a Success Stories carousel or stacked testimonials with learner names, roles, and measurable outcomes (promotion, certification, salary increase).\\n5. Configure the footer with links to Blog, FAQ, Privacy Policy, plus a \\"Contact Us\\" button opening an accessible modal containing support blurb, hours (24/7 chat), form fields (name, email, message), and a \\"Schedule a guidance call\\" CTA.\\n6. Wire up JavaScript for tagline rotation, quiz evaluation, modal open/close, and smooth scrolling navigation.\\n7. Apply responsive layout rules for breakpoints at 1024px and 640px; ensure cards stack gracefully on small screens.\\n\\n## Quality Checks\\n- Verify keyboard navigation and focus management for nav, quiz, and modal.\\n- Confirm hero tagline rotation timing and smooth transitions.\\n- Test quiz recommendations for each answer combination.\\n- Validate HTML, CSS, and JS linting with no console errors.\\n- Inspect responsiveness across mobile, tablet, and desktop viewports.","guidance":"Position this prompt before coding to ensure design decisions stay aligned with EduQuest's brand. Adjust color codes, course/testimonial data, or quiz logic as the marketing team supplies updates. Reuse the structure for future landing pages by swapping out brand inputs and success criteria.","changeSummary":["Introduced explicit brand palette, typography, and target persona.","Detailed quiz logic and modal content to remove placeholder ambiguity.","Clarified accessibility, performance, and responsiveness guardrails.","Outlined sequential build steps so the engineer delivers every section."],"assumptions":["Course and testimonial data will be available before implementation.","Video background will use optimized assets to avoid performance issues."],"evaluationCriteria":["Does the final HTML validate and run without console errors?","Are all interactive elements accessible and keyboard-operable?","Do quiz recommendations align with provided mapping logic?","Is the visual styling consistent with the specified palette and typography?","Does the modal convey support info and lead capture as described?"]}`;

const REFINER_FEW_SHOT_ANALYTICAL_USER = `<target_model>anthropic/claude-3.5-sonnet</target_model>
<original_prompt>Summarize Matterport's 2023 10-K in a memo highlighting key financial performance, market trends, and potential risks for the upcoming quarter.</original_prompt>
<extra_context></extra_context>
<tone>Executive, data-backed</tone>
<output_requirements>Two-page memo max, headings with bullet points.</output_requirements>
<blueprint>{"version":"${PROMPT_VERSION}","intent":"Condense Matterport's 2023 10-K into an actionable memo highlighting financial trends and upcoming risks.","audience":"Executive leadership team seeking actionable insights.","successCriteria":["Surface revenue growth/decline metrics and key segment performance.","Call out major strategic initiatives and competitive dynamics.","Highlight forward-looking risks and potential catalysts for the next quarter.","Provide clear recommendations or watch items."],"requiredInputs":["Top-line revenue, net loss, adjusted EBITDA.","Segment performance (digital twins, enterprise vs. SMB).","Major partnerships or product launches.","Risk factors relevant to near-term outlook."],"domainContext":["Leadership reads dozens of memos—needs crisp synthesis rooted in data."],"constraints":["Two-page maximum with headings and bullets.","Call out data sources or filing references when quoting figures."],"tone":"Executive, data-backed, decisive.","risks":["Memo could become verbose without length guardrails.","Recommendations may feel weak without explicit metrics."],"outputFormat":"Structured memo with headings and bullets.","evaluationChecklist":["Does the memo capture core financial metrics with comparisons vs. prior year?","Are market trends and competitive moves contextualized?","Do risks tie to upcoming quarter expectations?","Are recommendations or next steps explicit and actionable?"]}</blueprint>
<questions_and_answers>{"memo_audience":"Executive leadership including CEO, CFO, COO.","focus_areas":"Emphasize revenue trend, operating expenses, enterprise adoption, and real estate market impacts.","format_preferences":"Begin with Executive Summary, then Financial Performance, Market Trends & Competitive Landscape, Risks & Watch Items, and Recommended Actions.","risk_horizon":"Prioritize near-term (next quarter) indicators with note on medium-term catalysts."}</questions_and_answers>`;

const REFINER_FEW_SHOT_ANALYTICAL_ASSISTANT = `{"refinedPrompt":"## Role\\nYou are an equity research analyst preparing an executive-ready memo on Matterport's FY2023 10-K for leadership review.\\n\\n## Goal\\nDeliver a two-page (max) memo that surfaces FY2023 performance, next-quarter risks, and recommended leadership actions.\\n\\n## Required Inputs\\n- FY2023 revenue, YoY growth, GAAP net loss, adjusted EBITDA.\\n- Breakdown of enterprise vs. SMB adoption and digital twin platform metrics.\\n- Major partnerships, product releases, or go-to-market shifts.\\n- Risk factors impacting the next quarter (e.g., real estate market softness, churn).\\n- Prior-year comparatives where available.\\n\\n## Context / Background\\nMatterport provides 3D digital twin technology. Leadership needs a concise snapshot to monitor momentum, assess market positioning, and align resources for the upcoming quarter.\\n\\n## Constraints & Guardrails\\n- Memo must fit within two pages (~800-900 words).\\n- Use the following structure: Executive Summary; Financial Performance; Market Trends & Competitive Landscape; Risks & Watch Items; Recommended Actions.\\n- Embed bullet points under each section for scanability.\\n- Cite figures with references (e.g., \\"FY2023 revenue up 15% YoY, p.42\\").\\n\\n## Tone & Voice\\nExecutive, data-backed, and decisive. Favor crisp phrasing over narrative detail.\\n\\n## Output Format\\nReturn plain text memo adhering to the required sections and bullet formatting. Separate sections with clear headings in all caps or bold.\\n\\n## Step-by-step Instructions\\n1. Draft a 4-5 sentence Executive Summary covering topline growth, profitability trajectory, and overarching narrative.\\n2. Summarize Financial Performance with bullets on revenue, expenses, margins, cash position, and segment detail (enterprise vs. SMB).\\n3. Outline Market Trends & Competitive Landscape describing demand drivers, industry headwinds/tailwinds, and strategic initiatives (partnerships, product launches).\\n4. Detail Risks & Watch Items focused on next-quarter impacts (real estate trends, budget cycles, churn). Add medium-term catalysts in a separate bullet if material.\\n5. Provide 3-4 Recommended Actions leadership should consider (e.g., reinforce enterprise pipeline, adjust cost controls, invest in product features).\\n6. Close with a short reminder of data sources and suggest follow-up analysis if gaps remain.\\n\\n## Quality Checks\\n- Does the memo respect the two-page limit and specified structure?\\n- Are all financial metrics supported with figures and comparisons?\\n- Do risks align with near-term outlook while acknowledging mid-term catalysts?\\n- Are recommendations actionable and prioritized?\\n- Is the tone consistent with executive expectations?","guidance":"Before drafting, gather the specified financial metrics and segment data. Update references if you pull from amended filings. Reuse this template for future filings by swapping company-specific metrics and risks.","changeSummary":["Locked in leadership-focused structure with required sections.","Anchored tone, length, and citation expectations for executive readership.","Specified financial metrics, segment details, and risk horizon to cover.","Outlined actionable recommendations section to ensure next steps."],"assumptions":["Detailed FY2023 metrics and page references are accessible to the analyst.","Leadership is comfortable with bullet-style memo presentation."],"evaluationCriteria":["Does the final memo stay within two-page guidance?","Are key financial and segment metrics highlighted with YoY context?","Do risk bullets focus on the upcoming quarter with evidence?","Are recommended actions concrete and relevant for leadership?","Is sourcing/citation handled per expectations?"]}`;

const REFINER_FEW_SHOT_CRASH_USER = `<target_model>openai/gpt-4o-mini</target_model>
<original_prompt>My app crashes when I click the submit button.</original_prompt>
<extra_context></extra_context>
<tone>Professional and concise</tone>
<output_requirements>Provide a structured crash report template.</output_requirements>
<blueprint>{"version":"${PROMPT_VERSION}","intent":"Produce a thorough crash report that enables engineers to reproduce and debug the submit-button failure.","audience":"Support engineers or developers responsible for fixing the application crash.","successCriteria":["Describe the application type and version in detail.","List precise reproduction steps and whether the crash is consistent.","Include exact error messages, codes, or log snippets.","Specify environment details (OS, browser/device, versions).","Note inputs submitted and any recent changes or troubleshooting."],"requiredInputs":["Application/platform description and version.","Step-by-step reproduction sequence including input data.","Visible error messages, codes, or logs.","Environment specs (OS, device, browser).","Timeline and recent updates that may correlate."],"domainContext":["Crash reports typically follow structured debugging templates.","Useful diagnostics include logs, stack traces, and reproduction info."],"constraints":["Remain concise yet complete; avoid speculation.","Structure content so engineers can skim for key diagnostics."],"tone":"Calm, factual, and solution-focused.","risks":["Without environment or error data, engineers cannot reproduce the crash.","Missing recent-change context may hide the root cause."],"outputFormat":"Structured crash troubleshooting request with sections for summary, environment, reproduction, diagnostics, and attempted fixes.","evaluationChecklist":["Does the report specify platform, version, and environment?","Are reproduction steps and inputs clearly described?","Are error messages or logs captured verbatim?","Does it note when the issue began and any changes made?","Are attempted troubleshooting steps listed?"]}</blueprint>
<questions_and_answers>{"application_type":"Web application accessed via Chrome.","error_behavior":"The browser tab displays a white screen, then reloads the app.","error_message":"Console shows the JavaScript TypeError: Cannot read properties of undefined (reading 'id') at submitHandler.js:42.","repro_steps":"Yes—fill out the checkout form with any data and click Submit; it happens every time.","environment_details":"Windows 11 Pro, Chrome 119.0.6045.160 on Dell XPS 15.","recent_changes":"Issue started today right after deploying v2.3 which included a new recommendations widget."}</questions_and_answers>`;

const REFINER_FEW_SHOT_CRASH_ASSISTANT = `{"refinedPrompt":"## Role\\nYou are reporting a critical crash to the engineering support team for immediate triage.\\n\\n## Goal\\nProvide engineers with the diagnostic detail they need to reproduce and debug the submit-button crash.\\n\\n## Required Inputs\\n- Application: Checkout web app, version 2.3 deployed today with new recommendations widget.\\n- Platform: Web (Chrome 119.0.6045.160) on Windows 11 Pro, Dell XPS 15.\\n- User profile: Logged-in customer submitting checkout form.\\n- Form payload: Standard checkout data (name, shipping, payment).\\n\\n## Context / Background\\nCrash began immediately after deploying v2.3 containing the recommendations widget. Prior versions did not exhibit this issue.\\n\\n## Constraints & Guardrails\\n- Stick to observed facts; avoid speculation.\\n- Include console error details verbatim.\\n- Note any security/privacy considerations when sharing logs.\\n\\n## Tone & Voice\\nProfessional, concise, diagnostic.\\n\\n## Output Format\\nReturn a structured incident report with the following sections.\\n\\n## Step-by-step Instructions\\n1. **Summary**: One sentence stating that the checkout web app crashes (white screen then reload) whenever the Submit button is clicked.\\n2. **Environment**: List OS, browser (with version), device, and app build/version.\\n3. **Reproduction Steps**: Provide numbered steps from opening checkout to clicking Submit; confirm 100% reproducible.\\n4. **Expected vs Actual**: Expected = proceed to order confirmation; Actual = white screen then reload with console error.\\n5. **Diagnostics**: Paste console error \\"TypeError: Cannot read properties of undefined (reading 'id')\\" at submitHandler.js:42. Mention whether network failures or server errors appear.\\n6. **Inputs Submitted**: Note that any standard checkout data triggers the issue (specify fields if relevant).\\n7. **Timeline & Recent Changes**: State crash began after v2.3 deploy introducing the recommendations widget.\\n8. **Attempted Troubleshooting**: Document that cache clearing/reloading does not resolve; no other steps taken yet.\\n9. **Impact**: Highlight that checkout flow is blocked for all users; classify severity as critical.\\n10. **Attachments**: Request inclusion of screenshots, HAR file, and reproduction video if available.\\n\\n## Quality Checks\\n- All sections are present and clearly labeled.\\n- Console error and file reference are quoted exactly.\\n- Reproduction steps are precise and repeatable.\\n- Timeline references the deployment change introducing the regression.\\n- Impact statement communicates business urgency.","guidance":"Attach console logs, network traces, and a short screen recording to accelerate investigation. If safe, restore the previous version to mitigate impact while fixes are developed.","changeSummary":["Structured the incident into summary, environment, reproduction, diagnostics, and impact.","Embedded verbatim console error to target submitHandler.js:42.","Connected start time with v2.3 deployment to highlight regression.","Flagged severity and immediate business impact to prioritize response."],"assumptions":["Developers have access to submitHandler.js and deployment logs.","No additional authentication or account context is required to reproduce."],"evaluationCriteria":["Do engineers understand platform, build, and reproduction steps?","Is the exact error captured for debugging?","Are recent changes and impact clearly connected?","Does the report avoid speculation and focus on evidence?","Are next diagnostic artifacts (screenshots, HAR) requested?"]}`;

const REFINER_FEW_SHOT_EXCEL_USER = `<target_model>openai/gpt-4o-mini</target_model>
<original_prompt>Write Python code to automate Excel.</original_prompt>
<extra_context></extra_context>
<tone>Clear and instructional</tone>
<output_requirements>Provide a detailed automation spec for the developer.</output_requirements>
<blueprint>{"version":"${PROMPT_VERSION}","intent":"Define a concrete Excel automation specification covering tasks, structure, logic, and technical constraints.","audience":"Python automation developer building the Excel workflow.","successCriteria":["List the exact operations and triggers for automation.","Describe workbook layout, sheets, and key columns.","Detail input sources and desired outputs.","Capture formulas, aggregations, and validation rules.","Outline execution cadence and environment details."],"requiredInputs":["Excel task list with priorities.","Workbook schema (sheet names, column descriptions).","Business logic and formula requirements.","Input and output data formats.","Runtime details (Python version, libraries, scheduling)."],"domainContext":["Excel automation often uses pandas, openpyxl, or xlwings.","Reliable scripts require precise schema knowledge."],"constraints":["Specify if formatting and formulas must be preserved.","Note performance considerations for large datasets."],"tone":"Professional, thorough, and implementation-ready.","risks":["Ambiguity can lead to scripts that miss required transformations.","Ignoring environment constraints may produce unusable code."],"outputFormat":"Detailed automation brief with sections for objectives, inputs, logic, outputs, environment, and testing.","evaluationChecklist":["Are all target Excel operations described?","Is workbook structure and data schema documented?","Does the brief outline calculations and validation rules?","Are output deliverables and formats clear?","Does it note environment and scheduling constraints?"]}</blueprint>
<questions_and_answers>{"excel_tasks":"Monthly, combine sales CSV files into a master workbook, clean data, calculate KPIs, and generate charts.","workbook_structure":"Master workbook 'Monthly_Sales_Report.xlsx' with sheets Raw_Data, Clean_Data, KPIs, Charts. Raw data has columns: order_id, region, product, units_sold, revenue, sale_date.","input_source":"Weekly CSV exports dropped in /data/sales/YYYY-MM-DD.csv.","output_expectations":"Updated Excel workbook with cleaned data, pivot-style KPI table, and refreshed bar/line charts saved to the Charts sheet.","business_logic":"Normalize region names, convert sale_date to date, calculate total revenue and units per region/product, calculate month-over-month growth, flag orders with negative revenue.","environment_constraints":"Python 3.10 on Windows Server, prefer pandas and openpyxl. Scheduled to run via Windows Task Scheduler on the 1st of each month."}</questions_and_answers>`;

const REFINER_FEW_SHOT_EXCEL_ASSISTANT = `{"refinedPrompt":"## Role\\nYou are a Python automation engineer tasked with building a monthly Excel reporting pipeline for the analytics team.\\n\\n## Goal\\nAutomate ingestion of weekly sales CSV files, cleanse data, compute KPIs, and update a master Excel report with refreshed charts.\\n\\n## Required Inputs\\n- Source directory: /data/sales/ containing weekly CSV exports (order_id, region, product, units_sold, revenue, sale_date).\\n- Master workbook: Monthly_Sales_Report.xlsx with sheets Raw_Data, Clean_Data, KPIs, Charts.\\n- Region normalization mapping (provide dictionary in config).\\n- Prior-month benchmark data for month-over-month calculations.\\n\\n## Context / Background\\nCurrently, analysts manually consolidate weekly exports into the master workbook. Automation should produce the month-end report on the 1st of each month.\\n\\n## Constraints & Guardrails\\n- Python 3.10 environment on Windows Server with pandas and openpyxl available.\\n- Preserve Charts sheet layout while refreshing underlying data references.\\n- Script must handle up to 100k rows per month.\\n\\n## Tone & Voice\\nPrecise, instructional, implementation-ready.\\n\\n## Output Format\\nProvide a step-wise build plan followed by acceptance criteria.\\n\\n## Step-by-step Instructions\\n1. **Ingestion**: Enumerate CSV files for the month, load via pandas, enforce schema (data types, required columns).\\n2. **Normalization**: Trim whitespace, standardize region names using mapping, convert sale_date to pandas datetime, enforce positive numeric types.\\n3. **Combine & Clean**: Concatenate files, drop duplicates, log anomalies (negative revenue, missing fields) to a report.\\n4. **Write Raw_Data**: Overwrite Raw_Data sheet with cleaned monthly dataset; retain headers and autofit columns.\\n5. **KPIs Calculation**: Group by region/product to compute total revenue, total units_sold, average order value, and month-over-month growth against prior month data. Write results to KPIs sheet sorted by revenue descending.\\n6. **Charts Refresh**: Update data ranges for existing charts on Charts sheet (use openpyxl to adjust series references). If ranges shift, regenerate bar chart (revenue by region) and line chart (month-over-month growth) while preserving formatting.\\n7. **Metadata & Logging**: Add run metadata (timestamp, file count, anomalies) to KPIs sheet footer; create logs directory storing monthly run log with counts and errors.\\n8. **Scheduling**: Package script as entry point \`python automate_report.py --month YYYY-MM\` for Task Scheduler. Document required environment variables (e.g., REGION_MAP_PATH).\\n\\n## Quality Checks\\n- All source CSVs processed exactly once; missing files trigger warnings.\\n- Data types validated; anomalies logged and surfaced in summary.\\n- KPIs sheet totals cross-check with manual spot calculations.\\n- Charts display updated month data and remain linked to new ranges.\\n- Workbook saves without corrupting existing formatting or formulas.","guidance":"Version-control the script, capture configuration (paths, region mapping) via environment variables, and add integration tests using sample CSVs to verify KPI outputs. Consider incremental weekly automation if the workload grows.","changeSummary":["Clarified exact automation scope: ingest CSVs, clean data, compute KPIs, refresh charts.","Documented workbook structure and sheet responsibilities.","Established logging, scheduling, and performance guardrails.","Outlined detailed step sequence to build and validate the pipeline."],"assumptions":["Past monthly benchmarks are available to compute growth metrics.","Region normalization mapping will be maintained externally."],"evaluationCriteria":["Does the plan specify ingestion, cleaning, KPI computation, and chart refresh steps?","Are workbook sheets updated with correct data and formatting?","Are anomalies logged and surfaced to analysts?","Is scheduling/runtime environment fully described?","Are performance and data-volume considerations addressed?"]}`;

const REFINER_FEW_SHOT_SQL_USER = `<target_model>openai/gpt-4o-mini</target_model>
<original_prompt>Write a SQL query to analyze sales performance.</original_prompt>
<extra_context></extra_context>
<tone>Analytical and executive-ready</tone>
<output_requirements>Deliver a SQL requirements brief before coding.</output_requirements>
<blueprint>{"version":"${PROMPT_VERSION}","intent":"Produce a detailed SQL analytics brief that defines metrics, schema, filters, and output expectations.","audience":"Data analyst or engineer tasked with writing the SQL query.","successCriteria":["List primary KPIs and questions driving the analysis.","Document schema with table/column names and joins.","Define time filters, comparisons, and aggregation levels.","Specify grouping dimensions and sort preferences.","Capture SQL dialect and performance considerations."],"requiredInputs":["Business questions or KPIs to calculate.","Database schema details and join keys.","Time range and any comparison windows.","Required grouping and ordering preferences.","Filtering rules and data quality constraints."],"domainContext":["Sales analytics often requires joins between orders, customers, products, and regions.","Different SQL dialects require tailored syntax for dates and analytics functions."],"constraints":["Clarify acceptable run time and indexing expectations.","Indicate if intermediate tables or CTEs are allowed."],"tone":"Analytical, structured, and precise.","risks":["Ambiguous metrics lead to incorrect aggregations.","Schema gaps can produce invalid SQL or runtime errors."],"outputFormat":"SQL requirements document with sections for objectives, schema, filters, computations, output columns, and optimization notes.","evaluationChecklist":["Does it specify KPIs and business questions?","Are tables, joins, and key columns listed?","Is the analysis time frame clearly defined?","Are grouping and ordering directions included?","Is the SQL dialect or engine named?"]}</blueprint>
<questions_and_answers>{"analysis_goal":"Identify top-performing products and regions by revenue and year-over-year growth for the last two quarters.","schema_details":"orders(order_id, customer_id, product_id, order_date, status, revenue, quantity); products(product_id, product_name, category); regions(customer_id, region_name).","time_scope":"Compare Q2 2024 vs Q2 2023 and report year-over-year change.","grouping_dimensions":"Group by region_name and product_name; include category for context.","filters":"Use orders with status = 'completed'; exclude any orders with revenue <= 0.","sql_dialect":"PostgreSQL 14."}</questions_and_answers>`;

const REFINER_FEW_SHOT_SQL_ASSISTANT = `{"refinedPrompt":"## Role\\nYou are a data analyst preparing requirements for a PostgreSQL sales performance query.\\n\\n## Goal\\nDeliver a SQL requirements brief that captures schema, metrics, filters, and grouping needed to analyze product and regional performance year-over-year.\\n\\n## Required Inputs\\n- Tables: orders(order_id, customer_id, product_id, order_date, status, revenue, quantity); products(product_id, product_name, category); regions(customer_id, region_name).\\n- Time frame: Q2 2024 compared to Q2 2023.\\n- Only completed orders with revenue > 0.\\n\\n## Context / Background\\nLeadership wants visibility into which product-region combinations drove growth this quarter versus the same quarter last year.\\n\\n## Constraints & Guardrails\\n- PostgreSQL 14 syntax (window functions and CTEs allowed).\\n- Query should complete within acceptable time for ~5M orders; indexes on orders(order_date, status) and regions(customer_id) are available.\\n\\n## Tone & Voice\\nStructured, precise, and data-focused.\\n\\n## Output Format\\nProvide a numbered requirements brief; conclude with validation steps.\\n\\n## Step-by-step Instructions\\n1. **Business Objectives**: State that the query must compute total revenue, quantity, and year-over-year growth for each region_name + product_name pair, grouped by product category.\\n2. **Schema & Joins**: Document joins orders -> products via product_id and orders -> regions via customer_id. Note that orders.status must equal 'completed'.\\n3. **Time Filters**: Define Q2 2024 as order_date between 2024-04-01 and 2024-06-30; Q2 2023 similarly. Mention using CASE expressions or CTEs to separate periods.\\n4. **Metrics**: Specify calculations: current_revenue, prior_revenue, revenue_yoy_pct, current_quantity, prior_quantity. Include safeguards to avoid division by zero.\\n5. **Grouping & Sorting**: Describe grouping by region_name, product_name, products.category with ordering by revenue_yoy_pct DESC and optional limit to top 20 rows.\\n6. **Filters**: Enforce revenue > 0 and status = 'completed'; note optional threshold for minimum quantity.\\n7. **Output Columns**: List required columns (region_name, product_name, category, current_revenue, prior_revenue, revenue_yoy_pct, current_quantity, prior_quantity).\\n8. **Performance Notes**: Recommend using existing indexes, consider materialized CTE for filtered orders, and review EXPLAIN ANALYZE if execution exceeds 500 ms.\\n9. **Validation Steps**: Outline checks comparing totals vs finance reports, verifying year-over-year calculations on sampled products, and ensuring no null regions/products appear.\\n\\n## Quality Checks\\n- Requirements cover objectives, schema, metrics, filters, and ordering.\\n- Time windows and year-over-year calculations are unambiguous.\\n- Output column definitions match leadership needs.\\n- Performance and validation guidance are included.\\n- PostgreSQL-specific considerations are addressed.","guidance":"After drafting SQL, run EXPLAIN ANALYZE to confirm index usage and ensure year-over-year calculations match finance benchmarks. Consider a materialized view if leadership wants recurring access.","changeSummary":["Captured business goals, schema, and join relationships explicitly.","Defined exact time ranges and year-over-year metrics for Q2 comparison.","Clarified grouping, ordering, and output columns for leadership review.","Provided performance and validation guidance tailored to PostgreSQL."],"assumptions":["Orders table contains all necessary revenue/quantity fields without additional adjustments.","Region mapping via the regions table is complete for relevant customers."],"evaluationCriteria":["Does the brief enable an analyst to write SQL without extra clarification?","Are KPIs, schema, and filters clearly articulated?","Is the time comparison window explicit?","Do performance notes align with dataset scale?","Are validation steps provided to confirm accuracy?"]}`;

export const REFINER_FEW_SHOTS: FewShotPair[] = [
  {
    user: REFINER_FEW_SHOT_CREATIVE_USER,
    assistant: REFINER_FEW_SHOT_CREATIVE_ASSISTANT,
  },
  {
    user: REFINER_FEW_SHOT_ANALYTICAL_USER,
    assistant: REFINER_FEW_SHOT_ANALYTICAL_ASSISTANT,
  },
  {
    user: REFINER_FEW_SHOT_CRASH_USER,
    assistant: REFINER_FEW_SHOT_CRASH_ASSISTANT,
  },
  {
    user: REFINER_FEW_SHOT_EXCEL_USER,
    assistant: REFINER_FEW_SHOT_EXCEL_ASSISTANT,
  },
  {
    user: REFINER_FEW_SHOT_SQL_USER,
    assistant: REFINER_FEW_SHOT_SQL_ASSISTANT,
  },
];
