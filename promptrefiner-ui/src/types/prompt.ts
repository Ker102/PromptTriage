export interface PromptQuestion {
  id: string;
  question: string;
  purpose?: string;
}

export interface PromptAnalysisResult {
  analysis: string;
  improvementAreas: string[];
  questions: PromptQuestion[];
  overallConfidence?: string;
}

export interface PromptRefinementResult {
  refinedPrompt: string;
  guidance?: string;
  assumptions?: string[];
  evaluationCriteria?: string[];
}

export interface AnalyzeRequestPayload {
  prompt: string;
  targetModel: string;
  context?: string;
}

export interface RefineRequestPayload extends AnalyzeRequestPayload {
  answers: Record<string, string>;
  questions: PromptQuestion[];
  tone?: string;
  outputRequirements?: string;
}
