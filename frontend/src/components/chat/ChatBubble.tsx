/**
 * ChatBubble - Floating chat button that toggles the chat window
 */
import React from 'react';
import { MessageCircle, Zap, AlertCircle } from 'lucide-react';

interface ChatBubbleProps {
  isOpen: boolean;
  onClick: () => void;
  hasUnreadSuggestions?: boolean;
  isServiceHealthy?: boolean;
  className?: string;
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({
  isOpen,
  onClick,
  hasUnreadSuggestions = false,
  isServiceHealthy = true,
  className = ''
}) => {
  return (
    <div className={`fixed bottom-20 right-6 z-50 ${className}`}>
      <button
        onClick={onClick}
        className={`
          relative flex items-center justify-center w-14 h-14 rounded-full
          shadow-lg transition-all duration-300 transform hover:scale-110
          focus:outline-none focus:ring-4 focus:ring-offset-2
          ${isOpen 
            ? 'bg-red-500 hover:bg-red-600 focus:ring-red-300 rotate-45' 
            : isServiceHealthy
              ? 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-300'
              : 'bg-gray-400 hover:bg-gray-500 focus:ring-gray-300'
          }
        `}
        aria-label={isOpen ? 'Close chat' : 'Open biomarker chat assistant'}
        disabled={!isServiceHealthy}
      >
        {/* Main Icon */}
        {isOpen ? (
          <span className="text-white text-2xl font-bold">×</span>
        ) : isServiceHealthy ? (
          <MessageCircle className="w-6 h-6 text-white" />
        ) : (
          <AlertCircle className="w-6 h-6 text-white" />
        )}
        
        {/* Notification Badge */}
        {!isOpen && hasUnreadSuggestions && isServiceHealthy && (
          <div className="absolute -top-1 -right-1 w-4 h-4 bg-yellow-400 rounded-full flex items-center justify-center">
            <Zap className="w-2.5 h-2.5 text-yellow-900" />
          </div>
        )}
        
        {/* Pulse Animation for Suggestions */}
        {!isOpen && hasUnreadSuggestions && isServiceHealthy && (
          <div className="absolute inset-0 rounded-full bg-blue-400 animate-ping opacity-30"></div>
        )}
      </button>
      
      {/* Tooltip */}
      {!isOpen && (
        <div className="absolute bottom-full right-0 mb-2 px-3 py-1 bg-gray-900 text-white text-sm rounded-lg opacity-0 hover:opacity-100 transition-opacity duration-200 whitespace-nowrap pointer-events-none group-hover:opacity-100">
          {isServiceHealthy 
            ? hasUnreadSuggestions 
              ? 'New biomarker insights available!'
              : 'Ask about your biomarkers'
            : 'Chat service unavailable'
          }
          <div className="absolute top-full right-4 border-4 border-transparent border-t-gray-900"></div>
        </div>
      )}
    </div>
  );
}; 