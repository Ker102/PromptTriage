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
  blueprint: PromptBlueprint;
  externalContext?: RetrievedDocument[];
}

export interface PromptRefinementResult {
  refinedPrompt: string;
  guidance: string;
  changeSummary: string[];
  assumptions: string[];
  evaluationCriteria: string[];
}

export interface AnalyzeRequestPayload {
  prompt: string;
  targetModel: string;
  context?: string;
  useWebSearch?: boolean;
}

export interface RefineRequestPayload extends AnalyzeRequestPayload {
  answers: Record<string, string>;
  questions: PromptQuestion[];
  blueprint: PromptBlueprint;
  tone?: string;
  outputRequirements?: string;
  externalContext?: RetrievedDocument[];
  variationHint?: string;
}

export interface PromptBlueprint {
  version: string;
  intent: string;
  audience: string;
  successCriteria: string[];
  requiredInputs: string[];
  domainContext: string[];
  constraints: string[];
  tone: string;
  risks: string[];
  outputFormat: string;
  evaluationChecklist: string[];
}

export interface RetrievedDocument {
  title: string;
  url: string;
  snippet: string;
  score?: number;
}
