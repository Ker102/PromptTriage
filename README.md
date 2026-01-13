# PromptTriage

<div align="center">

![Next.js](https://img.shields.io/badge/Next.js-15.1.6-black?style=for-the-badge&logo=next.js)
![React](https://img.shields.io/badge/React-19.0.0-61DAFB?style=for-the-badge&logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?style=for-the-badge&logo=typescript)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC?style=for-the-badge&logo=tailwind-css)
![Google Gemini](https://img.shields.io/badge/Google_Gemini-API-4285F4?style=for-the-badge&logo=google)

**An intelligent prompt engineering platform using metaprompts, few-shot learning, and orchestrated AI workflows**

[Features](#-features) • [System Design](#-system-design-philosophy) • [Architecture](#-architecture) • [Technologies](#-technologies) • [Contributing](CONTRIBUTING.md) • [Security](SECURITY.md)

</div>

---

## 🎯 Overview

**PromptTriage** is an enterprise-grade prompt engineering platform that transforms rough ideas and vague requirements into structured, production-ready AI prompts. Unlike simple prompt wrappers, PromptTriage employs a sophisticated orchestration design built on **metaprompts**, **system prompts**, and **few-shot learning** to deliver consistent, high-quality results. The system analyzes user intent, identifies gaps through structured blueprints, asks intelligent follow-up questions, and generates optimized prompts tailored for specific AI models and use cases.

This is not just a Gemini API wrapper—it's a specialized prompt engineering system that uses carefully crafted system instructions, curated few-shot examples across multiple domains (creative, analytical, technical), and a two-phase orchestration workflow to ensure every generated prompt meets production standards.

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

### 🌐 **Web Context Enrichment**
- **Firecrawl Integration**: Optional web search capability to enrich prompts with### 🧠 **Advanced RAG Architecture**
- **Hybrid Vector Store**: Combines **Redis** (hot cache) and **Pinecone** (long-term storage) for sub-millisecond retrieval.
- **Smart Retrieval**: Uses Google's `embedding-001` model to semantic search across **28,000+** verified prompts.
- **System Prompts Corpus**: Includes a curated library of 79+ high-quality system prompts from industry leaders (Claude, Cursor, v0, etc.), categorized and labeled by Gemini 3 Pro.

### 🎨 **Modality-Specific Engineering**
- **Unified Interface**: Seamlessly switch between **Text**, **Image**, and **Video** generation modes.
- **Context-Aware Refinement**: 
  - *Text*: Focuses on system instructions, tone, and structure.
  - *Image*: Optimizes for negative prompts, aspect ratios, and style descriptors.
  - *Video*: Enhances temporal consistency, camera motion, and duration parameters.

### 🛠️ **Precision Control**
- **Output Format Selector**: Force outputs into JSON, XML, Markdown, or tabular formats.
- **Live Documentation**: Integrated **Context7** service to fetch real-time library documentation (Next.js 15, React 19, etc.) during prompt generation.

### 🔄 **Iterative Refinement**
- **One-Click Rewrite**: Generate alternative refinements without re-answering questions
- **Metaprompt-Driven Consistency**: Curated system prompts guide Gemini to maintain quality across generations

## 🏗️ System Design Philosophy

**PromptTriage is built on a foundation of advanced prompt engineering techniques, not just API calls.**

### Core Design Principles

#### 1. **Metaprompt Architecture**
The system uses sophisticated metaprompts (system instructions) that define how Gemini should reason about and transform user inputs:
- **Analyzer Metaprompt**: Guides the analysis phase with specific reasoning steps, output structure requirements, and quality criteria
- **Refiner Metaprompt**: Orchestrates the synthesis phase with section templates, formatting rules, and consistency checks
- **Versioned Prompts**: Each metaprompt is versioned (e.g., `2024-12-claude-hybrid`) for reproducibility and iteration

#### 2. **Few-Shot Learning System**
PromptTriage includes curated few-shot examples across multiple domains to teach Gemini the expected behavior:
- **Creative Domain**: Website design, interactive applications (e.g., EduQuest learning platform)
- **Analytical Domain**: Business analysis, financial reports (e.g., Matterport 10-K summaries)
- **Technical Domain**: Bug reports, crash troubleshooting, error diagnostics
- **Data Domain**: Excel automation, SQL query specifications
- **5+ Hand-Crafted Examples**: Each example includes user input and ideal assistant response demonstrating the target behavior

The few-shot examples are injected before every API call, ensuring Gemini understands the exact output format, reasoning depth, and quality standards expected.

#### 3. **Blueprint-Based Orchestration**
The system uses a two-phase orchestration design with structured blueprints:

**Phase 1 - Analysis**:
- Extracts intent, audience, success criteria, constraints, risks
- Generates targeted follow-up questions (2-5 questions)
- Creates a structured blueprint with 10+ fields for later synthesis
- Validates completeness through confidence scoring

**Phase 2 - Refinement**:
- Reconciles the original prompt with blueprint and user answers
- Synthesizes a production-ready prompt with 9 standardized sections
- Generates usage guidance, change summaries, assumptions, and evaluation criteria
- Maintains consistency through template enforcement

#### 4. **Specialized for Prompt Generation**
Unlike general-purpose AI assistants, PromptTriage is specifically optimized for one task: **transforming vague ideas into production-ready prompts**. This specialization enables:
- Domain-specific validation logic for prompt quality
- Structured output formats that work across AI models
- Consistent reasoning patterns through metaprompt conditioning
- Reproducible results through versioning and few-shot stability

The system doesn't rely on Gemini's function calling or native tools—it uses **pure prompt engineering techniques** (system instructions, few-shot learning, structured output requirements) to achieve reliable results.

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
┌─────────────────────────────────────────┐
│         Analyzer API                     │
│         /api/analyze                     │
│                                          │
│  ┌────────────────────────────────┐    │
│  │  System Prompt Injection       │    │◄──── ANALYZER_SYSTEM_PROMPT
│  │  + Few-Shot Examples (5)       │    │      (Metaprompt v2024-12)
│  └────────────────────────────────┘    │
│              ↓                          │
│  ┌────────────────────────────────┐    │
│  │  Google Gemini Processing      │    │◄──── Few-Shot Examples:
│  │  (Guided by Metaprompt)        │    │      - Creative (EduQuest)
│  └────────────────────────────────┘    │      - Analytical (Matterport)
│              ↓                          │      - Crash (Submit Bug)
│  • Blueprint Generation                 │      - Excel Automation
│  • Follow-up Questions                  │      - SQL Analytics
│  • Risk Assessment                      │
└─────────┬───────────────────────────────┘
          │
          ▼
┌─────────────────┐
│  User Answers   │
│   Questions     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│         Refiner API                      │
│         /api/refine                      │
│                                          │
│  ┌────────────────────────────────┐    │
│  │  System Prompt Injection       │    │◄──── REFINER_SYSTEM_PROMPT
│  │  + Few-Shot Examples (5)       │    │      (Synthesis Instructions)
│  └────────────────────────────────┘    │
│              ↓                          │
│  ┌────────────────────────────────┐    │
│  │  Blueprint + Answers Fusion    │    │
│  │  Structured Output Generation  │    │
│  └────────────────────────────────┘    │
│              ↓                          │
│  • 9-Section Prompt Generation          │
│  • Quality Checks                       │
│  • Evaluation Criteria                  │
└─────────┬───────────────────────────────┘
          │
          ▼
┌─────────────────┐
│  Final Prompt   │
│  (AI-Ready)     │
└─────────────────┘
```

### Key Components

#### Frontend Layer (`src/app/`)
- **`page.tsx`**: Main UI orchestration and state management
- **Responsive Interface**: Tailwind CSS-powered responsive design
- **Real-time Feedback**: Loading states and progressive enhancement

#### API Layer (`src/app/api/`)
- **`analyze/route.ts`**: Prompt analysis endpoint with metaprompt injection
- **`refine/route.ts`**: Prompt refinement and generation endpoint with few-shot learning
- **RESTful Design**: Clean API contracts with TypeScript validation

#### Core Libraries (`src/lib/`)
- **`gemini.ts`**: Gemini API client wrapper with error handling
- **JSON Parsing Utilities**: Robust extraction and validation

#### Type System (`src/types/`)
- **`prompt.ts`**: Shared interfaces for request/response payloads
- **Type Safety**: End-to-end TypeScript coverage

#### **Prompt Engineering Core (`src/prompts/`)**
This is the heart of PromptTriage's intelligence:

- **`metaprompt.ts`**: System prompts and few-shot examples repository
  - **`ANALYZER_SYSTEM_PROMPT`**: 500+ line metaprompt defining analysis reasoning steps
  - **`REFINER_SYSTEM_PROMPT`**: 400+ line metaprompt for synthesis with section templates
  - **`ANALYZER_FEW_SHOTS`**: 5 domain-specific examples (creative, analytical, crash, Excel, SQL)
  - **`REFINER_FEW_SHOTS`**: 5 corresponding refinement examples showing target output
  - **Version Control**: `PROMPT_VERSION = "2024-12-claude-hybrid"` for reproducibility
  - **Example Repository**: Hand-crafted scenarios (1000+ lines each) demonstrating optimal behavior

**How It Works**: 
Before every Gemini API call, the system constructs a conversation history starting with the system prompt, followed by all few-shot example pairs (user → assistant), and finally the actual user request. This teaches Gemini the exact reasoning pattern, output structure, and quality standards expected—achieving consistent, production-ready results without function calling or tool use.

## 🛠️ Technologies

### Core Stack
- **[Next.js 15.1.6](https://nextjs.org/)**: React framework with server-side rendering and API routes
- **[React 19.0.0](https://react.dev/)**: Component-based UI library
- **[TypeScript 5](https://www.typescriptlang.org/)**: Type-safe JavaScript superset
- **[Tailwind CSS 3.4](https://tailwindcss.com/)**: Utility-first CSS framework

### AI & Prompt Engineering
- **[Google Gemini API](https://ai.google.dev/)**: Language model for executing metaprompt-guided workflows
- **Custom Metaprompts**: Hand-crafted system instructions defining reasoning patterns
- **Few-Shot Learning**: Domain-specific examples teaching expected behavior
- **Structured Outputs**: JSON schema enforcement through prompt design
- **[Firecrawl](https://firecrawl.dev/)** *(Optional)*: Web scraping for context enrichment

### Authentication
- **[NextAuth.js 4.24](https://next-auth.js.org/)**: Authentication library with OAuth 2.0 support

### Development Tools
- **[ESLint 9](https://eslint.org/)**: Code linting and style enforcement
- **[Turbopack](https://turbo.build/)**: High-performance Next.js bundler
- **[PostCSS 8](https://postcss.org/)**: CSS transformation pipeline

### Infrastructure
- **Node.js 18.17+**: JavaScript runtime (optimized for Node 20+)
- **npm**: Package management

## 📈 Use Cases

- **AI Product Development**: Generate production-ready prompts for AI features
- **Content Creation**: Craft precise prompts for copywriting, marketing, and creative work
- **Data Analysis**: Structure prompts for analytical tasks and reporting
- **Research**: Formulate clear research questions and analysis frameworks
- **Education**: Teach effective prompt engineering techniques
- **Automation**: Create consistent, reusable prompt templates

## 🔄 Workflow

1. **Input**: User provides a rough idea or initial prompt
2. **Metaprompt Injection**: System injects ANALYZER_SYSTEM_PROMPT + 5 few-shot examples
3. **Analysis**: Gemini (guided by metaprompt) analyzes the prompt and generates a structured blueprint
4. **Clarification**: System asks 2-5 targeted follow-up questions based on detected gaps
5. **User Response**: User answers the clarifying questions
6. **Metaprompt Injection**: System injects REFINER_SYSTEM_PROMPT + 5 few-shot examples
7. **Synthesis**: User answers + blueprint are reconciled through the refiner metaprompt
8. **Generation**: Final AI-ready prompt is generated following 9-section template with metadata
9. **Iteration**: Optional one-click rewrite for alternative perspectives (uses variation hints)

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

- [ ] User authentication and prompt history storage
- [ ] Multi-LLM provider support (OpenAI, Anthropic, etc.)
- [ ] Collaborative prompt editing
- [ ] A/B testing framework for prompt versions
- [ ] Automated testing suite
- [ ] Template marketplace
- [ ] API for programmatic access
- [ ] Analytics dashboard for prompt performance

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on:
- Code of Conduct
- Development setup
- Pull request process
- Coding standards

## 🔒 Security

Security is a top priority. Please see our [Security Policy](SECURITY.md) for:
- Reporting vulnerabilities
- Security best practices
- Disclosure policy

## 📄 License

This project is licensed under the terms specified in the LICENSE file.

## 🙏 Acknowledgments

- **Google Gemini Team**: For providing the powerful language model that executes our metaprompts
- **Vercel**: For the Next.js framework
- **Open Source Community**: For the amazing tools and libraries
- **Prompt Engineering Research**: Inspired by advances in few-shot learning, chain-of-thought prompting, and structured output generation

## 📧 Contact

- **Issues**: [GitHub Issues](https://github.com/Ker102/PromptTriage/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Ker102/PromptTriage/discussions)

---

<div align="center">

**Built with ❤️ using metaprompts, few-shot learning, Next.js, TypeScript, and Google Gemini**

*Not just an API wrapper—a specialized prompt engineering system*

[⬆ Back to Top](#prompttriage)

</div>
