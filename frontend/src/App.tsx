/**
 * Main Chat Application Component
 */
import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import ChatMessage from './components/ChatMessage';
import ChatInput from './components/ChatInput';
import { apiService, ChatMessage as ChatMessageType } from './services/api';

function App() {
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [sessionId, setSessionId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [isConnected, setIsConnected] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when messages change
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize chat on component mount
  useEffect(() => {
    const initializeChat = async () => {
      try {
        // Check backend health
        await apiService.checkHealth();
        setIsConnected(true);

        // Get welcome message
        const welcomeResponse = await apiService.getWelcomeMessage();
        setSessionId(welcomeResponse.session_id);
        setMessages([
          {
            role: 'assistant',
            content: welcomeResponse.message,
            timestamp: new Date().toLocaleTimeString(),
          },
        ]);
      } catch (err) {
        setError('Failed to connect to chat service. Please check if the backend is running.');
        console.error('Initialization error:', err);
      }
    };

    initializeChat();
  }, []);

  const handleSendMessage = async (messageText: string) => {
    if (!messageText.trim()) return;

    // Add user message to chat
    const userMessage: ChatMessageType = {
      role: 'user',
      content: messageText,
      timestamp: new Date().toLocaleTimeString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError('');

    try {
      // Send message to backend
      const response = await apiService.sendMessage({
        message: messageText,
        session_id: sessionId,
      });

      // Update session ID if it changed
      if (response.session_id !== sessionId) {
        setSessionId(response.session_id);
      }

      // Add assistant response to chat
      const assistantMessage: ChatMessageType = {
        role: 'assistant',
        content: response.message,
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to send message. Please try again.'
      );
      console.error('Send message error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="app-header">
        <h1>🔵 TeleCorp Customer Support</h1>
        <div className="connection-status">
          {isConnected ? (
            <span className="status-connected">● Connected</span>
          ) : (
            <span className="status-disconnected">● Disconnected</span>
          )}
        </div>
      </header>

      <main className="chat-container">
        <div className="messages-container">
          {messages.map((msg, index) => (
            <ChatMessage
              key={index}
              role={msg.role}
              content={msg.content}
              timestamp={msg.timestamp}
            />
          ))}
          {isLoading && (
            <div className="typing-indicator">
              <span>🤖 Alex is typing</span>
              <span className="dots">
                <span>.</span>
                <span>.</span>
                <span>.</span>
              </span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {error && (
          <div className="error-message">
            <span>⚠️ {error}</span>
          </div>
        )}

        <ChatInput onSendMessage={handleSendMessage} disabled={isLoading || !isConnected} />
      </main>

      <footer className="app-footer">
        <p>Session ID: {sessionId || 'Not connected'}</p>
        <p>Powered by TeleCorp AI Assistant</p>
      </footer>
    </div>
  );
}

export default App;
