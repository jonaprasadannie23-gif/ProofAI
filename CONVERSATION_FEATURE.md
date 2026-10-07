# Conversational Interface - Implementation Guide

## Overview

The ProofAI frontend now includes a full conversational chat interface that maintains context across multiple questions about the same dataset. This enables natural follow-up questions and multi-turn data analysis conversations.

## Key Features

### 1. Chat-Based UI
- **Message History**: All questions and answers are displayed in a scrollable chat interface
- **Visual Distinction**: User messages and AI responses are clearly differentiated with avatars and styling
- **Timestamps**: Each message shows when it was sent
- **Auto-scroll**: Automatically scrolls to the latest message

### 2. Context Preservation
- **Conversation History**: The interface automatically builds a context history from previous Q&A pairs
- **Follow-up Support**: Each new question includes context from all previous questions in the conversation
- **Smart Context Building**: Converts chat messages into `{question, answer}` pairs for backend processing

### 3. Verification & Status Indicators
- **Verified Badge**: Green badge for successfully verified answers
- **Refused Badge**: Yellow badge when the system cannot verify an answer
- **Error Badge**: Red badge for errors
- **Analysis Mode Tags**: Shows whether analysis used AI or local fallback

### 4. Interactive Elements
- **Suggestion Chips**: Quick-access buttons for common questions (shown when no messages exist)
- **Clear Conversation**: Button to reset the conversation
- **Typing Indicator**: Animated dots while the AI is processing

### 5. Data Quality Warnings
- Inline warnings displayed with assistant messages
- Highlights data quality issues that may affect answer reliability

## Architecture

### Component Structure

```
App.jsx
├── ChatInterface.jsx (NEW)
│   ├── Message list with history
│   ├── Input field with submit
│   ├── Suggestion chips
│   └── Typing indicator
├── UploadPanel.jsx
└── DatasetPreview.jsx
```

### Data Flow

```
User types question
    ↓
ChatInterface adds user message to UI
    ↓
Build context history from previous messages
    ↓
Call onAnalyze(question, contextHistory)
    ↓
App.jsx sends FormData to /analyze endpoint
    - question: current question
    - file: uploaded dataset file
    - context_history: JSON array of [{question, answer}, ...]
    ↓
Backend analyzes with context
    ↓
Response returned to ChatInterface
    ↓
ChatInterface adds assistant message to UI
```

### State Management

**ChatInterface Local State:**
- `messages`: Array of message objects with role, content, timestamp, metadata
- `inputValue`: Current text input value

**App.jsx State:**
- `dataset`: Currently active dataset with file reference
- `analyzing`: Boolean indicating analysis in progress
- `history`: Global history across all datasets

### Message Structure

```javascript
{
  id: number,              // Unique message ID
  role: 'user' | 'assistant',
  content: string,         // The message text
  timestamp: string,       // ISO timestamp
  metadata: {              // Only for assistant messages
    status: string,        // 'success', 'refused', 'error'
    verification: string,  // 'VERIFIED', 'REFUSED', 'ERROR'
    generatedCode: string,
    dataQuality: object,
    warnings: string[],
    analysisMode: string   // 'gemini', 'local_fallback', 'refused'
  }
}
```

## Backend Integration

### Endpoint: POST /analyze

**Request:**
```
FormData:
  - question: string
  - file: File
  - context_history: JSON string of [{question: string, answer: string}, ...]
```

**Response:**
```json
{
  "status": "success" | "refused" | "error",
  "answer": "The verified answer",
  "verification": "VERIFIED" | "REFUSED" | "ERROR",
  "verification_detail": "Explanation of verification status",
  "generated_code": "Python code that produced the answer",
  "reproducible_proof": "Complete standalone script",
  "dataset_summary": { ... },
  "data_quality": {
    "issues": [...],
    "total_issues": number
  },
  "warnings": ["..."],
  "analysis_mode": "gemini" | "local_fallback" | "refused"
}
```

### Context History Format

The backend receives previous Q&A pairs to provide better context for follow-up questions:

```json
[
  {
    "question": "What is the total revenue?",
    "answer": "$1,250,000"
  },
  {
    "question": "How many orders were there?",
    "answer": "450 orders"
  }
]
```

This allows the LLM to:
- Understand references to previous answers ("what about last year?")
- Maintain calculation context
- Provide coherent multi-turn analysis

## CSS Styling

All chat interface styles are in `index.css` under the "Chat Interface Styles" section. Key style classes:

- `.chat-interface` - Main container
- `.chat-messages` - Scrollable message area
- `.chat-message.user` / `.chat-message.assistant` - Individual messages
- `.verification-badge` - Status indicators
- `.typing-indicator` - Loading animation
- `.chat-input` - Text input field

## Usage Example

### Basic Conversation Flow

1. **User uploads CSV file with sales data**
   - File preview appears on left
   - Chat interface ready on right
   - Suggestions shown at bottom

2. **User asks: "What is the total revenue?"**
   - User message appears in chat
   - Typing indicator shows
   - AI responds: "$1,250,000" with VERIFIED badge
   - Context: `[{question: "What is the total revenue?", answer: "$1,250,000"}]`

3. **User asks: "What about last month?"**
   - Previous context sent to backend
   - AI understands "last month" refers to revenue from previous question
   - AI responds: "$95,000" with VERIFIED badge
   - Context now includes both Q&A pairs

4. **User asks: "Show me the top product"**
   - Full context sent
   - AI provides answer based on entire conversation
   - Maintains understanding of the dataset and previous analysis

### Clearing Conversation

- Click the trash icon in chat header
- Confirms before clearing
- Removes all messages but keeps dataset loaded
- Ready for new conversation with clean slate

## Benefits

1. **Natural Interaction**: Users can ask follow-up questions naturally without repeating context
2. **Context Awareness**: Backend receives full conversation history for intelligent responses
3. **Transparent Verification**: Every answer shows its verification status
4. **Error Resilience**: Graceful handling of errors and refused queries
5. **History Tracking**: All conversations are preserved for later reference
6. **Reproducible Results**: Each answer includes the code that generated it

## Future Enhancements

Potential improvements for future iterations:

- [ ] Export conversation as PDF or Markdown
- [ ] Search within conversation history
- [ ] Pin important messages
- [ ] Edit previous questions
- [ ] Branch conversations at any point
- [ ] Side-by-side comparison of different analysis approaches
- [ ] Collaborative conversations (multi-user)
- [ ] Voice input for questions
- [ ] Conversation templates for common analysis patterns

## Testing Recommendations

1. **Single Question**: Upload dataset, ask one question, verify response
2. **Follow-up Questions**: Ask 3-5 related questions, ensure context is maintained
3. **Error Handling**: Test with invalid questions, missing data, API failures
4. **UI Responsiveness**: Test with long questions/answers, many messages
5. **Data Quality Warnings**: Upload dataset with issues, verify warnings display
6. **Suggestions**: Verify suggestion chips work and populate input
7. **Clear Conversation**: Test clearing messages mid-conversation
8. **Multiple Datasets**: Switch between datasets, verify conversations reset

## Technical Notes

### Performance Considerations

- Messages array grows with conversation length (consider pagination for very long conversations)
- Each message includes full metadata (consider lazy loading for older messages)
- Context history sent with every request (reasonable for typical conversations <50 Q&A pairs)

### Browser Compatibility

- Tested on modern browsers (Chrome, Firefox, Safari, Edge)
- Uses CSS Grid and Flexbox (IE11 not supported)
- Smooth scrolling requires `scroll-behavior` support (fallback: instant scroll)

### Accessibility

- Semantic HTML with proper ARIA roles
- Keyboard navigation supported
- Screen reader friendly message structure
- Focus management for input field

## Deployment Checklist

- [x] Create ChatInterface component
- [x] Add CSS styles for chat UI
- [x] Integrate with App.jsx
- [x] Update layout for full-height chat
- [x] Add context history building logic
- [x] Add verification badges
- [x] Add typing indicator
- [x] Add suggestion chips
- [x] Add clear conversation button
- [ ] Test with backend /analyze endpoint
- [ ] User acceptance testing
- [ ] Performance testing with large conversations
- [ ] Mobile responsive design (future)
