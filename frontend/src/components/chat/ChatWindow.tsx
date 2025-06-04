/**
 * ChatWindow - Main chat interface component
 */
import React, { useCallback, useEffect } from 'react';
import { X, RefreshCw, AlertCircle } from 'lucide-react';
import { ConversationView } from './ConversationView';
import { MessageInput } from './MessageInput';
import { QuickQuestions } from './QuickQuestions';
import { useChat } from '../../hooks/useChat';
import { useProfile } from '../../contexts/ProfileContext';
import { BiomarkerReference } from '../../types/chat';

interface ChatWindowProps {
  isOpen: boolean;
  onClose: () => void;
  className?: string;
  onBiomarkerClick?: (biomarker: BiomarkerReference) => void;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  isOpen,
  onClose,
  className = '',
  onBiomarkerClick
}) => {
  const { activeProfile } = useProfile();
  const {
    messages,
    isLoading,
    error,
    suggestions,
    usageMetrics,
    sendMessage,
    clearConversation,
    submitFeedback,
    retryLastMessage,
    canRetry,
    isHealthy
  } = useChat({ autoLoadSuggestions: true, trackUsage: true });

  // Keyboard shortcut to close chat (Escape)
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, onClose]);

  // Prepare biomarker context from active profile
  const getBiomarkerContext = useCallback(() => {
    // Note: biomarkers should be passed from parent component that has access to them
    // Profile doesn't contain biomarkers directly
    return undefined; // For now, return undefined - this should be passed as a prop
  }, []);

  const handleSendMessage = useCallback(async (message: string) => {
    const biomarkerContext = getBiomarkerContext();
    await sendMessage(message, biomarkerContext);
  }, [sendMessage, getBiomarkerContext]);

  const handleQuestionClick = useCallback((question: string) => {
    handleSendMessage(question);
  }, [handleSendMessage]);

  const handleClearConversation = useCallback(() => {
    if (window.confirm('Are you sure you want to clear the conversation? This cannot be undone.')) {
      clearConversation();
    }
  }, [clearConversation]);

  const handleRetry = useCallback(async () => {
    if (canRetry) {
      await retryLastMessage();
    }
  }, [canRetry, retryLastMessage]);

  // Don't render if not open
  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-25 z-40"
        onClick={onClose}
      />
      
      {/* Chat Window */}
      <div className={`
        fixed bottom-24 right-6 bg-white rounded-lg shadow-2xl z-50
        flex flex-col overflow-hidden transform transition-all duration-300
        h-[min(600px,90vh)] max-h-[600px]
        w-96 max-w-[calc(100vw-3rem)] 
        sm:right-6 sm:w-96
        ${className}
      `}>
        {/* Header */}
        <div className="bg-blue-600 text-white p-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
              <span className="text-sm font-bold">🧬</span>
            </div>
            <div>
              <h2 className="font-semibold text-sm">Biomarker Assistant</h2>
              <p className="text-xs text-blue-100">
                {activeProfile?.name || 'No profile selected'}
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {/* Service Status */}
            <div className={`w-2 h-2 rounded-full ${
              isHealthy ? 'bg-green-400' : 'bg-red-400'
            }`} title={isHealthy ? 'Service healthy' : 'Service unavailable'} />
            
            {/* Clear Conversation */}
            {messages.length > 0 && (
              <button
                onClick={handleClearConversation}
                className="p-1 hover:bg-blue-500 rounded transition-colors duration-200"
                title="Clear conversation"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            )}
            
            {/* Close Button */}
            <button
              onClick={onClose}
              className="p-1 hover:bg-blue-500 rounded transition-colors duration-200"
              aria-label="Close chat"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Error State */}
        {!isHealthy && (
          <div className="bg-red-50 border-b border-red-200 p-3">
            <div className="flex items-center space-x-2 text-red-700">
              <AlertCircle className="w-4 h-4" />
              <span className="text-xs">
                Chat service is currently unavailable. Please try again later.
              </span>
            </div>
          </div>
        )}

        {/* No Profile State */}
        {!activeProfile && (
          <div className="bg-yellow-50 border-b border-yellow-200 p-3">
            <div className="flex items-center space-x-2 text-yellow-700">
              <AlertCircle className="w-4 h-4" />
              <span className="text-xs">
                Please select a profile to start chatting about biomarkers.
              </span>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border-b border-red-200 p-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-red-700">
                <AlertCircle className="w-4 h-4" />
                <span className="text-xs">{error}</span>
              </div>
              {canRetry && (
                <button
                  onClick={handleRetry}
                  className="text-xs bg-red-100 hover:bg-red-200 text-red-700 px-2 py-1 rounded transition-colors duration-200"
                >
                  Retry
                </button>
              )}
            </div>
          </div>
        )}

        {/* Quick Questions */}
        {suggestions.length > 0 && messages.length === 0 && (
          <div className="flex-shrink-0">
            <QuickQuestions
              questions={suggestions}
              onQuestionClick={handleQuestionClick}
              disabled={!isHealthy || !activeProfile || isLoading}
            />
          </div>
        )}

        {/* Conversation Container */}
        <div className="flex-1 flex flex-col min-h-0">
          <ConversationView
            messages={messages}
            isLoading={isLoading}
            onFeedback={submitFeedback}
            onBiomarkerClick={onBiomarkerClick}
            className="flex-1"
          />
        </div>

        {/* Message Input */}
        <div className="flex-shrink-0">
          <MessageInput
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
            disabled={!isHealthy || !activeProfile}
            placeholder={
              !activeProfile 
                ? "Select a profile to start chatting..."
                : !isHealthy
                  ? "Service unavailable..."
                  : "Ask about your biomarkers..."
            }
          />
        </div>

        {/* Usage Metrics (if enabled) */}
        {usageMetrics && (
          <div className="bg-gray-50 border-t border-gray-200 px-4 py-2">
            <div className="text-xs text-gray-500 flex items-center justify-between">
              <span>Today: {usageMetrics.dailyApiCalls} queries</span>
              <span>Avg response: {usageMetrics.averageResponseTime}ms</span>
            </div>
          </div>
        )}
      </div>
    </>
  );
}; 