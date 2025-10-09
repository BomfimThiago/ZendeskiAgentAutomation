/**
 * Main Application Component - MyAwesomeFakeCompany Website
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
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [hasUnread, setHasUnread] = useState(false);
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
        await apiService.checkHealth();
        setIsConnected(true);

        const welcomeResponse = await apiService.getWelcomeMessage();
        setSessionId(welcomeResponse.session_id);
        setMessages([
          {
            role: 'assistant',
            content: welcomeResponse.message,
            timestamp: new Date().toLocaleTimeString(),
          },
        ]);
        setHasUnread(true);
      } catch (err) {
        setError('Unable to connect to chat service.');
        console.error('Initialization error:', err);
      }
    };

    initializeChat();
  }, []);

  const handleSendMessage = async (messageText: string) => {
    if (!messageText.trim()) return;

    const userMessage: ChatMessageType = {
      role: 'user',
      content: messageText,
      timestamp: new Date().toLocaleTimeString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError('');

    try {
      const response = await apiService.sendMessage({
        message: messageText,
        session_id: sessionId,
      });

      if (response.session_id !== sessionId) {
        setSessionId(response.session_id);
      }

      const assistantMessage: ChatMessageType = {
        role: 'assistant',
        content: response.message,
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);

      if (!isChatOpen) {
        setHasUnread(true);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to send message. Please try again.'
      );
      console.error('Send message error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleChat = () => {
    setIsChatOpen(!isChatOpen);
    if (!isChatOpen) {
      setHasUnread(false);
    }
  };

  return (
    <div className="App">
      {/* Navigation */}
      <nav className="navbar">
        <div className="nav-container">
          <div className="nav-logo">
            <span className="logo-icon">⚡</span>
            <span className="logo-text">MyAwesomeFakeCompany</span>
          </div>
          <ul className="nav-menu">
            <li><a href="#home">Home</a></li>
            <li><a href="#plans">Plans</a></li>
            <li><a href="#about">About</a></li>
            <li><a href="#support">Support</a></li>
            <li><a href="#contact" className="nav-cta">Contact Sales</a></li>
          </ul>
        </div>
      </nav>

      {/* Hero Section */}
      <section id="home" className="hero">
        <div className="hero-content">
          <h1 className="hero-title">Lightning-Fast Internet for Everyone</h1>
          <p className="hero-subtitle">
            Experience blazing speeds up to 1 Gbps with our fiber-optic network.
            Reliable, affordable, and always there when you need it.
          </p>
          <div className="hero-buttons">
            <button className="btn btn-primary">View Plans</button>
            <button className="btn btn-secondary">Check Availability</button>
          </div>
          <div className="hero-features">
            <div className="feature-badge">
              <span className="badge-icon">✓</span>
              <span>No Contracts</span>
            </div>
            <div className="feature-badge">
              <span className="badge-icon">✓</span>
              <span>24/7 Support</span>
            </div>
            <div className="feature-badge">
              <span className="badge-icon">✓</span>
              <span>Free Installation</span>
            </div>
          </div>
        </div>
        <div className="hero-image">
          <div className="speed-indicator">
            <div className="speed-dial"></div>
            <p className="speed-text">Up to 1 Gbps</p>
          </div>
        </div>
      </section>

      {/* Plans Section */}
      <section id="plans" className="plans-section">
        <div className="section-container">
          <h2 className="section-title">Choose Your Perfect Plan</h2>
          <p className="section-subtitle">No hidden fees. No surprises. Just fast internet.</p>

          <div className="plans-grid">
            <div className="plan-card">
              <div className="plan-header">
                <h3>Basic</h3>
                <div className="plan-price">
                  <span className="price">$29.99</span>
                  <span className="period">/month</span>
                </div>
              </div>
              <ul className="plan-features">
                <li>✓ Up to 25 Mbps</li>
                <li>✓ Perfect for browsing</li>
                <li>✓ Streaming in HD</li>
                <li>✓ 1-2 devices</li>
              </ul>
              <button className="btn btn-outline">Select Plan</button>
            </div>

            <div className="plan-card featured">
              <div className="popular-badge">Most Popular</div>
              <div className="plan-header">
                <h3>Standard</h3>
                <div className="plan-price">
                  <span className="price">$49.99</span>
                  <span className="period">/month</span>
                </div>
              </div>
              <ul className="plan-features">
                <li>✓ Up to 100 Mbps</li>
                <li>✓ Multiple devices</li>
                <li>✓ 4K streaming</li>
                <li>✓ 3-5 devices</li>
              </ul>
              <button className="btn btn-primary">Select Plan</button>
            </div>

            <div className="plan-card">
              <div className="plan-header">
                <h3>Gigabit</h3>
                <div className="plan-price">
                  <span className="price">$79.99</span>
                  <span className="period">/month</span>
                </div>
              </div>
              <ul className="plan-features">
                <li>✓ Up to 1 Gbps</li>
                <li>✓ Unlimited devices</li>
                <li>✓ Gaming & streaming</li>
                <li>✓ Home office ready</li>
              </ul>
              <button className="btn btn-outline">Select Plan</button>
            </div>
          </div>
        </div>
      </section>

      {/* About Section */}
      <section id="about" className="about-section">
        <div className="section-container">
          <div className="about-content">
            <h2 className="section-title">Why Choose Us?</h2>
            <div className="features-grid">
              <div className="feature-item">
                <div className="feature-icon">🚀</div>
                <h3>Lightning Fast</h3>
                <p>Experience speeds that keep up with your lifestyle. Stream, game, and work without interruption.</p>
              </div>
              <div className="feature-item">
                <div className="feature-icon">🛡️</div>
                <h3>Reliable Service</h3>
                <p>99.9% uptime guarantee. Our network is built to keep you connected when it matters most.</p>
              </div>
              <div className="feature-item">
                <div className="feature-icon">💬</div>
                <h3>24/7 Support</h3>
                <p>Real people, real help. Our support team is always here to assist you, day or night.</p>
              </div>
              <div className="feature-item">
                <div className="feature-icon">💰</div>
                <h3>No Hidden Fees</h3>
                <p>Transparent pricing with no surprises. What you see is what you pay.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-container">
          <div className="footer-section">
            <h4>MyAwesomeFakeCompany</h4>
            <p>Connecting communities with reliable, high-speed internet since 2018.</p>
          </div>
          <div className="footer-section">
            <h4>Quick Links</h4>
            <ul>
              <li><a href="#plans">Plans & Pricing</a></li>
              <li><a href="#about">About Us</a></li>
              <li><a href="#support">Support Center</a></li>
            </ul>
          </div>
          <div className="footer-section">
            <h4>Contact</h4>
            <ul>
              <li>📞 1-800-AWESOME</li>
              <li>📧 support@myawesomefakecompany.com</li>
              <li>📍 123 Internet Lane, Web City</li>
            </ul>
          </div>
        </div>
        <div className="footer-bottom">
          <p>&copy; 2024 MyAwesomeFakeCompany. All rights reserved.</p>
        </div>
      </footer>

      {/* Chat Widget */}
      {isChatOpen && (
        <div className="chat-widget open">
          <div className="chat-header">
            <div className="chat-header-info">
              <span className="chat-agent-avatar">🤖</span>
              <div>
                <h3>Alex - Virtual Assistant</h3>
                <span className={`chat-status ${isConnected ? 'online' : 'offline'}`}>
                  {isConnected ? 'Online' : 'Offline'}
                </span>
              </div>
            </div>
            <button className="chat-close" onClick={toggleChat}>✕</button>
          </div>

          <div className="chat-messages">
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
                <span className="typing-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {error && (
            <div className="chat-error">
              <span>⚠️ {error}</span>
            </div>
          )}

          <ChatInput onSendMessage={handleSendMessage} disabled={isLoading || !isConnected} />
        </div>
      )}

      {/* Chat Toggle Button */}
      <button
        className={`chat-toggle ${hasUnread ? 'has-unread' : ''}`}
        onClick={toggleChat}
        title="Chat with us"
      >
        {isChatOpen ? '✕' : '💬'}
        {hasUnread && !isChatOpen && <span className="unread-badge"></span>}
      </button>
    </div>
  );
}

export default App;
