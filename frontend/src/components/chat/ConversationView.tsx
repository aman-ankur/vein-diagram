/**
 * ConversationView - Displays chat messages with biomarker references
 */
import React, { useEffect, useRef } from 'react';
import { ChatMessage, BiomarkerReference } from '../../types/chat';
import { User, Bot, ThumbsUp, ThumbsDown, Clock, Zap } from 'lucide-react';

interface ConversationViewProps {
  messages: ChatMessage[];
  isLoading: boolean;
  onFeedback?: (responseId: string, isHelpful: boolean) => void;
  onBiomarkerClick?: (biomarker: BiomarkerReference) => void;
  className?: string;
}

export const ConversationView: React.FC<ConversationViewProps> = ({
  messages,
  isLoading,
  onFeedback,
  onBiomarkerClick,
  className = ''
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current) {
      const scrollContainer = messagesEndRef.current.parentElement;
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [messages, isLoading]);
  
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
  };
  
  const renderBiomarkerReferences = (biomarkers?: BiomarkerReference[]) => {
    if (!biomarkers || biomarkers.length === 0) return null;
    
    return (
      <div className="mt-3 flex flex-wrap gap-2">
        {biomarkers.map((biomarker, index) => (
          <button
            key={index}
            onClick={() => onBiomarkerClick?.(biomarker)}
            className={`
              inline-flex items-center px-2 py-1 rounded-full text-xs font-medium
              transition-colors duration-200 hover:shadow-sm
              ${biomarker.isAbnormal 
                ? 'bg-red-100 text-red-800 hover:bg-red-200' 
                : 'bg-green-100 text-green-800 hover:bg-green-200'
              }
            `}
          >
            {biomarker.name}: {biomarker.value} {biomarker.unit}
          </button>
        ))}
      </div>
    );
  };
  
  const renderMessage = (message: ChatMessage, index: number) => {
    const isUser = message.role === 'user';
    const isLast = index === messages.length - 1;
    
    return (
      <div
        key={message.id}
        className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
      >
        <div className={`flex max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
          {/* Avatar */}
          <div className={`
            flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center
            ${isUser ? 'bg-blue-600 ml-3' : 'bg-gray-600 mr-3'}
          `}>
            {isUser ? (
              <User className="w-4 h-4 text-white" />
            ) : (
              <Bot className="w-4 h-4 text-white" />
            )}
          </div>
          
          {/* Message Content */}
          <div className={`
            rounded-lg px-4 py-3 shadow-sm
            ${isUser 
              ? 'bg-blue-600 text-white' 
              : 'bg-white text-gray-900 border border-gray-200'
            }
          `}>
            {/* Message Text */}
            <div className="text-sm whitespace-pre-wrap break-words">
              {message.content}
            </div>
            
            {/* Biomarker References (AI messages only) */}
            {!isUser && renderBiomarkerReferences(message.biomarkerReferences)}
            
            {/* Message Metadata */}
            <div className={`
              mt-2 flex items-center justify-between text-xs
              ${isUser ? 'text-blue-100' : 'text-gray-500'}
            `}>
              <div className="flex items-center space-x-2">
                <Clock className="w-3 h-3" />
                <span>{formatTimestamp(message.timestamp)}</span>
                
                {/* Cache indicator */}
                {!isUser && message.isFromCache && (
                  <div className="flex items-center space-x-1 text-green-600">
                    <Zap className="w-3 h-3" />
                    <span>Instant</span>
                  </div>
                )}
              </div>
              
              {/* Feedback Buttons (AI messages only) */}
              {!isUser && message.responseId && onFeedback && (
                <div className="flex items-center space-x-1">
                  <button
                    onClick={() => onFeedback(message.responseId!, true)}
                    className="p-1 rounded hover:bg-gray-100 transition-colors duration-200"
                    aria-label="Helpful response"
                  >
                    <ThumbsUp className="w-3 h-3 text-gray-400 hover:text-green-600" />
                  </button>
                  <button
                    onClick={() => onFeedback(message.responseId!, false)}
                    className="p-1 rounded hover:bg-gray-100 transition-colors duration-200"
                    aria-label="Not helpful response"
                  >
                    <ThumbsDown className="w-3 h-3 text-gray-400 hover:text-red-600" />
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };
  
  return (
    <div className={`flex-1 overflow-y-auto p-4 space-y-4 ${className}`} style={{ minHeight: 0 }}>
      {/* Welcome Message */}
      {messages.length === 0 && !isLoading && (
        <div className="text-center py-8">
          <Bot className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Hi! I'm your biomarker health assistant
          </h3>
          <p className="text-gray-600 max-w-md mx-auto">
            I can help you understand your lab results and suggest lifestyle improvements. 
            What would you like to know about your biomarkers?
          </p>
        </div>
      )}
      
      {/* Messages */}
      {messages.map(renderMessage)}
      
      {/* Loading Indicator */}
      {isLoading && (
        <div className="flex justify-start mb-4">
          <div className="flex max-w-[80%]">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-600 mr-3 flex items-center justify-center">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div className="bg-white rounded-lg px-4 py-3 border border-gray-200">
              <div className="flex items-center space-x-2 text-gray-500">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
                <span className="text-xs">Analyzing your biomarkers...</span>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Scroll Target */}
      <div ref={messagesEndRef} />
    </div>
  );
}; 