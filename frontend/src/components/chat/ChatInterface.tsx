/**
 * ChatInterface - Complete chat feature combining bubble and window
 */
import React, { useState, useCallback } from 'react';
import { ChatBubble } from './ChatBubble';
import { ChatWindow } from './ChatWindow';
import { useChat } from '../../hooks/useChat';
import { useProfile } from '../../contexts/ProfileContext';
import { BiomarkerReference } from '../../types/chat';

interface ChatInterfaceProps {
  /** Optional callback when user clicks on biomarker references */
  onBiomarkerClick?: (biomarker: BiomarkerReference) => void;
  /** Custom CSS class */
  className?: string;
  /** Whether to show usage metrics */
  showMetrics?: boolean;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  onBiomarkerClick,
  className = '',
  showMetrics = false
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const { activeProfile } = useProfile();
  const { 
    chatState, 
    isServiceHealthy 
  } = useChat({ 
    autoLoadSuggestions: false, // Only load suggestions when chat is opened
    trackUsage: showMetrics 
  });

  const toggleChat = useCallback(() => {
    setIsOpen(prev => !prev);
  }, []);

  const closeChat = useCallback(() => {
    setIsOpen(false);
  }, []);

  // Determine if there are unread suggestions
  const hasUnreadSuggestions = chatState.suggestedQuestions.length > 0 && 
                               chatState.messages.length === 0;

  // Don't show chat if no active profile (unless we want to show a "select profile" message)
  const shouldShowChat = Boolean(activeProfile);

  return (
    <div className={`${className}`}>
      {/* Chat Bubble - Always visible when profile is active */}
      {shouldShowChat && (
        <ChatBubble
          isOpen={isOpen}
          onClick={toggleChat}
          hasUnreadSuggestions={hasUnreadSuggestions}
          isServiceHealthy={isServiceHealthy}
        />
      )}

      {/* Chat Window - Only visible when open */}
      <ChatWindow
        isOpen={isOpen}
        onClose={closeChat}
        onBiomarkerClick={onBiomarkerClick}
      />
    </div>
  );
};

// Export all chat components for individual use
export { ChatBubble } from './ChatBubble';
export { ChatWindow } from './ChatWindow';
export { ConversationView } from './ConversationView';
export { MessageInput } from './MessageInput';
export { QuickQuestions } from './QuickQuestions'; 