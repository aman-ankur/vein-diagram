/**
 * Chat Components - Biomarker Insights Chatbot UI Components
 */

// Main chat interface (recommended for most use cases)
export { ChatInterface } from './ChatInterface';

// Individual components for custom implementations
export { ChatBubble } from './ChatBubble';
export { ChatWindow } from './ChatWindow';
export { ConversationView } from './ConversationView';
export { MessageInput } from './MessageInput';
export { QuickQuestions } from './QuickQuestions';

// Re-export types for convenience
export type { BiomarkerReference, ChatMessage, SuggestedQuestion } from '../../types/chat'; 