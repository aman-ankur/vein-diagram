/**
 * Tests for useChat hook
 */
import { renderHook, act } from '@testing-library/react';
import { useChat } from '../useChat';
import { chatService } from '../../services/chatService';
import { ChatResponse, ChatSuggestionsResponse } from '../../types/chat';

// Mock the chat service
jest.mock('../../services/chatService');
const mockChatService = chatService as jest.Mocked<typeof chatService>;

// Mock ProfileContext
const mockProfileContext = {
  activeProfile: {
    id: 'test-profile-123',
    name: 'Test User',
    biomarkers: [
      {
        name: 'Glucose',
        value: 110.0,
        unit: 'mg/dL',
        referenceRange: '70-99',
        isAbnormal: true,
        isFavorite: true,
      },
    ],
  },
  profiles: [],
  setActiveProfile: jest.fn(),
  addProfile: jest.fn(),
  updateProfile: jest.fn(),
  deleteProfile: jest.fn(),
};

// Mock React context
jest.mock('react', () => ({
  ...jest.requireActual('react'),
  useContext: () => mockProfileContext,
}));

describe('useChat', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockChatService.loadConversation.mockReturnValue([]);
    mockChatService.loadSessionState.mockReturnValue(null);
  });

  describe('Initialization', () => {
    it('should initialize with default state', () => {
      const { result } = renderHook(() => useChat());

      expect(result.current.isOpen).toBe(false);
      expect(result.current.messages).toEqual([]);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.suggestions).toEqual([]);
      expect(result.current.welcomeMessage).toBe('');
    });

    it('should load existing conversation on mount', () => {
      const existingConversation = [
        {
          role: 'user' as const,
          content: 'Hello',
          timestamp: '2023-01-01T10:00:00Z',
        },
        {
          role: 'assistant' as const,
          content: 'Hi! How can I help you?',
          timestamp: '2023-01-01T10:00:01Z',
        },
      ];

      mockChatService.loadConversation.mockReturnValue(existingConversation);

      const { result } = renderHook(() => useChat());

      expect(result.current.messages).toEqual(existingConversation);
      expect(mockChatService.loadConversation).toHaveBeenCalledWith('test-profile-123');
    });

    it('should restore session state on mount', () => {
      const sessionState = {
        isOpen: true,
        lastActiveProfile: 'test-profile-123',
        pendingMessage: 'test message',
      };

      mockChatService.loadSessionState.mockReturnValue(sessionState);

      const { result } = renderHook(() => useChat());

      expect(result.current.isOpen).toBe(true);
    });
  });

  describe('Chat Operations', () => {
    it('should open chat and load suggestions', async () => {
      const mockSuggestions: ChatSuggestionsResponse = {
        suggestions: [
          {
            question: 'What does my high glucose mean?',
            category: 'abnormal',
            priority: 1,
          },
        ],
        welcomeMessage: 'Hello! I can help you understand your biomarkers.',
      };

      mockChatService.getSuggestions.mockResolvedValue(mockSuggestions);

      const { result } = renderHook(() => useChat());

      await act(async () => {
        await result.current.openChat();
      });

      expect(result.current.isOpen).toBe(true);
      expect(result.current.suggestions).toEqual(mockSuggestions.suggestions);
      expect(result.current.welcomeMessage).toBe(mockSuggestions.welcomeMessage);
      expect(mockChatService.getSuggestions).toHaveBeenCalledWith('test-profile-123');
    });

    it('should close chat and save session state', () => {
      const { result } = renderHook(() => useChat());

      act(() => {
        result.current.closeChat();
      });

      expect(result.current.isOpen).toBe(false);
      expect(mockChatService.saveSessionState).toHaveBeenCalledWith({
        isOpen: false,
        lastActiveProfile: 'test-profile-123',
        pendingMessage: '',
      });
    });

    it('should send message successfully', async () => {
      const mockResponse: ChatResponse = {
        response: 'Based on your glucose level, I recommend reducing refined carbohydrates.',
        biomarkerReferences: [
          {
            name: 'Glucose',
            value: 110.0,
            unit: 'mg/dL',
            referenceRange: '70-99',
            isAbnormal: true,
          },
        ],
        suggestedFollowUps: ['What specific foods should I avoid?'],
        responseId: 'response-123',
        isFromCache: false,
        tokenUsage: 150,
        responseTimeMs: 1200,
      };

      mockChatService.sendMessage.mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useChat());

      await act(async () => {
        await result.current.sendMessage('What can I do to improve my glucose?');
      });

      expect(result.current.messages).toHaveLength(2); // User message + assistant response
      expect(result.current.messages[0]).toEqual({
        role: 'user',
        content: 'What can I do to improve my glucose?',
        timestamp: expect.any(String),
      });
      expect(result.current.messages[1]).toEqual({
        role: 'assistant',
        content: mockResponse.response,
        timestamp: expect.any(String),
        responseId: mockResponse.responseId,
        biomarkerReferences: mockResponse.biomarkerReferences,
        suggestedFollowUps: mockResponse.suggestedFollowUps,
      });

      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('should handle send message error', async () => {
      const errorMessage = 'Network error';
      mockChatService.sendMessage.mockRejectedValue(new Error(errorMessage));

      const { result } = renderHook(() => useChat());

      await act(async () => {
        await result.current.sendMessage('Test message');
      });

      expect(result.current.error).toBe(errorMessage);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.messages).toHaveLength(1); // Only user message
    });

    it('should not send empty messages', async () => {
      const { result } = renderHook(() => useChat());

      await act(async () => {
        await result.current.sendMessage('');
      });

      expect(mockChatService.sendMessage).not.toHaveBeenCalled();
      expect(result.current.messages).toHaveLength(0);
    });

    it('should not send messages while loading', async () => {
      mockChatService.sendMessage.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 1000))
      );

      const { result } = renderHook(() => useChat());

      // Start first message
      act(() => {
        result.current.sendMessage('First message');
      });

      expect(result.current.isLoading).toBe(true);

      // Try to send second message while loading
      await act(async () => {
        await result.current.sendMessage('Second message');
      });

      expect(mockChatService.sendMessage).toHaveBeenCalledTimes(1);
    });
  });

  describe('Feedback Operations', () => {
    it('should submit feedback successfully', async () => {
      mockChatService.submitFeedback.mockResolvedValue({
        success: true,
        message: 'Thank you for your feedback',
      });

      const { result } = renderHook(() => useChat());

      await act(async () => {
        await result.current.submitFeedback('response-123', true, 'accuracy');
      });

      expect(mockChatService.submitFeedback).toHaveBeenCalledWith({
        responseId: 'response-123',
        isHelpful: true,
        feedbackType: 'accuracy',
      });
    });

    it('should handle feedback submission error', async () => {
      mockChatService.submitFeedback.mockRejectedValue(new Error('Feedback error'));

      const { result } = renderHook(() => useChat());

      await act(async () => {
        await result.current.submitFeedback('response-123', true);
      });

      expect(result.current.error).toBe('Feedback error');
    });
  });

  describe('Conversation Management', () => {
    it('should clear conversation', async () => {
      // Set up initial conversation
      const { result } = renderHook(() => useChat());

      await act(async () => {
        await result.current.sendMessage('Test message');
      });

      // Clear conversation
      await act(async () => {
        await result.current.clearConversation();
      });

      expect(result.current.messages).toEqual([]);
      expect(mockChatService.clearConversation).toHaveBeenCalledWith('test-profile-123');
    });

    it('should retry last message', async () => {
      const mockResponse: ChatResponse = {
        response: 'Retry response',
        responseId: 'retry-123',
        isFromCache: false,
        tokenUsage: 100,
        responseTimeMs: 800,
      };

      mockChatService.sendMessage.mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useChat());

      // Send initial message
      await act(async () => {
        await result.current.sendMessage('Test message');
      });

      const initialMessageCount = result.current.messages.length;

      // Retry last message
      await act(async () => {
        await result.current.retryLastMessage();
      });

      expect(result.current.messages).toHaveLength(initialMessageCount + 1);
      expect(result.current.messages[result.current.messages.length - 1].content).toBe(
        'Retry response'
      );
    });

    it('should not retry when no messages exist', async () => {
      const { result } = renderHook(() => useChat());

      await act(async () => {
        await result.current.retryLastMessage();
      });

      expect(mockChatService.sendMessage).not.toHaveBeenCalled();
    });

    it('should save conversation after each message', async () => {
      const mockResponse: ChatResponse = {
        response: 'Test response',
        responseId: 'test-123',
        isFromCache: false,
        tokenUsage: 100,
        responseTimeMs: 500,
      };

      mockChatService.sendMessage.mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useChat());

      await act(async () => {
        await result.current.sendMessage('Test message');
      });

      expect(mockChatService.saveConversation).toHaveBeenCalledWith(
        'test-profile-123',
        expect.arrayContaining([
          expect.objectContaining({ role: 'user', content: 'Test message' }),
          expect.objectContaining({ role: 'assistant', content: 'Test response' }),
        ])
      );
    });
  });

  describe('Profile Context Integration', () => {
    it('should prepare biomarker context from active profile', async () => {
      const mockResponse: ChatResponse = {
        response: 'Test response',
        responseId: 'test-123',
        isFromCache: false,
        tokenUsage: 100,
        responseTimeMs: 500,
      };

      mockChatService.sendMessage.mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useChat());

      await act(async () => {
        await result.current.sendMessage('Test message');
      });

      expect(mockChatService.sendMessage).toHaveBeenCalledWith({
        message: 'Test message',
        profileId: 'test-profile-123',
        conversationHistory: [],
        biomarkerContext: {
          relevantBiomarkers: [
            {
              name: 'Glucose',
              value: 110.0,
              unit: 'mg/dL',
              referenceRange: '70-99',
              isAbnormal: true,
              isFavorite: true,
            },
          ],
        },
      });
    });

    it('should handle missing active profile', () => {
      // Mock no active profile
      const mockEmptyProfileContext = {
        ...mockProfileContext,
        activeProfile: null,
      };

      jest.mocked(require('react').useContext).mockReturnValue(mockEmptyProfileContext);

      const { result } = renderHook(() => useChat());

      expect(result.current.isOpen).toBe(false);
      // Should not crash or throw errors
    });

    it('should reload conversation when profile changes', () => {
      const { result, rerender } = renderHook(() => useChat());

      // Change active profile
      mockProfileContext.activeProfile = {
        id: 'new-profile-456',
        name: 'New User',
        biomarkers: [],
      };

      rerender();

      expect(mockChatService.loadConversation).toHaveBeenCalledWith('new-profile-456');
    });
  });

  describe('Usage Metrics', () => {
    it('should get usage metrics', async () => {
      const mockUsageMetrics = {
        dailyApiCalls: 5,
        dailyTokens: 750,
        cacheHitRate: 20.0,
        lastUpdated: '2023-01-01T12:00:00Z',
      };

      mockChatService.getUsageMetrics.mockResolvedValue(mockUsageMetrics);

      const { result } = renderHook(() => useChat());

      await act(async () => {
        await result.current.getUsageMetrics();
      });

      expect(result.current.usageMetrics).toEqual(mockUsageMetrics);
      expect(mockChatService.getUsageMetrics).toHaveBeenCalledWith('test-profile-123');
    });

    it('should handle usage metrics error', async () => {
      mockChatService.getUsageMetrics.mockRejectedValue(new Error('Metrics error'));

      const { result } = renderHook(() => useChat());

      await act(async () => {
        await result.current.getUsageMetrics();
      });

      expect(result.current.error).toBe('Metrics error');
      expect(result.current.usageMetrics).toBeNull();
    });
  });

  describe('Health Check', () => {
    it('should check service health', async () => {
      const mockHealthResponse = {
        status: 'healthy',
        service: 'chat',
        timestamp: '2023-01-01T12:00:00Z',
      };

      mockChatService.checkHealth.mockResolvedValue(mockHealthResponse);

      const { result } = renderHook(() => useChat());

      await act(async () => {
        await result.current.checkHealth();
      });

      expect(result.current.isHealthy).toBe(true);
      expect(mockChatService.checkHealth).toHaveBeenCalled();
    });

    it('should handle health check failure', async () => {
      mockChatService.checkHealth.mockRejectedValue(new Error('Health check failed'));

      const { result } = renderHook(() => useChat());

      await act(async () => {
        await result.current.checkHealth();
      });

      expect(result.current.isHealthy).toBe(false);
      expect(result.current.error).toBe('Health check failed');
    });
  });

  describe('Error Handling', () => {
    it('should clear errors', () => {
      const { result } = renderHook(() => useChat());

      // Set an error
      act(() => {
        result.current.sendMessage('Test').catch(() => {});
      });

      // Clear error
      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBeNull();
    });

    it('should handle multiple concurrent errors', async () => {
      mockChatService.sendMessage.mockRejectedValue(new Error('First error'));
      mockChatService.getSuggestions.mockRejectedValue(new Error('Second error'));

      const { result } = renderHook(() => useChat());

      await act(async () => {
        await Promise.allSettled([
          result.current.sendMessage('Test message'),
          result.current.openChat(),
        ]);
      });

      // Should show the most recent error
      expect(result.current.error).toBeTruthy();
    });
  });

  describe('Cleanup', () => {
    it('should cleanup on unmount', () => {
      const { unmount } = renderHook(() => useChat());

      unmount();

      expect(mockChatService.saveSessionState).toHaveBeenCalled();
    });

    it('should cleanup old conversations periodically', () => {
      renderHook(() => useChat());

      expect(mockChatService.cleanupOldConversations).toHaveBeenCalled();
    });
  });
}); 