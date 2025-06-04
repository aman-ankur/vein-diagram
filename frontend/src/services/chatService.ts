/**
 * Chat service for handling Biomarker Insights Chatbot API communication
 * and conversation persistence using localStorage/sessionStorage.
 */
import { 
  ChatMessage, ChatRequest, ChatResponse, 
  ChatSuggestionsResponse,
  ChatFeedback, BiomarkerContext, UsageMetrics, ChatError
} from '../types/chat';
import { Biomarker } from '../types/pdf';
import api from './api';
import { logger } from '../utils/logger';

class ChatService {
  private readonly MAX_MESSAGES_PER_CONVERSATION = 100;
  
  /**
   * Send a chat message and get AI response
   */
  async sendMessage(
    messageOrRequest: string | ChatRequest,
    profileId?: string,
    biomarkerContext?: BiomarkerContext
  ): Promise<ChatResponse> {
    try {
      let request: ChatRequest;
      
      // Handle both single object parameter and multiple parameters
      if (typeof messageOrRequest === 'string') {
        if (!profileId) {
          throw new Error('profileId is required when message is passed as string');
        }
        request = {
          message: messageOrRequest.trim(),
          profileId,
          biomarkerContext
        };
      } else {
        request = messageOrRequest;
      }
      
      // Get recent conversation history for context
      const conversationHistory = this.getConversationHistory(request.profileId);
      const recentMessages = conversationHistory.slice(-10); // Last 10 messages for API context
      
      // Add conversation history if not already provided
      if (!request.conversationHistory) {
        request.conversationHistory = recentMessages;
      }
      
      // Validate message length
      if (request.message.length === 0 || request.message.length > 1000) {
        throw new Error('Message must be between 1 and 1000 characters');
      }
      
      const response = await api.post<ChatResponse>('/api/chat', request);
      
      // Store both user message and AI response in conversation history
      this.addMessagesToHistory(request.profileId, [
        {
          id: this.generateMessageId(),
          role: 'user',
          content: request.message,
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
        logger.info('Chat interaction', {
          action: 'message_sent',
          profileId: request.profileId,
          messageLength: request.message.length,
          isFromCache: response.data.isFromCache,
          tokenUsage: response.data.tokenUsage,
          responseTime: response.data.responseTimeMs
        });
      } catch (logError) {
        console.log('Chat interaction logged:', {
          action: 'message_sent',
          profileId: request.profileId,
          messageLength: request.message.length,
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
        logger.info('Chat suggestions fetched', {
          profileId,
          suggestionsCount: response.data.suggestions.length
        });
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
        logger.info('Chat feedback submitted', {
          responseId: feedback.responseId,
          isHelpful: feedback.isHelpful,
          feedbackType: feedback.feedbackType
        });
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
   * Check service health
   */
  async checkHealth(): Promise<any> {
    try {
      const response = await api.get('/api/chat/health');
      return response.data;
    } catch (error: any) {
      logger.error('Health check error:', error);
      throw new Error('Health check failed');
    }
  }
  
  /**
   * Get conversation history for a profile
   */
  getConversationHistory(profileId: string): ChatMessage[] {
    return this.loadConversation(profileId);
  }
  
  /**
   * Add messages to conversation history
   */
  addMessagesToHistory(profileId: string, messages: ChatMessage[]): void {
    try {
      const existing = this.loadConversation(profileId);
      const updated = [...existing, ...messages];
      
      // Keep only the latest messages (limit per conversation)
      const limited = updated.slice(-this.MAX_MESSAGES_PER_CONVERSATION);
      
      this.saveConversation(profileId, limited);
      
      // Log conversation update (with fallback)
      try {
        logger.info('Conversation updated', {
          profileId,
          messageCount: messages.length,
          totalMessages: limited.length
        });
      } catch (logError) {
        console.log('Conversation updated for profile:', profileId, 'Added:', messages.length);
      }
      
    } catch (error) {
      logger.error('Error adding messages to history:', error);
    }
  }
  
  /**
   * Clear conversation history via API
   */
  async clearConversationHistory(profileId: string): Promise<boolean> {
    try {
      await api.delete(`/api/chat/history/${profileId}`);
      return true;
    } catch (error: any) {
      logger.error('Clear conversation history error:', error);
      return false;
    }
  }
  
  /**
   * Clear all conversation history for all profiles
   */
  clearAllConversations(): void {
    try {
      // Find all chat conversation keys and remove them
      const keys = [];
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith('chat_conversation_')) {
          keys.push(key);
        }
      }
      
      keys.forEach(key => localStorage.removeItem(key));
      
      // Log conversation clear (with fallback)
      try {
        logger.info('All conversations cleared', { count: keys.length });
      } catch (logError) {
        console.log('All conversations cleared:', keys.length);
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
   * Save conversation to localStorage
   */
  saveConversation(profileId: string, messages: ChatMessage[]): void {
    try {
      localStorage.setItem(`chat_conversation_${profileId}`, JSON.stringify(messages));
    } catch (error) {
      logger.error('Error saving conversation:', error);
    }
  }
  
  /**
   * Load conversation from localStorage
   */
  loadConversation(profileId: string): ChatMessage[] {
    try {
      const stored = localStorage.getItem(`chat_conversation_${profileId}`);
      return stored ? JSON.parse(stored) : [];
    } catch (error) {
      logger.error('Error loading conversation:', error);
      return [];
    }
  }
  
  /**
   * Clear conversation from localStorage
   */
  clearConversation(profileId: string): void {
    try {
      localStorage.removeItem(`chat_conversation_${profileId}`);
    } catch (error) {
      logger.error('Error clearing conversation:', error);
    }
  }
  
  /**
   * Save session state to sessionStorage
   */
  saveSessionState(state: any): void {
    try {
      sessionStorage.setItem('chat_session_state', JSON.stringify(state));
    } catch (error) {
      logger.error('Error saving session state:', error);
    }
  }
  
  /**
   * Load session state from sessionStorage
   */
  loadSessionState(): any {
    try {
      const stored = sessionStorage.getItem('chat_session_state');
      return stored ? JSON.parse(stored) : null;
    } catch (error) {
      logger.error('Error loading session state:', error);
      return null;
    }
  }
  
  // Private helper methods
  
  /**
   * Cleanup old conversations (make public)
   */
  cleanupOldConversations(): void {
    try {
      const maxAge = 30 * 24 * 60 * 60 * 1000; // 30 days
      const now = Date.now();
      
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith('chat_conversation_')) {
          try {
            const stored = localStorage.getItem(key);
            if (stored) {
              const messages: ChatMessage[] = JSON.parse(stored);
              if (messages.length > 0) {
                const lastMessage = messages[messages.length - 1];
                const lastMessageTime = new Date(lastMessage.timestamp).getTime();
                if (now - lastMessageTime > maxAge) {
                  localStorage.removeItem(key);
                }
              }
            }
          } catch (error) {
            // If we can't parse the conversation, remove it
            localStorage.removeItem(key);
          }
        }
      }
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