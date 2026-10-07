import { useState, useRef, useEffect } from 'react';
import AnalysisResult from './AnalysisResult';

/**
 * ChatInterface - Conversational UI for asking questions about the dataset
 * 
 * Maintains conversation history and sends context to backend for follow-up questions
 */
export default function ChatInterface({ 
  currentFile, 
  onAnalyze, 
  isAnalyzing,
  suggestions = [],
  initialMessages = []
}) {
  const [messages, setMessages] = useState(initialMessages);
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Update messages when initialMessages changes (session restored)
  useEffect(() => {
    if (initialMessages.length > 0) {
      setMessages(initialMessages);
    }
  }, [initialMessages]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when component mounts or file changes
  useEffect(() => {
    if (currentFile) {
      inputRef.current?.focus();
    }
  }, [currentFile]);

  const handleSubmit = async (e) => {
    e?.preventDefault();
    
    if (!inputValue.trim() || !currentFile || isAnalyzing) return;

    const userQuestion = inputValue.trim();
    
    // Add user message to chat
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: userQuestion,
      timestamp: new Date().toISOString(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');

    // Build context history from previous Q&A pairs
    const contextHistory = messages
      .reduce((acc, msg, idx, arr) => {
        if (msg.role === 'user' && arr[idx + 1]?.role === 'assistant') {
          acc.push({
            question: msg.content,
            answer: arr[idx + 1].content,
          });
        }
        return acc;
      }, []);

    try {
      // Call the backend with context
      const result = await onAnalyze(userQuestion, contextHistory);
      
      // Add assistant response to chat with FULL result data
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: result.answer || result.verification_detail || 'Unable to process your question.',
        timestamp: new Date().toISOString(),
        // Store the COMPLETE result for full rendering
        result: result,
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      // Add error message to chat
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: `Error: ${error.message || 'Failed to analyze your question'}`,
        timestamp: new Date().toISOString(),
        result: {
          status: 'error',
          verification: 'ERROR',
          verification_detail: error.message || 'Failed to analyze your question',
        },
      };
      
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const handleCurrencyConversion = async (targetCurrency, questionText) => {
    if (!currentFile || isAnalyzing) return;
    const q = questionText || inputValue.trim();
    if (!q) return;

    const contextHistory = messages.reduce((acc, msg, idx, arr) => {
      if (msg.role === 'user' && arr[idx + 1]?.role === 'assistant') {
        acc.push({
          question: msg.content,
          answer: arr[idx + 1].content,
        });
      }
      return acc;
    }, []);

    try {
      const result = await onAnalyze(q, contextHistory, targetCurrency);
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: result.answer || result.verification_detail || 'Unable to process your question.',
        timestamp: new Date().toISOString(),
        result: result,
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Currency conversion analysis failed:", error);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setInputValue(suggestion);
    inputRef.current?.focus();
  };

  const clearChat = () => {
    if (window.confirm('Clear all messages from this conversation?')) {
      setMessages([]);
      setInputValue('');
    }
  };

  return (
    <div className="chat-interface">
      {/* Header */}
      <div className="chat-header">
        <div className="chat-header-content">
          <h2>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            Conversation
          </h2>
          {currentFile && (
            <span className="chat-file-indicator">
              {currentFile.name}
            </span>
          )}
        </div>
        {messages.length > 0 && (
          <button 
            onClick={clearChat}
            className="clear-chat-btn"
            title="Clear conversation"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="3 6 5 6 21 6" />
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
            </svg>
          </button>
        )}
      </div>

      {/* Messages Area */}
      <div className="chat-messages">
        {messages.length === 0 && currentFile && (
          <div className="chat-empty-state">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="12" cy="12" r="10" />
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
            <h3>Ask me anything about your data</h3>
            <p>I'll analyze your dataset and provide verified answers with reproducible proof.</p>
          </div>
        )}
        
        {!currentFile && (
          <div className="chat-empty-state">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" />
              <polyline points="13 2 13 9 20 9" />
            </svg>
            <h3>Upload a dataset to get started</h3>
            <p>Upload a CSV, Excel, or other data file to begin asking questions.</p>
          </div>
        )}

        {messages.map((message, idx) => (
          <div 
            key={message.id} 
            className={`chat-message ${message.role}`}
          >
            <div className="message-avatar">
              {message.role === 'user' ? (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
              ) : (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <rect x="3" y="11" width="18" height="10" rx="2" />
                  <circle cx="12" cy="5" r="2" />
                  <path d="M12 7v4" />
                  <line x1="8" y1="16" x2="8" y2="16" />
                  <line x1="16" y1="16" x2="16" y2="16" />
                </svg>
              )}
            </div>
            
            <div className="message-content">
              <div className="message-header">
                <span className="message-role">
                  {message.role === 'user' ? 'You' : 'ProofAI'}
                </span>
                <span className="message-time">
                  {new Date(message.timestamp).toLocaleTimeString([], { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                  })}
                </span>
              </div>
              
              <div className="message-text">
                {message.content}
              </div>

              {/* Full Analysis Result for assistant messages */}
              {message.role === 'assistant' && message.result && (
                <AnalysisResult
                  result={message.result}
                  onConvertCurrency={(currency) => handleCurrencyConversion(currency, message.result?.question)}
                />
              )}
            </div>
          </div>
        ))}

        {isAnalyzing && (
          <div className="chat-message assistant">
            <div className="message-avatar">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <rect x="3" y="11" width="18" height="10" rx="2" />
                <circle cx="12" cy="5" r="2" />
                <path d="M12 7v4" />
              </svg>
            </div>
            <div className="message-content">
              <div className="message-header">
                <span className="message-role">ProofAI</span>
              </div>
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggestions */}
      {suggestions.length > 0 && currentFile && (
        <div className="chat-suggestions">
          <div className="suggestions-label">Suggested questions:</div>
          <div className="suggestions-grid">
            {suggestions.slice(0, 4).map((suggestion, idx) => (
              <button
                key={idx}
                onClick={() => handleSuggestionClick(suggestion)}
                className="suggestion-chip"
                disabled={isAnalyzing}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                  <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Area */}
      <form onSubmit={handleSubmit} className="chat-input-container">
        {/* Context Indicator */}
        {messages.length > 0 && !isAnalyzing && (
          <div className="context-indicator">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
            <span>
              {messages.filter(m => m.role === 'user').length} previous {messages.filter(m => m.role === 'user').length === 1 ? 'question' : 'questions'} in context
            </span>
          </div>
        )}
        
        <div className="chat-input-wrapper">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={currentFile ? "Ask a question about your data..." : "Upload a file first"}
            disabled={!currentFile || isAnalyzing}
            className="chat-input"
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || !currentFile || isAnalyzing}
            className="chat-submit-btn"
            title="Send message"
          >
            {isAnalyzing ? (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="spinner">
                <line x1="12" y1="2" x2="12" y2="6" />
                <line x1="12" y1="18" x2="12" y2="22" />
                <line x1="4.93" y1="4.93" x2="7.76" y2="7.76" />
                <line x1="16.24" y1="16.24" x2="19.07" y2="19.07" />
                <line x1="2" y1="12" x2="6" y2="12" />
                <line x1="18" y1="12" x2="22" y2="12" />
                <line x1="4.93" y1="19.07" x2="7.76" y2="16.24" />
                <line x1="16.24" y1="7.76" x2="19.07" y2="4.93" />
              </svg>
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
