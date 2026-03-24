# PromptTriage

<div align="center">

![RAG Pipeline](https://img.shields.io/badge/RAG-Pinecone_Pipeline-FF6B6B?style=for-the-badge&logo=database)
![Multi-Modal](https://img.shields.io/badge/Multi--Modal-Text_|_Image_|_Video-9B59B6?style=for-the-badge)
![Vectors](https://img.shields.io/badge/Vectors-28K+-00D4AA?style=for-the-badge&logo=pinecone)
![MCP Tools](https://img.shields.io/badge/MCP-Context7_Integrated-3498DB?style=for-the-badge)
![Fine-Tuning](https://img.shields.io/badge/Fine--Tuning-Dataset_Ready-F39C12?style=for-the-badge)

![Next.js](https://img.shields.io/badge/Next.js-15.1.6-black?style=flat-square&logo=next.js)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?style=flat-square&logo=typescript)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat-square&logo=fastapi)
![Pinecone](https://img.shields.io/badge/Pinecone-Vector_DB-000?style=flat-square)

**A RAG-powered prompt engineering platform with modality-specific optimization for Text, Image, Video, and System Prompts**

*System prompts are generated referencing frontier LLM providers (Claude, Cursor, v0, Gemini CLI)*

[![Live](https://img.shields.io/badge/🚀_Live-prompttriage.kaelux.dev-00D4AA?style=for-the-badge)](https://prompttriage.kaelux.dev)

[Try it Live](https://prompttriage.kaelux.dev) • [Features](#-features) • [System Design](#-system-design-philosophy) • [Architecture](#-architecture) • [Technologies](#-technologies) • [Contributing](CONTRIBUTING.md) • [Security](SECURITY.md)

</div>

---

## 🎯 Overview

**PromptTriage** is an enterprise-grade prompt engineering platform that transforms rough ideas into production-ready AI prompts through **RAG-powered retrieval** and **modality-specific optimization**. 

The platform excels at **system prompt generation** by referencing a curated corpus of frontier LLM system prompts from Claude Code, Cursor, v0, Windsurf, and Gemini CLI—ensuring your prompts follow proven patterns from industry leaders.

### What Sets PromptTriage Apart

- **Pinecone RAG Architecture**: 28K+ vectors for fast semantic retrieval of similar high-quality prompts
- **Modality-Specific Prompts**: Dedicated metaprompts for Text, Image, Video, and System Prompt generation—each optimized for their domain
- **MCP Tool Integration**: Context7 integration provides live documentation lookup for current library APIs
- **Fine-Tuning Ready**: Curated datasets prepared for Unsloth QLoRA and custom model fine-tuning

## 🔬 Backed by 28K+ Scale Research

PromptTriage isn't just a wrapper—it's built on our proprietary empirical research. We analyzed **28,000 production system prompts** to extract what actually drives frontier model reasoning:

- **The 50-Word Rule (Study E):** Short prompts (<50 words, 80.1/100) consistently outperform long, bloated prompts (>300 words, 66.9/100). PromptTriage structures instructions into ruthless, boundary-focused directives.
- **The Format Scaffold (Study E):** Forcing models into JSON or YAML schemas acts as a cognitive scaffold, mathematically improving reasoning quality over plain text output.
- **The "Expert" Trap (Study C):** 80% of production prompts start with "Act as an expert." Our data proves this provides zero performance lift. PromptTriage strips out emotional appeals and persona bloat in favor of hard, negative constraints.

---

## ✨ Features

### 🔍 **Intelligent Prompt Analysis**
- **Deep Context Understanding**: Gemini analyzes your initial prompt to identify gaps, ambiguities, and missing context
- **Risk Assessment**: Automatically detects potential issues, biases, and edge cases in your prompt design
- **Structured Blueprint Generation**: Creates a comprehensive blueprint with intent, audience, success criteria, constraints, and evaluation checklists

### ❓ **Dynamic Question Generation**
- **Context-Aware Questions**: Generates 2-5 custom follow-up questions based on detected gaps
- **Adaptive Intelligence**: Questions evolve based on the target AI model, tone, and output requirements
- **Efficient Information Gathering**: Streamlined workflow to capture all necessary details

### 🛠️ **AI-Ready Prompt Generation**
- **Multi-Model Support**: Optimized prompts for OpenAI GPT, Claude (Sonnet/Opus/Haiku), Gemini (Pro/Flash), Grok, and Mistral
- **Structured Output**: Generates markdown-formatted prompts with nine comprehensive sections
- **Quality Guardrails**: Includes assumptions, change summaries, and evaluation criteria for response validation

### 🧠 **Advanced RAG Architecture**
- **Pinecone Vector Store**: 28K+ embeddings for fast semantic retrieval
- **Smart Retrieval**: Uses Google's `gemini-embedding-001` model (768d) to search across **28,000+** verified prompts
- **System Prompts Corpus**: Curated library of **79+ system prompts** from frontier models (Claude Code, Cursor, v0, Gemini CLI), professionally categorized and labeled
- **Modality Routing**: Automatic namespace selection based on prompt type (text → `system-prompts`, image → `image-prompts`, video → `video-prompts`)

### 🎨 **Modality-Specific Engineering**
- **Unified Interface**: Seamlessly switch between **Text**, **Image**, and **Video** generation modes.
- **Context-Aware Refinement**: 
  - *Text*: Focuses on system instructions, tone, and structure.
  - *Image*: Optimizes for negative prompts, aspect ratios, and style descriptors.
  - *Video*: Enhances temporal consistency, camera motion, and duration parameters.

### 🛠️ **Precision Control**
- **Output Format Selector**: Force outputs into JSON, XML, Markdown, or tabular formats
- **Desired Output Specification**: Tell the AI what format your *target model* should respond in
- **Thinking Mode**: Enable deep analysis with extended reasoning for complex prompts
- **Fast Mode (Non-Thinking)**: Powered by `TriageAgent 14B` (our fine-tuned Qwen 3.0 14B model) for rapid iteration

### 🔌 **MCP Tool Integration**
- **Context7**: Live documentation lookup for current library APIs (Next.js 15, React 19, LangChain, etc.)
- **Firecrawl** *(Optional)*: Web search to enrich prompts with real-world context when needed

### 🔄 **Iterative Refinement**
- **One-Click Rewrite**: Generate alternative refinements without re-answering questions
- **Metaprompt-Driven Consistency**: Curated system prompts guide Gemini to maintain quality across generations

## 🏗️ System Design Philosophy

**PromptTriage is built on RAG-powered retrieval and modality-specific optimization, not just API wrappers.**

### Core Design Principles

#### 1. **RAG-First Retrieval**
Before generating any prompt, the system queries a curated vector store to find similar high-quality prompts:
- **Semantic Search**: Pinecone vector store with 28K+ embeddings finds the most relevant reference prompts
- **Modality Routing**: Queries automatically route to the correct namespace (`system-prompts`, `video-prompts`, `image-prompts`)
- **Frontier Model References**: System prompt generation draws from Claude Code, Cursor, v0, Windsurf, and Gemini CLI patterns

#### 2. **9 Modality-Specific Metaprompts**
Each modality has dedicated analyzer, fast mode, and refiner prompts:
- **Text/System**: Focuses on role definition, guardrails, and multi-turn behavior
- **Image**: Optimizes for composition, style keywords, and negative prompts
- **Video**: Enhances camera motion, temporal consistency, and duration compliance
- **Versioned Prompts**: Current version `2025-01-systemprompts-enhanced` for reproducibility

#### 3. **Reference Examples (Few-Shot)**
Curated examples provide format consistency alongside RAG retrieval:
- Domain examples (creative, analytical, technical) demonstrate target output structure
- Examples work *with* RAG context, not as the primary source of prompt patterns

#### 4. **Blueprint-Based Orchestration**
The system uses a two-phase orchestration design with structured blueprints:

**Phase 1 - Analysis**:
- Extracts intent, audience, success criteria, constraints, risks
- Generates targeted follow-up questions (2-5 questions)
- Creates a structured blueprint with 10+ fields for later synthesis
- Validates completeness through confidence scoring

**Phase 2 - Refinement**:
- Reconciles the original prompt with blueprint, RAG context, and user answers
- Synthesizes a production-ready prompt with 9 standardized sections
- Generates usage guidance, change summaries, assumptions, and evaluation criteria

#### 5. **MCP Tool Augmentation**
The platform integrates with MCP tools for real-time context:
- **Context7**: Fetches current library documentation during prompt generation
- **Firecrawl**: Optional web search for additional context enrichment

### 🔐 **Enterprise Security**
- **Google OAuth 2.0**: Secure authentication with Google Sign-In
- **NextAuth.js Integration**: Session management and authentication flows
- **Environment-based Configuration**: Secure API key management

### 📊 **Developer Experience**
- **TypeScript-First**: Full type safety across the application
- **Modern Tooling**: ESLint, Turbopack, and PostCSS for optimal development
- **Responsive Design**: Tailwind CSS-powered UI that works on all devices

## 🏗️ Architecture

### System Design Overview

```
┌─────────────────┐
│   User Input    │
│  (Rough Idea)   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                     Analyzer API                             │
│                     /api/analyze                             │
│                                                              │
│  ┌──────────────────┐    ┌──────────────────────────────┐  │
│  │ Modality Router  │───▶│ RAG Service (FastAPI)         │  │
│  │ Text/Image/Video │    │ ┌─────────────────────────┐  │  │
│  └──────────────────┘    │ │  Pinecone (28K+ Vecs)   │  │  │
│           │              │ └─────────────────────────┘  │  │
│           ▼              └──────────────────────────────┘  │
│  ┌──────────────────┐                                       │
│  │ Metaprompt       │◄────── 9 Modality-Specific Prompts   │
│  │ (v2025-01)       │        + RAG Context                 │
│  └──────────────────┘    ┌──────────────────────────────┐  │
│           │              │ MCP Tools                      │  │
│           ▼              │ • Context7 MCP → Live Docs     │  │
│  ┌──────────────────┐    │ • Firecrawl → Web Search       │  │
│  │ AI Generation     │    └──────────────────────────────┘  │
│  └──────────────────┘                                       │
│           │                                                  │
│  • Blueprint Generation                                      │
│  • Follow-up Questions                                       │
└───────────┬─────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────┐
│  User Answers   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                     Refiner API                              │
│                     /api/refine                              │
│                                                              │
│  ┌──────────────────┐    ┌──────────────────────────────┐  │
│  │ Modality-Specific │    │ Blueprint + RAG Context      │  │
│  │ Refiner Prompt    │───▶│ + User Answers               │  │
│  └──────────────────┘    └──────────────────────────────┘  │
│           │                                                  │
│           ▼                                                  │
│  • Production-Ready Prompt                                   │
│  • Negative Prompts (Image/Video)                           │
│  • Evaluation Criteria                                       │
└───────────┬─────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────┐
│  Final Prompt   │
│  (AI-Ready)     │
└─────────────────┘
```

### Key Components

#### Frontend Layer (`promptrefiner-ui/src/`)
- **`app/page.tsx`**: Main UI with modality selection and form orchestration
- **`components/`**: ModalitySelector, OutputFormatSelector, DesiredOutputSelector, ImageUploader, ErrorFeedback, PipelineProgress
- **`services/`**: RAG client, Context7 MCP integration, Firecrawl client
- **`lib/`**: PipelineLogger (structured agentic logging)

#### API Layer (`src/app/api/`)
- **`analyze/route.ts`**: Prompt analysis with modality routing and RAG context
- **`refine/route.ts`**: Prompt refinement with modality-specific system prompts

#### Backend Layer (`backend/`)
- **`app/routers/rag.py`**: RAG endpoints with Pinecone retrieval
- **`app/services/rag.py`**: RAG service with modality-based namespace routing
- **`scripts/`**: Dataset ingestion and labeling pipelines

#### **Prompt Engineering Core (`src/prompts/`)**
- **`metaprompt.ts`**: 9 modality-specific system prompts
  - `ANALYZER_SYSTEM_PROMPT` / `FAST_MODE_SYSTEM_PROMPT` / `REFINER_SYSTEM_PROMPT` (Text)
  - `IMAGE_ANALYZER_SYSTEM_PROMPT` / `IMAGE_FAST_MODE_SYSTEM_PROMPT` / `IMAGE_REFINER_SYSTEM_PROMPT`
  - `VIDEO_ANALYZER_SYSTEM_PROMPT` / `VIDEO_FAST_MODE_SYSTEM_PROMPT` / `VIDEO_REFINER_SYSTEM_PROMPT`
  - `SYSTEM_PROMPT_ANALYZER` / `SYSTEM_PROMPT_FAST_MODE` / `SYSTEM_PROMPT_REFINER`
- **Version Control**: `PROMPT_VERSION = "2025-01-systemprompts-enhanced"`

## 🛠️ Technologies

### Frontend
- **[Next.js 15.1.6](https://nextjs.org/)**: React framework with App Router
- **[React 19.0.0](https://react.dev/)**: UI component library
- **[TypeScript 5](https://www.typescriptlang.org/)**: Type-safe development
- **[Tailwind CSS 3.4](https://tailwindcss.com/)**: Utility-first styling

### Backend
- **[FastAPI](https://fastapi.tiangolo.com/)**: Python backend for RAG services
- **[Pinecone](https://www.pinecone.io/)**: Vector database (28K+ embeddings)

### AI & RAG
- **Thinking Mode**: Deep reasoning powered by `gemini-3.1-pro`
- **Fast Mode**: Standard generation powered by our fine-tuned `TriageAgent 14B` (Qwen 3.0 14B)
- **Advanced Configuration**: Corrective RAG (CRAG) architecture with Brave Search fallback
- **Retrieval Engine**: `GTE-ModernBERT` embeddings for state-of-the-art vector similarity across 28K+ vectors
- **9 Modality Metaprompts**: Text, Image, Video, System Prompt specializations

### MCP Tools
- **Context7**: Live library documentation lookup
- **Firecrawl** *(Optional)*: Web search for context enrichment

### Auth & Infrastructure
- **[NextAuth.js 4.24](https://next-auth.js.org/)**: Google OAuth 2.0 authentication
- **Node.js 20+**: JavaScript runtime
- **Python 3.9+**: Backend runtime

## 📈 Use Cases

- **AI Product Development**: Generate production-ready prompts for AI features
- **Content Creation**: Craft precise prompts for copywriting, marketing, and creative work
- **Data Analysis**: Structure prompts for analytical tasks and reporting
- **Research**: Formulate clear research questions and analysis frameworks
- **Education**: Teach effective prompt engineering techniques
- **Automation**: Create consistent, reusable prompt templates

## 🔄 Workflow

1. **Input**: User provides rough idea + selects modality (Text/Image/Video/System)
2. **RAG Retrieval**: System queries Pinecone for similar high-quality prompts
3. **Modality Routing**: Appropriate analyzer prompt is selected based on modality
4. **Analysis**: AI generates structured blueprint with gaps and questions
5. **Clarification**: User answers 2-5 targeted follow-up questions
6. **Refinement**: Blueprint + RAG context + answers are synthesized
7. **Generation**: Production-ready prompt with modality-specific optimizations
8. **Iteration**: One-click rewrite or modify with custom instructions

## 🎨 Prompt Structure

Generated prompts include nine comprehensive sections:

1. **Context**: Background and situational information
2. **Objective**: Clear goal statement
3. **Constraints**: Limitations and boundaries
4. **Audience**: Target users or stakeholders
5. **Tone & Style**: Communication approach
6. **Format**: Expected output structure
7. **Examples**: Reference cases (when applicable)
8. **Success Criteria**: Evaluation metrics
9. **Additional Notes**: Edge cases and considerations

Plus metadata:
- **Usage Guidance**: How to use the prompt effectively
- **Change Summary**: What was refined from the original
- **Assumptions Made**: Inferred context
- **Evaluation Checklist**: Quality validation points

## 🚀 Roadmap

### ✅ Completed
- [x] Pinecone RAG pipeline (28K+ vectors)
- [x] 9 modality-specific metaprompts
- [x] Context7 MCP integration (direct `mcp.context7.com`)
- [x] System prompt corpus from frontier models
- [x] Google OAuth authentication
- [x] Error feedback UX (inline form + GitHub issues)
- [x] Chain-of-thought loading indicator
- [x] Pipeline logging (PipelineLogger)

### 🔜 In Progress
- [ ] Open-sourcing the 28K Prompts empirical dataset
- [ ] Deploying predictive Prompt Performance Analytics based on Study E findings
- [ ] Public API with rate limiting

### 📋 Planned
- [ ] Automated A/B testing and format permutation generator
- [ ] Multi-LLM provider support (OpenAI, Anthropic)
- [ ] Unsloth QLoRA tuning pipelines for enterprise clients

## 🤝 Contributing

This is an early-stage project and I'm currently the only developer — so if you spot something broken, confusing, or just have an idea, **please don't be shy!**

- 🐛 **Something broken?** [Open an issue](https://github.com/Ker102/PromptTriage/issues/new) — even a one-liner helps
- 💡 **Got an idea?** [Start a discussion](https://github.com/Ker102/PromptTriage/discussions) or drop a feature request
- 🔧 **Want to contribute code?** PRs are welcome, big or small

See the [Contributing Guidelines](CONTRIBUTING.md) for setup instructions and conventions.

## 🔒 Security

Security is a top priority. Please see our [Security Policy](SECURITY.md) for:
- Reporting vulnerabilities
- Security best practices
- Disclosure policy

## 📄 License

This project is licensed under the terms specified in the LICENSE file.

## 🙏 Acknowledgments

- **Google Gemini Team**: For Gemini API and embeddings powering generation and RAG
- **Pinecone**: For the vector database infrastructure
- **Frontier Model Providers**: Claude, Cursor, v0, Windsurf—whose system prompts informed our corpus
- **Open Source Community**: For the amazing tools and libraries

## 📧 Contact

- **Issues**: [GitHub Issues](https://github.com/Ker102/PromptTriage/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Ker102/PromptTriage/discussions)

---

<div align="center">

**Built with ❤️ using RAG pipelines, modality-specific prompts, and frontier model patterns**

*Not just an API wrapper—a specialized prompt engineering system*

[⬆ Back to Top](#prompttriage)

</div>
