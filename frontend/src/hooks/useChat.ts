/**
 * Custom hook for managing chat state and interactions
 */
import { useState, useEffect, useCallback, useMemo } from 'react';
import { 
  ChatMessage, ChatState, SuggestedQuestion, 
  BiomarkerContext, ChatError, UsageMetrics 
} from '../types/chat';
import { Biomarker } from '../types/pdf';
import { chatService } from '../services/chatService';
import { useProfile } from '../contexts/ProfileContext';
import { logger } from '../utils/logger';

interface UseChatProps {
  /** Whether to auto-load suggestions on mount */
  autoLoadSuggestions?: boolean;
  /** Whether to enable usage metrics tracking */
  trackUsage?: boolean;
}

interface UseChatReturn {
  // Chat state (individual properties, not nested)
  isOpen: boolean;
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  suggestions: SuggestedQuestion[];
  welcomeMessage: string;
  usageMetrics: UsageMetrics | null;
  isHealthy: boolean;
  
  // Actions
  sendMessage: (message: string, biomarkerContext?: BiomarkerContext) => Promise<void>;
  clearConversation: () => void;
  toggleChat: () => void;
  openChat: () => void;
  closeChat: () => void;
  clearError: () => void;
  
  // Feedback
  submitFeedback: (responseId: string, isHelpful: boolean, feedbackType?: string, comment?: string) => Promise<void>;
  
  // Data
  loadSuggestions: () => Promise<void>;
  prepareBiomarkerContext: (biomarkers: Biomarker[], favoriteBiomarkers?: string[]) => BiomarkerContext;
  getUsageMetrics: () => Promise<void>;
  checkHealth: () => Promise<void>;
  
  // Utilities
  retryLastMessage: () => Promise<void>;
  canRetry: boolean;
}

export const useChat = ({ 
  autoLoadSuggestions = true, 
  trackUsage = false 
}: UseChatProps = {}): UseChatReturn => {
  
  const { activeProfile } = useProfile();
  
  // Core chat state
  const [chatState, setChatState] = useState<ChatState>({
    isOpen: false,
    messages: [],
    isLoading: false,
    error: null,
    suggestedQuestions: [],
    usageMetrics: undefined
  });
  
  // Service health state
  const [isServiceHealthy, setIsServiceHealthy] = useState(true);
  
  // Last message for retry functionality
  const [lastMessage, setLastMessage] = useState<{
    message: string;
    biomarkerContext?: BiomarkerContext;
  } | null>(null);
  
  // Load conversation history when profile changes
  useEffect(() => {
    if (activeProfile?.id) {
      const messages = chatService.getConversationHistory(activeProfile.id);
      setChatState(prev => ({
        ...prev,
        messages,
        error: null
      }));
      
      // Auto-load suggestions if enabled
      if (autoLoadSuggestions) {
        loadSuggestions();
      }
      
      // Load usage metrics if enabled
      if (trackUsage) {
        loadUsageMetrics();
      }
    }
  }, [activeProfile?.id, autoLoadSuggestions, trackUsage]);
  
  // Check service health on mount
  useEffect(() => {
    checkServiceHealth();
  }, []);
  
  const checkServiceHealth = useCallback(async () => {
    try {
      await chatService.checkHealth();
      setIsServiceHealthy(true);
    } catch (error) {
      setIsServiceHealthy(false);
    }
  }, []);
  
  const loadSuggestions = useCallback(async () => {
    if (!activeProfile?.id) return;
    
    try {
      const suggestions = await chatService.getSuggestions(activeProfile.id);
      setChatState(prev => ({
        ...prev,
        suggestedQuestions: suggestions.suggestions,
        error: null
      }));
    } catch (error: any) {
      logger.error('Failed to load chat suggestions:', error);
      // Don't set error state for suggestions - they're not critical
    }
  }, [activeProfile?.id]);
  
  const loadUsageMetrics = useCallback(async () => {
    if (!activeProfile?.id || !trackUsage) return;
    
    try {
      const metrics = await chatService.getUsageMetrics(activeProfile.id);
      setChatState(prev => ({
        ...prev,
        usageMetrics: metrics || undefined
      }));
    } catch (error: any) {
      logger.error('Failed to load usage metrics:', error);
      // Don't set error state for metrics - they're not critical
    }
  }, [activeProfile?.id, trackUsage]);
  
  const sendMessage = useCallback(async (
    message: string, 
    biomarkerContext?: BiomarkerContext
  ) => {
    if (!activeProfile?.id) {
      setChatState(prev => ({
        ...prev,
        error: 'No active profile selected'
      }));
      return;
    }
    
    if (!message.trim()) {
      setChatState(prev => ({
        ...prev,
        error: 'Message cannot be empty'
      }));
      return;
    }
    
    // Store for retry functionality
    setLastMessage({ message, biomarkerContext });
    
    setChatState(prev => ({
      ...prev,
      isLoading: true,
      error: null
    }));
    
    try {
      const response = await chatService.sendMessage(
        message, 
        activeProfile.id, 
        biomarkerContext
      );
      
      // Reload conversation history from storage
      const updatedMessages = chatService.getConversationHistory(activeProfile.id);
      
      setChatState(prev => ({
        ...prev,
        messages: updatedMessages,
        isLoading: false,
        error: null
      }));
      
      // Update usage metrics if tracking is enabled
      if (trackUsage) {
        loadUsageMetrics();
      }
      
      // Check for follow-up suggestions
      if (response.suggestedFollowUps && response.suggestedFollowUps.length > 0) {
        const followUpSuggestions: SuggestedQuestion[] = response.suggestedFollowUps.map((q, index) => ({
          question: q,
          category: "general",
          priority: index + 5
        }));
        
        setChatState(prev => ({
          ...prev,
          suggestedQuestions: followUpSuggestions
        }));
      }
      
    } catch (error: any) {
      const chatError = error as ChatError;
      
      setChatState(prev => ({
        ...prev,
        isLoading: false,
        error: chatError.message || 'Failed to send message'
      }));
      
      // Check service health if there was an error
      if (chatError.type === 'network_error' || chatError.type === 'api_error') {
        checkServiceHealth();
      }
      
      logger.error('Chat send message error:', error);
    }
  }, [activeProfile?.id, trackUsage, loadUsageMetrics, checkServiceHealth]);
  
  const retryLastMessage = useCallback(async () => {
    if (!lastMessage) return;
    
    await sendMessage(lastMessage.message, lastMessage.biomarkerContext);
  }, [lastMessage, sendMessage]);
  
  const clearConversation = useCallback(() => {
    if (!activeProfile?.id) return;
    
    try {
      chatService.clearConversationHistory(activeProfile.id);
      setChatState(prev => ({
        ...prev,
        messages: [],
        error: null
      }));
      
      // Reload suggestions after clearing
      loadSuggestions();
      
    } catch (error: any) {
      logger.error('Failed to clear conversation:', error);
      setChatState(prev => ({
        ...prev,
        error: 'Failed to clear conversation'
      }));
    }
  }, [activeProfile?.id, loadSuggestions]);
  
  const submitFeedback = useCallback(async (
    responseId: string,
    isHelpful: boolean,
    feedbackType?: string,
    comment?: string
  ) => {
    try {
      await chatService.submitFeedback({
        responseId,
        isHelpful,
        feedbackType: feedbackType as "accuracy" | "clarity" | "completeness" | "actionability" | undefined,
        comment
      });
    } catch (error: any) {
      logger.error('Failed to submit feedback:', error);
      // Don't show error to user for feedback - it's not critical
    }
  }, []);
  
  const prepareBiomarkerContext = useCallback((
    biomarkers: Biomarker[],
    favoriteBiomarkers: string[] = []
  ): BiomarkerContext => {
    return chatService.prepareBiomarkerContext(biomarkers, favoriteBiomarkers);
  }, []);
  
  // Chat window controls
  const toggleChat = useCallback(() => {
    setChatState(prev => ({
      ...prev,
      isOpen: !prev.isOpen
    }));
  }, []);
  
  const openChat = useCallback(() => {
    setChatState(prev => ({
      ...prev,
      isOpen: true
    }));
  }, []);
  
  const closeChat = useCallback(() => {
    setChatState(prev => ({
      ...prev,
      isOpen: false
    }));
  }, []);
  
  const clearError = useCallback(() => {
    setChatState(prev => ({
      ...prev,
      error: null
    }));
  }, []);
  
  // Computed values
  const canRetry = useMemo(() => {
    return lastMessage !== null && !chatState.isLoading && chatState.error !== null;
  }, [lastMessage, chatState.isLoading, chatState.error]);
  
  return {
    isOpen: chatState.isOpen,
    messages: chatState.messages,
    isLoading: chatState.isLoading,
    error: chatState.error,
    suggestions: chatState.suggestedQuestions,
    welcomeMessage: '',
    usageMetrics: chatState.usageMetrics || null,
    isHealthy: isServiceHealthy,
    sendMessage,
    clearConversation,
    toggleChat,
    openChat,
    closeChat,
    clearError,
    submitFeedback,
    loadSuggestions,
    prepareBiomarkerContext,
    getUsageMetrics: loadUsageMetrics,
    checkHealth: checkServiceHealth,
    retryLastMessage,
    canRetry
  };
}; 