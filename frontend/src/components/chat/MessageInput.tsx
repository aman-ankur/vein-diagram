/**
 * MessageInput - Input field for sending chat messages
 */
import React, { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { Send, Loader2 } from 'lucide-react';

interface MessageInputProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  disabled?: boolean;
  placeholder?: string;
  maxLength?: number;
  className?: string;
}

export const MessageInput: React.FC<MessageInputProps> = ({
  onSendMessage,
  isLoading,
  disabled = false,
  placeholder = "Ask about your biomarkers...",
  maxLength = 1000,
  className = ''
}) => {
  const [message, setMessage] = useState('');
  const [isComposing, setIsComposing] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
    }
  }, [message]);
  
  // Focus on mount and when not loading
  useEffect(() => {
    if (!isLoading && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [isLoading]);
  
  const handleSubmit = () => {
    const trimmedMessage = message.trim();
    if (trimmedMessage && !isLoading && !disabled) {
      onSendMessage(trimmedMessage);
      setMessage('');
    }
  };
  
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
      e.preventDefault();
      handleSubmit();
    }
  };
  
  const handleCompositionStart = () => {
    setIsComposing(true);
  };
  
  const handleCompositionEnd = () => {
    setIsComposing(false);
  };
  
  const remainingChars = maxLength - message.length;
  const isNearLimit = remainingChars <= 50;
  const canSend = message.trim().length > 0 && !isLoading && !disabled;
  
  return (
    <div className={`bg-white border-t border-gray-200 p-4 ${className}`}>
      <div className="relative">
        {/* Character Counter */}
        {isNearLimit && (
          <div className={`absolute -top-6 right-0 text-xs ${
            remainingChars < 0 ? 'text-red-500' : 'text-gray-500'
          }`}>
            {remainingChars} characters remaining
          </div>
        )}
        
        <div className="flex items-end space-x-3">
          {/* Message Input */}
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              onCompositionStart={handleCompositionStart}
              onCompositionEnd={handleCompositionEnd}
              placeholder={placeholder}
              disabled={disabled || isLoading}
              maxLength={maxLength}
              rows={1}
              className={`
                w-full resize-none rounded-lg border border-gray-300 px-4 py-3 pr-12
                focus:border-blue-500 focus:ring-2 focus:ring-blue-200 focus:outline-none
                transition-colors duration-200 text-sm font-medium
                ${disabled || isLoading ? 'bg-gray-50 text-gray-500' : 'bg-white text-gray-900'}
                ${remainingChars < 0 ? 'border-red-300 focus:border-red-500 focus:ring-red-200' : ''}
                placeholder:text-gray-500 placeholder:font-normal
              `}
              style={{ minHeight: '44px', maxHeight: '100px' }}
            />
            
            {/* Send Button */}
            <button
              onClick={handleSubmit}
              disabled={!canSend}
              className={`
                absolute right-2 bottom-2 p-2 rounded-lg transition-all duration-200
                ${canSend 
                  ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-sm hover:shadow-md' 
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                }
              `}
              aria-label="Send message"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>
        
        {/* Helpful Tips */}
        {message.length === 0 && !isLoading && (
          <div className="mt-2 text-xs text-gray-500">
            💡 Try asking: "What do my abnormal biomarkers mean?" or "How can I improve my glucose levels?"
          </div>
        )}
      </div>
    </div>
  );
}; 