/**
 * Tests for chat service functionality
 */
import { chatService } from '../chatService';
import { ChatRequest, ChatResponse, ChatSuggestionsResponse, UsageMetrics } from '../../types/chat';

// Mock fetch globally
global.fetch = jest.fn();

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

// Mock sessionStorage
const mockSessionStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'sessionStorage', {
  value: mockSessionStorage,
});

describe('ChatService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (fetch as jest.Mock).mockClear();
    mockLocalStorage.getItem.mockClear();
    mockLocalStorage.setItem.mockClear();
    mockSessionStorage.getItem.mockClear();
    mockSessionStorage.setItem.mockClear();
  });

  describe('sendMessage', () => {
    const mockChatRequest: ChatRequest = {
      message: 'What can I do to improve my glucose levels?',
      profileId: 'test-profile-123',
      conversationHistory: [
        {
          id: 'msg-1',
          role: 'user',
          content: 'Hello',
          timestamp: '2023-01-01T10:00:00Z',
        },
      ],
      biomarkerContext: {
        relevantBiomarkers: [
          {
            name: 'Glucose',
            value: 110.0,
            unit: 'mg/dL',
            reference_range: '70-99',
            is_abnormal: true,
            trend: 'worsened',
            isFavorite: true,
          },
        ],
      },
    };

    const mockChatResponse: ChatResponse = {
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
      suggestedFollowUps: [
        'What specific foods should I avoid?',
        'How much exercise do I need?',
      ],
      sources: ['American Diabetes Association'],
      responseId: 'response-123',
      isFromCache: false,
      tokenUsage: 150,
      responseTimeMs: 1200,
    };

    it('should send message successfully', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockChatResponse,
      });

      const result = await chatService.sendMessage(mockChatRequest);

      expect(fetch).toHaveBeenCalledWith('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: mockChatRequest.message,
          profile_id: mockChatRequest.profileId,
          conversation_history: mockChatRequest.conversationHistory,
          biomarker_context: {
            relevant_biomarkers: mockChatRequest.biomarkerContext?.relevantBiomarkers,
            health_score_context: mockChatRequest.biomarkerContext?.healthScoreContext,
          },
        }),
      });

      expect(result).toEqual(mockChatResponse);
    });

    it('should handle API error responses', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ error: 'Internal server error' }),
      });

      await expect(chatService.sendMessage(mockChatRequest)).rejects.toThrow(
        'Chat request failed: Internal server error'
      );
    });

    it('should handle network errors', async () => {
      (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      await expect(chatService.sendMessage(mockChatRequest)).rejects.toThrow(
        'Network error occurred while sending message'
      );
    });

    it('should handle minimal request without optional fields', async () => {
      const minimalRequest: ChatRequest = {
        message: 'Hello',
        profileId: 'test-profile-123',
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockChatResponse,
      });

      await chatService.sendMessage(minimalRequest);

      expect(fetch).toHaveBeenCalledWith('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: 'Hello',
          profile_id: 'test-profile-123',
          conversation_history: undefined,
          biomarker_context: undefined,
        }),
      });
    });
  });

  describe('getSuggestions', () => {
    const mockSuggestions: ChatSuggestionsResponse = {
      suggestions: [
        {
          question: 'What does my high glucose mean?',
          category: 'abnormal',
          priority: 1,
        },
        {
          question: 'How can I improve my HDL?',
          category: 'favorites',
          priority: 2,
        },
      ],
      welcomeMessage: 'Hello! I can help you understand your biomarker results.',
    };

    it('should get suggestions successfully', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockSuggestions,
      });

      const result = await chatService.getSuggestions('test-profile-123');

      expect(fetch).toHaveBeenCalledWith('/api/chat/suggestions/test-profile-123');
      expect(result).toEqual(mockSuggestions);
    });

    it('should handle suggestions API error', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ error: 'Profile not found' }),
      });

      await expect(chatService.getSuggestions('invalid-profile')).rejects.toThrow(
        'Failed to get suggestions: Profile not found'
      );
    });
  });

  describe('submitFeedback', () => {
    const feedbackRequest = {
      responseId: 'response-123',
      isHelpful: true,
      feedbackType: 'accuracy' as const,
      comment: 'Very helpful response',
    };

    it('should submit feedback successfully', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, message: 'Thank you for your feedback' }),
      });

      const result = await chatService.submitFeedback(feedbackRequest);

      expect(fetch).toHaveBeenCalledWith('/api/chat/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          response_id: feedbackRequest.responseId,
          is_helpful: feedbackRequest.isHelpful,
          feedback_type: feedbackRequest.feedbackType,
          comment: feedbackRequest.comment,
        }),
      });

      expect(result).toEqual({ success: true, message: 'Thank you for your feedback' });
    });

    it('should handle feedback submission error', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ error: 'Invalid feedback data' }),
      });

      await expect(chatService.submitFeedback(feedbackRequest)).rejects.toThrow(
        'Failed to submit feedback: Invalid feedback data'
      );
    });
  });

  describe('getUsageMetrics', () => {
    const mockUsageMetrics: UsageMetrics = {
      dailyApiCalls: 10,
      dailyTokens: 1500,
      cacheHitRate: 0.3,
      averageResponseTime: 850,
      date: '2023-01-01',
      lastUpdated: '2023-01-01T12:00:00Z'
    };

    it('should get usage metrics successfully', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUsageMetrics,
      });

      const result = await chatService.getUsageMetrics('test-profile-123');

      expect(fetch).toHaveBeenCalledWith('/api/chat/usage/test-profile-123');
      expect(result).toEqual(mockUsageMetrics);
    });

    it('should return null when no usage data exists', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'No usage data found' }),
      });

      const result = await chatService.getUsageMetrics('test-profile-123');
      expect(result).toBeNull();
    });
  });

  describe('clearConversationHistory', () => {
    it('should clear conversation history successfully', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, message: 'Conversation history cleared' }),
      });

      const result = await chatService.clearConversationHistory('test-profile-123');

      expect(fetch).toHaveBeenCalledWith('/api/chat/history/test-profile-123', {
        method: 'DELETE',
      });

      expect(result).toBe(true);
    });

    it('should handle clear history failure', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Failed to clear conversation history' }),
      });

      const result = await chatService.clearConversationHistory('test-profile-123');
      expect(result).toBe(false);
    });
  });

  describe('checkHealth', () => {
    it('should check service health successfully', async () => {
      const mockHealthResponse = {
        status: 'healthy',
        service: 'chat',
        timestamp: '2023-01-01T12:00:00Z',
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockHealthResponse,
      });

      const result = await chatService.checkHealth();

      expect(fetch).toHaveBeenCalledWith('/api/chat/health');
      expect(result).toEqual(mockHealthResponse);
    });

    it('should handle health check failure', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 503,
      });

      await expect(chatService.checkHealth()).rejects.toThrow(
        'Health check failed'
      );
    });
  });

  describe('Conversation Persistence', () => {
    const profileId = 'test-profile-123';
    const mockConversation = [
      {
        id: 'msg-1',
        role: 'user' as const,
        content: 'Hello',
        timestamp: '2023-01-01T10:00:00Z',
      },
      {
        id: 'msg-2',
        role: 'assistant' as const,
        content: 'Hi! How can I help you?',
        timestamp: '2023-01-01T10:00:01Z',
      },
    ];

    describe('saveConversation', () => {
      it('should save conversation to localStorage', () => {
        chatService.saveConversation(profileId, mockConversation);

        expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
          `chat_conversation_${profileId}`,
          JSON.stringify(mockConversation)
        );
      });

      it('should handle localStorage errors gracefully', () => {
        mockLocalStorage.setItem.mockImplementationOnce(() => {
          throw new Error('Storage quota exceeded');
        });

        // Should not throw error
        expect(() => {
          chatService.saveConversation(profileId, mockConversation);
        }).not.toThrow();
      });
    });

    describe('loadConversation', () => {
      it('should load conversation from localStorage', () => {
        mockLocalStorage.getItem.mockReturnValueOnce(JSON.stringify(mockConversation));

        const result = chatService.loadConversation(profileId);

        expect(mockLocalStorage.getItem).toHaveBeenCalledWith(
          `chat_conversation_${profileId}`
        );
        expect(result).toEqual(mockConversation);
      });

      it('should return empty array when no conversation exists', () => {
        mockLocalStorage.getItem.mockReturnValueOnce(null);

        const result = chatService.loadConversation(profileId);

        expect(result).toEqual([]);
      });

      it('should handle corrupted localStorage data', () => {
        mockLocalStorage.getItem.mockReturnValueOnce('invalid json');

        const result = chatService.loadConversation(profileId);

        expect(result).toEqual([]);
      });
    });

    describe('clearConversation', () => {
      it('should clear conversation from localStorage', () => {
        chatService.clearConversation(profileId);

        expect(mockLocalStorage.removeItem).toHaveBeenCalledWith(
          `chat_conversation_${profileId}`
        );
      });
    });

    describe('saveSessionState', () => {
      it('should save session state to sessionStorage', () => {
        const sessionState = {
          isOpen: true,
          lastActiveProfile: profileId,
          pendingMessage: 'test message',
        };

        chatService.saveSessionState(sessionState);

        expect(mockSessionStorage.setItem).toHaveBeenCalledWith(
          'chat_session_state',
          JSON.stringify(sessionState)
        );
      });
    });

    describe('loadSessionState', () => {
      it('should load session state from sessionStorage', () => {
        const sessionState = {
          isOpen: true,
          lastActiveProfile: profileId,
          pendingMessage: 'test message',
        };

        mockSessionStorage.getItem.mockReturnValueOnce(JSON.stringify(sessionState));

        const result = chatService.loadSessionState();

        expect(mockSessionStorage.getItem).toHaveBeenCalledWith('chat_session_state');
        expect(result).toEqual(sessionState);
      });

      it('should return null when no session state exists', () => {
        mockSessionStorage.getItem.mockReturnValueOnce(null);

        const result = chatService.loadSessionState();

        expect(result).toBeNull();
      });
    });
  });

  describe('Storage Cleanup', () => {
    it('should cleanup old conversations', () => {
      const oldDate = new Date();
      oldDate.setDate(oldDate.getDate() - 31); // 31 days ago

      // Mock localStorage with old conversations
      mockLocalStorage.getItem.mockImplementation((key) => {
        if (key.startsWith('chat_conversation_')) {
          return JSON.stringify([
            {
              id: 'old-msg-1',
              role: 'user',
              content: 'Old message',
              timestamp: oldDate.toISOString(),
            },
          ]);
        }
        return null;
      });

      // Mock localStorage.key to simulate stored conversations
      Object.defineProperty(mockLocalStorage, 'length', { value: 2 });
      Object.defineProperty(mockLocalStorage, 'key', {
        value: jest.fn()
          .mockReturnValueOnce('chat_conversation_old_profile_1')
          .mockReturnValueOnce('chat_conversation_old_profile_2'),
      });

      chatService.cleanupOldConversations();

      // Should remove old conversations
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith(
        'chat_conversation_old_profile_1'
      );
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith(
        'chat_conversation_old_profile_2'
      );
    });

    it('should preserve recent conversations', () => {
      const recentDate = new Date();
      recentDate.setDate(recentDate.getDate() - 1); // 1 day ago

      mockLocalStorage.getItem.mockImplementation((key) => {
        if (key.startsWith('chat_conversation_')) {
          return JSON.stringify([
            {
              id: 'recent-msg-1',
              role: 'user',
              content: 'Recent message',
              timestamp: recentDate.toISOString(),
            },
          ]);
        }
        return null;
      });

      Object.defineProperty(mockLocalStorage, 'length', { value: 1 });
      Object.defineProperty(mockLocalStorage, 'key', {
        value: jest.fn().mockReturnValueOnce('chat_conversation_recent_profile'),
      });

      chatService.cleanupOldConversations();

      // Should not remove recent conversations
      expect(mockLocalStorage.removeItem).not.toHaveBeenCalledWith(
        'chat_conversation_recent_profile'
      );
    });
  });

  describe('Error Handling', () => {
    it('should handle fetch timeout', async () => {
      // Mock fetch to never resolve (simulate timeout)
      (fetch as jest.Mock).mockImplementationOnce(
        () => new Promise(() => {}) // Never resolves
      );

      // Mock setTimeout to immediately call the timeout callback
      jest.spyOn(global, 'setTimeout').mockImplementationOnce((callback) => {
        (callback as Function)();
        return 0 as any;
      });

      const request: ChatRequest = {
        message: 'Test message',
        profileId: 'test-profile',
      };

      await expect(chatService.sendMessage(request)).rejects.toThrow(
        'Request timeout'
      );

      jest.restoreAllMocks();
    });

    it('should retry failed requests', async () => {
      const request: ChatRequest = {
        message: 'Test message',
        profileId: 'test-profile',
      };

      const mockResponse: ChatResponse = {
        response: 'Test response',
        responseId: 'test-id',
        isFromCache: false,
        tokenUsage: 100,
        responseTimeMs: 500,
      };

      // First call fails, second succeeds
      (fetch as jest.Mock)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        });

      const result = await chatService.sendMessage(request);

      expect(fetch).toHaveBeenCalledTimes(2);
      expect(result).toEqual(mockResponse);
    });

    it('should fail after max retries', async () => {
      const request: ChatRequest = {
        message: 'Test message',
        profileId: 'test-profile',
      };

      // All calls fail
      (fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

      await expect(chatService.sendMessage(request)).rejects.toThrow(
        'Network error occurred while sending message'
      );

      expect(fetch).toHaveBeenCalledTimes(3); // Initial + 2 retries
    });
  });

  describe('addMessagesToHistory', () => {
    it('should add messages to history successfully', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, message: 'Messages added to history' }),
      });

      const result = await chatService.addMessagesToHistory('test-profile', [
        {
          id: 'msg-1',
          role: 'user',
          content: 'Test message',
          timestamp: '2023-01-01T10:00:00Z'
        }
      ]);

      expect(fetch).toHaveBeenCalledWith('/api/chat/history/test-profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [
            {
              id: 'msg-1',
              role: 'user',
              content: 'Test message',
              timestamp: '2023-01-01T10:00:00Z'
            }
          ]
        }),
      });

      expect(result).toEqual({ success: true, message: 'Messages added to history' });
    });

    it('should handle conversation saving error', async () => {
      mockLocalStorage.setItem.mockImplementation(() => {
        throw new Error('Storage error');
      });

      // Should not throw error
      expect(() => {
        chatService.addMessagesToHistory('test-profile', [
          {
            id: 'msg-1',
            role: 'user',
            content: 'Test message',
            timestamp: '2023-01-01T10:00:00Z'
          }
        ]);
      }).not.toThrow();
    });
  });
}); 