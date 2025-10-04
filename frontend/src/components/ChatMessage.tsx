/**
 * ChatMessage Component
 * Displays a single message in the chat
 */
import React from 'react';
import './ChatMessage.css';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ role, content, timestamp }) => {
  return (
    <div className={`chat-message ${role}`}>
      <div className="message-header">
        <span className="message-author">
          {role === 'assistant' ? '🤖 Alex' : '💬 You'}
        </span>
        {timestamp && <span className="message-time">{timestamp}</span>}
      </div>
      <div className="message-content">{content}</div>
    </div>
  );
};

export default ChatMessage;
