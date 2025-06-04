/**
 * Chat-related type definitions for the Biomarker Insights Chatbot
 */

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  responseId?: string; // For feedback tracking
  biomarkerReferences?: BiomarkerReference[];
  isFromCache?: boolean; // Indicates if response came from cache
  tokenUsage?: number; // For cost monitoring
}

export interface BiomarkerReference {
  name: string;
  value: number;
  unit: string;
  isAbnormal: boolean;
  referenceRange?: string;
}

export interface ConversationHistory {
  messages: ChatMessage[];
  profileId: string;
  createdAt: string;
  lastUpdated: string;
}

export interface BiomarkerContext {
  relevantBiomarkers: Array<{
    name: string;
    value: number;
    unit: string;
    reference_range: string;
    is_abnormal: boolean;
    trend?: "improved" | "worsened" | "stable";
    isFavorite?: boolean;
  }>;
  healthScoreContext?: {
    currentScore: number;
    influencingFactors: string[];
    trend: string;
  };
}

export interface ChatRequest {
  message: string;
  profileId: string;
  conversationHistory?: ChatMessage[];
  biomarkerContext?: BiomarkerContext;
}

export interface ChatResponse {
  response: string;
  biomarkerReferences?: BiomarkerReference[];
  suggestedFollowUps?: string[];
  sources?: string[];
  responseId: string;
  isFromCache: boolean;
  tokenUsage: number;
  responseTimeMs: number;
}

export interface SuggestedQuestion {
  question: string;
  category: "abnormal" | "favorites" | "general" | "health_score";
  priority: number;
}

export interface ChatSuggestionsResponse {
  suggestions: SuggestedQuestion[];
  welcomeMessage: string;
}

export interface ChatFeedback {
  responseId: string;
  isHelpful: boolean;
  feedbackType?: "accuracy" | "clarity" | "completeness" | "actionability";
  comment?: string;
}

export interface UsageMetrics {
  dailyApiCalls: number;
  dailyTokens: number;
  cacheHitRate: number;
  averageResponseTime: number;
  date: string;
  lastUpdated: string;
}

export interface ChatState {
  isOpen: boolean;
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  suggestedQuestions: SuggestedQuestion[];
  usageMetrics?: UsageMetrics;
}

export interface ConversationStorage {
  conversations: { [profileId: string]: ConversationHistory };
  maxConversationsPerProfile: number;
  maxMessagesPerConversation: number;
}

// Feature flags for optional functionality
export interface ChatFeatureFlags {
  healthScoreIntegration: boolean;
  usageLimitsEnabled: boolean;
  advancedCaching: boolean;
  feedbackCollection: boolean;
}

// Error types for better error handling
export interface ChatError {
  type: 'api_error' | 'network_error' | 'validation_error' | 'rate_limit' | 'cache_error';
  message: string;
  retryable: boolean;
  details?: any;
} 