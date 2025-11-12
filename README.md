# PromptTriage

<div align="center">

![GitHub](https://img.shields.io/github/license/Ker102/PromptTriage?style=for-the-badge)
![GitHub Stars](https://img.shields.io/github/stars/Ker102/PromptTriage?style=for-the-badge)
![GitHub Issues](https://img.shields.io/github/issues/Ker102/PromptTriage?style=for-the-badge)
![GitHub Pull Requests](https://img.shields.io/github/issues-pr/Ker102/PromptTriage?style=for-the-badge)
![Next.js](https://img.shields.io/badge/Next.js-15.1.6-black?style=for-the-badge&logo=next.js)
![React](https://img.shields.io/badge/React-19.0.0-61DAFB?style=for-the-badge&logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?style=for-the-badge&logo=typescript)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC?style=for-the-badge&logo=tailwind-css)

**An intelligent AI prompt refinement platform powered by Google Gemini**

[Features](#-features) • [Architecture](#-architecture) • [Technologies](#-technologies) • [Contributing](CONTRIBUTING.md) • [Security](SECURITY.md)

</div>

---

## 🎯 Overview

**PromptTriage** is an enterprise-grade Next.js application that transforms rough ideas and vague requirements into structured, production-ready AI prompts. By leveraging Google Gemini's advanced language understanding, PromptTriage analyzes user intent, identifies gaps, asks intelligent follow-up questions, and generates optimized prompts tailored for specific AI models and use cases.

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
- **Firecrawl Integration**: Optional web search capability to enrich prompts with real-time information
- **Source Attribution**: Transparent citation system for all external context
- **Fresh Data Pipeline**: Ensures prompts are informed by current information when needed

### 🔄 **Iterative Refinement**
- **One-Click Rewrite**: Generate alternative refinements without re-answering questions
- **Version Tracking**: Built-in prompt versioning system for iteration management
- **Few-Shot Metaprompting**: Curated examples guide Gemini to maintain consistency and quality

### 🔐 **Enterprise Security**
- **Google OAuth 2.0**: Secure authentication with Google Sign-In
- **NextAuth.js Integration**: Session management and authentication flows
- **Environment-based Configuration**: Secure API key management

### 📊 **Developer Experience**
- **TypeScript-First**: Full type safety across the application
- **Modern Tooling**: ESLint, Turbopack, and PostCSS for optimal development
- **Responsive Design**: Tailwind CSS-powered UI that works on all devices

## 🏗️ Architecture

### System Design

```
┌─────────────────┐
│   User Input    │
│  (Rough Idea)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Analyzer API   │◄──── Google Gemini
│  /api/analyze   │      (Analysis)
└────────┬────────┘
         │
         ├─► Blueprint Generation
         ├─► Follow-up Questions
         └─► Risk Assessment
         │
         ▼
┌─────────────────┐
│  User Answers   │
│   Questions     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Refiner API    │◄──── Google Gemini
│  /api/refine    │      (Synthesis)
└────────┬────────┘
         │
         ├─► Prompt Generation
         ├─► Quality Checks
         └─► Evaluation Criteria
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
- **`analyze/route.ts`**: Prompt analysis endpoint with Gemini integration
- **`refine/route.ts`**: Prompt refinement and generation endpoint
- **RESTful Design**: Clean API contracts with TypeScript validation

#### Core Libraries (`src/lib/`)
- **`gemini.ts`**: Gemini API client wrapper with error handling
- **JSON Parsing Utilities**: Robust extraction and validation

#### Type System (`src/types/`)
- **`prompt.ts`**: Shared interfaces for request/response payloads
- **Type Safety**: End-to-end TypeScript coverage

#### Prompt Engineering (`src/prompts/`)
- **`metaprompt.ts`**: System prompts and few-shot examples
- **Version Control**: Prompt versioning for reproducibility
- **Example Repository**: Curated scenarios for optimal Gemini performance

## 🛠️ Technologies

### Core Stack
- **[Next.js 15.1.6](https://nextjs.org/)**: React framework with server-side rendering and API routes
- **[React 19.0.0](https://react.dev/)**: Component-based UI library
- **[TypeScript 5](https://www.typescriptlang.org/)**: Type-safe JavaScript superset
- **[Tailwind CSS 3.4](https://tailwindcss.com/)**: Utility-first CSS framework

### AI & Authentication
- **[Google Gemini API](https://ai.google.dev/)**: Advanced language model for prompt analysis and generation
- **[NextAuth.js 4.24](https://next-auth.js.org/)**: Authentication library with OAuth 2.0 support
- **[Firecrawl](https://firecrawl.dev/)** *(Optional)*: Web scraping for context enrichment

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
2. **Analysis**: Gemini analyzes the prompt and generates a structured blueprint
3. **Clarification**: System asks 2-5 targeted follow-up questions
4. **Synthesis**: User answers are combined with the blueprint
5. **Generation**: Final AI-ready prompt is generated with metadata
6. **Iteration**: Optional one-click rewrite for alternative perspectives

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

## 📊 Project Status

![GitHub commit activity](https://img.shields.io/github/commit-activity/m/Ker102/PromptTriage?style=flat-square)
![GitHub last commit](https://img.shields.io/github/last-commit/Ker102/PromptTriage?style=flat-square)

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

- **Google Gemini Team**: For providing the powerful AI capabilities
- **Vercel**: For the Next.js framework
- **Open Source Community**: For the amazing tools and libraries

## 📧 Contact

- **Issues**: [GitHub Issues](https://github.com/Ker102/PromptTriage/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Ker102/PromptTriage/discussions)

---

<div align="center">

**Built with ❤️ using Next.js, TypeScript, and Google Gemini**

[⬆ Back to Top](#prompttriage)

</div>
