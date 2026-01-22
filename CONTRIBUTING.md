# Contributing to PromptTriage

Thank you for your interest in contributing to PromptTriage! We welcome contributions from the community and are grateful for your support.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Community](#community)

## 📜 Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js**: Version 20+ recommended
- **Python**: Version 3.9+ (for backend services)
- **npm**: Version 9.0 or higher
- **Git**: For version control
- **Google Gemini API Key**: Required for AI functionality
- **Pinecone API Key**: Required for RAG functionality
- **Redis**: Optional, for hot caching

### First-Time Contributors

If you're new to open source, welcome! Here are some resources to help you get started:

- [How to Contribute to Open Source](https://opensource.guide/how-to-contribute/)
- [GitHub Flow Guide](https://guides.github.com/introduction/flow/)
- [Understanding the GitHub Flow](https://guides.github.com/introduction/flow/)

## 🛠️ Development Setup

### 1. Fork and Clone the Repository

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR-USERNAME/PromptTriage.git
cd PromptTriage
```

### 2. Set Up the Development Environment

#### Frontend Setup
```bash
# Navigate to the application directory
cd promptrefiner-ui

# Install dependencies
npm install
```

#### Backend Setup
```bash
# Navigate to the backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env.local` file in the `promptrefiner-ui` directory and a `.env` file in `backend`:

```env
# Required: AI Services
GEMINI_API_KEY=your_gemini_api_key_here
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=prompt-triage

# Optional: Authentication
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
NEXTAUTH_SECRET=your_nextauth_secret
NEXTAUTH_URL=http://localhost:3000

# Optional: Enhancements
REDIS_URL=redis://localhost:6379
FIRECRAWL_API_KEY=your_firecrawl_api_key
```

**How to get API keys:**
- **Gemini API Key**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Pinecone API Key**: Visit [Pinecone Console](https://app.pinecone.io/)

### 4. Start the Development Server

```bash
# Run the development server with Turbopack
npm run dev
```

The application will be available at [http://localhost:3000](http://localhost:3000).

### 5. Verify Your Setup

1. Open your browser and navigate to `http://localhost:3000`
2. Test the analyzer by entering a sample prompt
3. Verify that the AI responses are working correctly

## 🤝 How to Contribute

### Types of Contributions We Welcome

- **🐛 Bug Fixes**: Fix issues and improve stability
- **✨ New Features**: Add new functionality that aligns with project goals
- **📚 Documentation**: Improve or add documentation
- **🧪 Tests**: Add or improve test coverage
- **🎨 UI/UX Improvements**: Enhance the user interface and experience
- **⚡ Performance**: Optimize code and improve performance
- **🔒 Security**: Identify and fix security vulnerabilities

### Before You Start

1. **Check Existing Issues**: Browse [open issues](https://github.com/Ker102/PromptTriage/issues) to see if someone is already working on it
2. **Create an Issue**: For significant changes, create an issue first to discuss your approach
3. **Claim an Issue**: Comment on an issue to let others know you're working on it

### Working on an Issue

1. **Create a Branch**: Use a descriptive branch name
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

2. **Make Your Changes**: Follow the coding standards and keep commits focused

3. **Test Your Changes**: Ensure all tests pass and manually verify functionality

4. **Commit Your Changes**: Use clear, descriptive commit messages
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

## 🔄 Pull Request Process

### 1. Prepare Your Pull Request

Before submitting:

- [ ] Ensure your code follows the project's coding standards
- [ ] Run linting: `npm run lint`
- [ ] Build the project: `npm run build`
- [ ] Test your changes thoroughly
- [ ] Update documentation if needed
- [ ] Add/update tests if applicable
- [ ] Rebase on the latest `main` branch

### 2. Submit Your Pull Request

1. Push your branch to your fork:
   ```bash
   git push origin your-branch-name
   ```

2. Go to the [PromptTriage repository](https://github.com/Ker102/PromptTriage) and click "New Pull Request"

3. Fill out the PR template completely:
   - Provide a clear description of your changes
   - Reference related issues
   - Include screenshots for UI changes
   - List any breaking changes

### 3. Pull Request Review

- **Be Responsive**: Address review comments promptly
- **Be Patient**: Reviews may take time
- **Be Open**: Be receptive to feedback and suggestions
- **Iterate**: Make requested changes and push updates

### 4. After Your PR is Merged

- Delete your feature branch
- Pull the latest changes from `main`
- Celebrate! 🎉 You've contributed to PromptTriage!

## 📏 Coding Standards

### TypeScript

- Use TypeScript for all new code
- Define proper types and interfaces
- Avoid using `any` type unless absolutely necessary
- Use meaningful variable and function names

### Code Style

- Follow the existing code style
- Use ESLint to check your code: `npm run lint`
- Use 2 spaces for indentation
- Use single quotes for strings
- Add trailing commas in multi-line objects and arrays

### File Organization

```
PromptTriage/
├── promptrefiner-ui/     # Next.js frontend
│   ├── src/
│   │   ├── app/          # Next.js App Router
│   │   ├── api/          # Integration endpoints
│   │   ├── components/   # React components
│   │   ├── services/     # RAG, Context7, Firecrawl clients
│   │   └── prompts/      # Modality-specific metaprompts
├── backend/              # FastAPI RAG service
│   ├── app/routers/      # RAG & Ingestion endpoints
│   └── scripts/          # Dataset ingestion pipelines
└── datasets/             # Curated prompt datasets
```

### Naming Conventions

- **Files**: Use kebab-case for file names (e.g., `prompt-analyzer.ts`)
- **Components**: Use PascalCase for React components (e.g., `PromptForm.tsx`)
- **Functions**: Use camelCase for functions (e.g., `analyzePrompt()`)
- **Constants**: Use UPPER_SNAKE_CASE for constants (e.g., `API_ENDPOINT`)

### Comments

- Write clear, concise comments for complex logic
- Use JSDoc for function documentation
- Avoid obvious comments that just restate the code

```typescript
/**
 * Analyzes a user prompt and generates follow-up questions
 * @param prompt - The initial user prompt to analyze
 * @param targetModel - The AI model to optimize for
 * @returns Analysis blueprint and follow-up questions
 */
async function analyzePrompt(prompt: string, targetModel: string) {
  // Implementation
}
```

## 🧪 Testing Guidelines

### Manual Testing

All changes should be manually tested:

1. **Functional Testing**: Verify the feature works as expected
2. **Edge Cases**: Test with unusual or extreme inputs
3. **Cross-Browser**: Test on Chrome, Firefox, Safari
4. **Responsive**: Test on different screen sizes
5. **Error Handling**: Test error scenarios

### Testing Checklist

- [ ] Code runs without errors
- [ ] No console warnings or errors
- [ ] UI is responsive and accessible
- [ ] Error messages are clear and helpful
- [ ] Loading states are handled properly
- [ ] Forms validate input correctly

### Future: Automated Testing

We're planning to add:
- Unit tests with Jest
- Integration tests
- E2E tests with Playwright

Contributions to test infrastructure are welcome!

## 📚 Documentation

Good documentation is crucial for a healthy project.

### When to Update Documentation

Update documentation when you:
- Add new features
- Change existing behavior
- Fix bugs that affect usage
- Update configuration or setup

### Documentation Types

- **README.md**: Project overview and getting started
- **Code Comments**: Inline documentation
- **API Documentation**: Document API endpoints
- **Examples**: Add examples for new features

### Writing Good Documentation

- Use clear, simple language
- Provide examples and use cases
- Include screenshots for UI features
- Keep it up-to-date with code changes

## 👥 Community

### Get Help

- **GitHub Discussions**: [Ask questions and share ideas](https://github.com/Ker102/PromptTriage/discussions)
- **GitHub Issues**: [Report bugs or request features](https://github.com/Ker102/PromptTriage/issues)

### Stay Connected

- **Star the Repository**: Show your support!
- **Watch for Updates**: Get notified of new releases
- **Follow Contributors**: Learn from other contributors

### Recognition

Contributors are recognized in:
- GitHub's contributor graph
- Release notes (for significant contributions)
- Project documentation (for major features)

## 📝 Commit Message Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `ci`: CI/CD changes

### Examples

```
feat(analyzer): add support for custom model parameters

Added configuration options to allow users to customize
temperature, top_p, and max_tokens for the analyzer.

Closes #123
```

```
fix(ui): resolve mobile responsiveness issue in prompt form

The prompt textarea was overflowing on small screens.
Updated the CSS to ensure proper responsive behavior.

Fixes #456
```

## 🔐 Security

If you discover a security vulnerability, please do **NOT** open a public issue. Instead, follow our [Security Policy](SECURITY.md) to report it responsibly.

## ⚖️ License

By contributing to PromptTriage, you agree that your contributions will be licensed under the same license as the project.

## 🙏 Thank You!

Your contributions make PromptTriage better for everyone. Whether you're fixing a typo, adding a feature, or helping with documentation, every contribution counts!

---

**Questions?** Feel free to open a [discussion](https://github.com/Ker102/PromptTriage/discussions) or reach out to the maintainers.

Happy contributing! 🚀
