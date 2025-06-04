/**
 * Chat service for handling Biomarker Insights Chatbot API communication
 * and conversation persistence using localStorage/sessionStorage.
 */
import { 
  ChatMessage, ChatRequest, ChatResponse, 
  SuggestedQuestion, ChatSuggestionsResponse,
  ChatFeedback, ConversationHistory, ConversationStorage,
  BiomarkerContext, UsageMetrics, ChatError
} from '../types/chat';
import { Biomarker } from '../types/pdf';
import api from './api';
import { logger } from '../utils/logger';

class ChatService {
  private readonly STORAGE_KEY = 'vein_diagram_chat_conversations';
  private readonly MAX_CONVERSATIONS_PER_PROFILE = 5;
  private readonly MAX_MESSAGES_PER_CONVERSATION = 100;
  
  /**
   * Send a chat message and get AI response
   */
  async sendMessage(
    message: string,
    profileId: string,
    biomarkerContext?: BiomarkerContext
  ): Promise<ChatResponse> {
    try {
      // Get recent conversation history for context
      const conversationHistory = this.getConversationHistory(profileId);
      const recentMessages = conversationHistory.slice(-10); // Last 10 messages for API context
      
      const request: ChatRequest = {
        message: message.trim(),
        profileId,
        conversationHistory: recentMessages,
        biomarkerContext
      };
      
      // Validate message length
      if (request.message.length === 0 || request.message.length > 1000) {
        throw new Error('Message must be between 1 and 1000 characters');
      }
      
      const response = await api.post<ChatResponse>('/api/chat', request);
      
      // Store both user message and AI response in conversation history
      this.addMessagesToHistory(profileId, [
        {
          id: this.generateMessageId(),
          role: 'user',
          content: message,
          timestamp: new Date().toISOString()
        },
        {
          id: response.data.responseId,
          role: 'assistant',
          content: response.data.response,
          timestamp: new Date().toISOString(),
          responseId: response.data.responseId,
          biomarkerReferences: response.data.biomarkerReferences,
          isFromCache: response.data.isFromCache,
          tokenUsage: response.data.tokenUsage
        }
      ]);
      
      // Log chat interaction (fallback if logger doesn't have logChatInteraction)
      try {
        if (typeof logger.logChatInteraction === 'function') {
          logger.logChatInteraction('message_sent', {
            profileId,
            messageLength: message.length,
            isFromCache: response.data.isFromCache,
            tokenUsage: response.data.tokenUsage,
            responseTime: response.data.responseTimeMs
          });
        } else {
          logger.info('Chat interaction', {
            action: 'message_sent',
            profileId,
            messageLength: message.length,
            isFromCache: response.data.isFromCache,
            tokenUsage: response.data.tokenUsage,
            responseTime: response.data.responseTimeMs
          });
        }
      } catch (logError) {
        console.log('Chat interaction logged:', {
          action: 'message_sent',
          profileId,
          messageLength: message.length,
          isFromCache: response.data.isFromCache,
          tokenUsage: response.data.tokenUsage,
          responseTime: response.data.responseTimeMs
        });
      }
      
      return response.data;
      
    } catch (error: any) {
      logger.error('Chat service error:', error);
      
      // Create standardized error response
      const chatError: ChatError = {
        type: this.categorizeError(error),
        message: this.getErrorMessage(error),
        retryable: this.isRetryableError(error),
        details: error.response?.data || error.message
      };
      
      throw chatError;
    }
  }
  
  /**
   * Get suggested questions for a profile
   */
  async getSuggestions(profileId: string): Promise<ChatSuggestionsResponse> {
    try {
      const response = await api.get<ChatSuggestionsResponse>(`/api/chat/suggestions/${profileId}`);
      
      // Log suggestions fetch (with fallback)
      try {
        if (typeof logger.logChatInteraction === 'function') {
          logger.logChatInteraction('suggestions_fetched', {
            profileId,
            suggestionsCount: response.data.suggestions.length
          });
        } else {
          logger.info('Chat suggestions fetched', {
            profileId,
            suggestionsCount: response.data.suggestions.length
          });
        }
      } catch (logError) {
        console.log('Chat suggestions fetched:', { profileId, suggestionsCount: response.data.suggestions.length });
      }
      
      return response.data;
      
    } catch (error: any) {
      logger.error('Chat suggestions error:', error);
      
      // Return fallback suggestions
      return {
        suggestions: [
          { question: "What do my abnormal biomarkers mean?", category: "abnormal", priority: 1 },
          { question: "How can I improve my biomarker values?", category: "general", priority: 2 },
          { question: "What dietary changes would help?", category: "general", priority: 3 }
        ],
        welcomeMessage: "Hi! I'm your biomarker health assistant. How can I help you today?"
      };
    }
  }
  
  /**
   * Submit feedback on a chat response
   */
  async submitFeedback(feedback: ChatFeedback): Promise<void> {
    try {
      await api.post('/api/chat/feedback', feedback);
      
      // Log feedback submission (with fallback)
      try {
        if (typeof logger.logChatInteraction === 'function') {
          logger.logChatInteraction('feedback_submitted', {
            responseId: feedback.responseId,
            isHelpful: feedback.isHelpful,
            feedbackType: feedback.feedbackType
          });
        } else {
          logger.info('Chat feedback submitted', {
            responseId: feedback.responseId,
            isHelpful: feedback.isHelpful,
            feedbackType: feedback.feedbackType
          });
        }
      } catch (logError) {
        console.log('Chat feedback submitted:', {
          responseId: feedback.responseId,
          isHelpful: feedback.isHelpful,
          feedbackType: feedback.feedbackType
        });
      }
      
    } catch (error: any) {
      logger.error('Chat feedback error:', error);
      // Don't throw error for feedback - it's not critical
    }
  }
  
  /**
   * Get usage metrics for cost monitoring
   */
  async getUsageMetrics(profileId: string): Promise<UsageMetrics | null> {
    try {
      const response = await api.get<UsageMetrics>(`/api/chat/usage/${profileId}`);
      return response.data;
      
    } catch (error: any) {
      logger.error('Usage metrics error:', error);
      return null;
    }
  }
  
  /**
   * Get conversation history for a profile
   */
  getConversationHistory(profileId: string): ChatMessage[] {
    try {
      const storage = this.loadConversationStorage();
      const conversation = storage.conversations[profileId];
      
      if (!conversation) {
        return [];
      }
      
      return conversation.messages;
      
    } catch (error) {
      logger.error('Error loading conversation history:', error);
      return [];
    }
  }
  
  /**
   * Add messages to conversation history
   */
  addMessagesToHistory(profileId: string, messages: ChatMessage[]): void {
    try {
      const storage = this.loadConversationStorage();
      
      if (!storage.conversations[profileId]) {
        storage.conversations[profileId] = {
          messages: [],
          profileId,
          createdAt: new Date().toISOString(),
          lastUpdated: new Date().toISOString()
        };
      }
      
      const conversation = storage.conversations[profileId];
      conversation.messages.push(...messages);
      conversation.lastUpdated = new Date().toISOString();
      
      // Trim messages if conversation gets too long
      if (conversation.messages.length > this.MAX_MESSAGES_PER_CONVERSATION) {
        const excessMessages = conversation.messages.length - this.MAX_MESSAGES_PER_CONVERSATION;
        conversation.messages = conversation.messages.slice(excessMessages);
      }
      
      this.saveConversationStorage(storage);
      
    } catch (error) {
      logger.error('Error saving conversation history:', error);
    }
  }
  
  /**
   * Clear conversation history for a profile
   */
  clearConversationHistory(profileId: string): void {
    try {
      const storage = this.loadConversationStorage();
      delete storage.conversations[profileId];
      this.saveConversationStorage(storage);
      
      // Log conversation clear (with fallback)
      try {
        if (typeof logger.logChatInteraction === 'function') {
          logger.logChatInteraction('conversation_cleared', { profileId });
        } else {
          logger.info('Conversation cleared', { profileId });
        }
      } catch (logError) {
        console.log('Conversation cleared for profile:', profileId);
      }
      
    } catch (error) {
      logger.error('Error clearing conversation history:', error);
    }
  }
  
  /**
   * Clear all conversation data (privacy)
   */
  clearAllConversations(): void {
    try {
      localStorage.removeItem(this.STORAGE_KEY);
      sessionStorage.removeItem(this.STORAGE_KEY);
      
      // Log all conversations clear (with fallback)
      try {
        if (typeof logger.logChatInteraction === 'function') {
          logger.logChatInteraction('all_conversations_cleared', {});
        } else {
          logger.info('All conversations cleared');
        }
      } catch (logError) {
        console.log('All conversations cleared');
      }
      
    } catch (error) {
      logger.error('Error clearing all conversations:', error);
    }
  }
  
  /**
   * Prepare biomarker context from user's biomarker data
   */
  prepareBiomarkerContext(
    biomarkers: Biomarker[],
    favoriteBiomarkers: string[] = []
  ): BiomarkerContext {
    const relevantBiomarkers = biomarkers.map(biomarker => ({
      name: biomarker.name,
      value: biomarker.value,
      unit: biomarker.unit,
      reference_range: biomarker.referenceRange || '',
      is_abnormal: biomarker.isAbnormal || false,
      trend: undefined, // TODO: Calculate from historical data
      isFavorite: favoriteBiomarkers.includes(biomarker.name)
    }));
    
    // Prioritize abnormal and favorite biomarkers
    const sortedBiomarkers = relevantBiomarkers.sort((a, b) => {
      if (a.is_abnormal && !b.is_abnormal) return -1;
      if (!a.is_abnormal && b.is_abnormal) return 1;
      if (a.isFavorite && !b.isFavorite) return -1;
      if (!a.isFavorite && b.isFavorite) return 1;
      return 0;
    });
    
    // Limit to top 20 biomarkers for context efficiency
    return {
      relevantBiomarkers: sortedBiomarkers.slice(0, 20)
      // healthScoreContext: Optional - implement when Health Score is ready
    };
  }
  
  /**
   * Check if chat service is available
   */
  async checkServiceHealth(): Promise<boolean> {
    try {
      const response = await api.get('/api/chat/health');
      return response.status === 200;
      
    } catch (error) {
      return false;
    }
  }
  
  // Private helper methods
  
  private loadConversationStorage(): ConversationStorage {
    try {
      // Try localStorage first, fall back to sessionStorage
      const stored = localStorage.getItem(this.STORAGE_KEY) || 
                   sessionStorage.getItem(this.STORAGE_KEY);
      
      if (stored) {
        return JSON.parse(stored);
      }
      
    } catch (error) {
      logger.error('Error parsing conversation storage:', error);
    }
    
    // Return empty storage if none exists or parsing fails
    return {
      conversations: {},
      maxConversationsPerProfile: this.MAX_CONVERSATIONS_PER_PROFILE,
      maxMessagesPerConversation: this.MAX_MESSAGES_PER_CONVERSATION
    };
  }
  
  private saveConversationStorage(storage: ConversationStorage): void {
    try {
      const serialized = JSON.stringify(storage);
      
      // Save to both localStorage and sessionStorage for persistence
      localStorage.setItem(this.STORAGE_KEY, serialized);
      sessionStorage.setItem(this.STORAGE_KEY, serialized);
      
    } catch (error) {
      // Handle storage quota exceeded
      if (error instanceof DOMException && error.code === 22) {
        this.cleanupOldConversations();
        // Try saving again after cleanup
        try {
          const serialized = JSON.stringify(storage);
          localStorage.setItem(this.STORAGE_KEY, serialized);
        } catch (retryError) {
          logger.error('Storage still full after cleanup:', retryError);
        }
      } else {
        logger.error('Error saving conversation storage:', error);
      }
    }
  }
  
  private cleanupOldConversations(): void {
    try {
      const storage = this.loadConversationStorage();
      
      // Sort conversations by last updated date
      const sortedConversations = Object.entries(storage.conversations)
        .sort(([, a], [, b]) => new Date(b.lastUpdated).getTime() - new Date(a.lastUpdated).getTime());
      
      // Keep only the most recent conversations per profile
      const cleanedConversations: { [profileId: string]: ConversationHistory } = {};
      
      for (const [profileId, conversation] of sortedConversations) {
        cleanedConversations[profileId] = {
          ...conversation,
          messages: conversation.messages.slice(-50) // Keep last 50 messages
        };
      }
      
      storage.conversations = cleanedConversations;
      this.saveConversationStorage(storage);
      
    } catch (error) {
      logger.error('Error cleaning up conversations:', error);
    }
  }
  
  private generateMessageId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
  
  private categorizeError(error: any): ChatError['type'] {
    if (error.response?.status === 429) return 'rate_limit';
    if (error.response?.status >= 400 && error.response?.status < 500) return 'validation_error';
    if (!error.response && error.message?.includes('Network')) return 'network_error';
    if (error.message?.includes('cache')) return 'cache_error';
    return 'api_error';
  }
  
  private getErrorMessage(error: any): string {
    if (error.response?.data?.detail) return error.response.data.detail;
    if (error.message) return error.message;
    return 'An unexpected error occurred';
  }
  
  private isRetryableError(error: any): boolean {
    const status = error.response?.status;
    return !status || status >= 500 || status === 429 || this.categorizeError(error) === 'network_error';
  }
}

// Export singleton instance
export const chatService = new ChatService();
export default chatService; 