// Task Classification Utility for PromptTriage
// Determines whether a prompt should be routed to the standard Analyzer/Refiner
// or to the specialized System Prompt Generator

export type PromptType = 'task_prompt' | 'system_prompt';

export interface ClassificationResult {
    type: PromptType;
    confidence: 'high' | 'medium' | 'low';
    reason: string;
    suggestedRoute: '/api/analyze' | '/api/generate-system-prompt';
}

// Keywords that strongly indicate a system prompt request
const SYSTEM_PROMPT_INDICATORS = [
    'system prompt',
    'agent prompt',
    'assistant prompt',
    'ai persona',
    'ai personality',
    'chatbot personality',
    'define the ai',
    'ai behavior',
    'ai assistant definition',
    'create an agent',
    'build an agent',
    'design an ai',
    'ai character',
    'bot personality',
    'custom gpt',
    'gpts instructions',
];

// Keywords that strongly indicate a task/regular prompt
const TASK_PROMPT_INDICATORS = [
    'write a function',
    'create a website',
    'analyze this',
    'summarize',
    'explain how',
    'help me with',
    'debug this',
    'fix this code',
    'generate code',
    'write documentation',
    'translate',
    'convert',
    'calculate',
    'find the',
    'what is',
    'how do i',
    'step by step',
];

// Contextual phrases that suggest defining AI behavior (system prompt)
const BEHAVIORAL_PHRASES = [
    'should act as',
    'should behave like',
    'should respond as',
    'role as',
    'persona of',
    'character of',
    'personality that',
    'tone should be',
    'voice should be',
    'always respond',
    'never respond',
    'when asked about',
    'if the user',
];

/**
 * Classifies a prompt to determine the appropriate route
 */
export function classifyPrompt(prompt: string, context?: string): ClassificationResult {
    const normalizedPrompt = prompt.toLowerCase().trim();
    const normalizedContext = context?.toLowerCase().trim() ?? '';
    const combined = `${normalizedPrompt} ${normalizedContext}`;

    // Check for explicit system prompt indicators
    const systemPromptMatches = SYSTEM_PROMPT_INDICATORS.filter(indicator =>
        combined.includes(indicator)
    );

    // Check for task prompt indicators
    const taskPromptMatches = TASK_PROMPT_INDICATORS.filter(indicator =>
        combined.includes(indicator)
    );

    // Check for behavioral phrases
    const behavioralMatches = BEHAVIORAL_PHRASES.filter(phrase =>
        combined.includes(phrase)
    );

    // Calculate scores
    const systemScore = systemPromptMatches.length * 3 + behavioralMatches.length * 2;
    const taskScore = taskPromptMatches.length * 2;

    // Decision logic
    if (systemScore >= 3 && systemScore > taskScore) {
        return {
            type: 'system_prompt',
            confidence: systemScore >= 6 ? 'high' : 'medium',
            reason: `Detected system prompt indicators: ${systemPromptMatches.join(', ')}${behavioralMatches.length > 0 ? ` and behavioral phrases: ${behavioralMatches.join(', ')}` : ''}`,
            suggestedRoute: '/api/generate-system-prompt',
        };
    }

    if (taskScore > systemScore || systemScore < 3) {
        return {
            type: 'task_prompt',
            confidence: taskScore >= 4 ? 'high' : taskScore >= 2 ? 'medium' : 'low',
            reason: taskScore > 0
                ? `Detected task-oriented language: ${taskPromptMatches.join(', ')}`
                : 'No strong indicators found, defaulting to task prompt',
            suggestedRoute: '/api/analyze',
        };
    }

    // Ambiguous case
    return {
        type: 'task_prompt',
        confidence: 'low',
        reason: 'Ambiguous request - defaulting to standard analysis. User can switch to System Prompt Generator if needed.',
        suggestedRoute: '/api/analyze',
    };
}

/**
 * Quick check if a prompt is likely a system prompt request
 * Used for UI hints without full classification
 */
export function isLikelySystemPromptRequest(prompt: string): boolean {
    const normalized = prompt.toLowerCase().trim();
    return SYSTEM_PROMPT_INDICATORS.some(indicator => normalized.includes(indicator));
}

/**
 * Get a suggestion message for the user based on classification
 */
export function getRoutingSuggestion(result: ClassificationResult): string | null {
    if (result.type === 'system_prompt' && result.confidence !== 'low') {
        return 'This looks like a request to create a system prompt for an AI assistant. Would you like to use the System Prompt Generator for better results?';
    }

    if (result.type === 'task_prompt' && result.confidence === 'low') {
        return 'If you\'re trying to define how an AI should behave (rather than what it should do), try our System Prompt Generator.';
    }

    return null;
}
