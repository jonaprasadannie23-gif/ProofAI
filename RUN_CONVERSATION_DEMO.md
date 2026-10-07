# Running the Conversational Interface Demo

This guide shows you how to start ProofAI with the new conversational chat interface.

## Prerequisites

1. **Backend Requirements:**
   - Python 3.8+
   - Virtual environment activated (`.venv_backend`)
   - Required packages installed from `backend/requirements.txt`
   - API keys configured in `backend/.env`

2. **Frontend Requirements:**
   - Node.js 16+
   - npm or yarn
   - Dependencies installed (`cd frontend && npm install`)

## Quick Start

### Terminal 1: Start Backend Server

```bash
cd ProofAI

# Activate virtual environment (if not already active)
source .venv_backend/bin/activate  # macOS/Linux
# OR
.venv_backend\Scripts\activate     # Windows

# Navigate to backend
cd backend

# Ensure .env file exists with your API keys
# Copy .env.example to .env if needed:
# cp .env.example .env
# Then edit .env and add your GROQ_API_KEY or GEMINI_API_KEY

# Start the FastAPI server
uvicorn main:app --reload --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Terminal 2: Start Frontend Dev Server

```bash
cd ProofAI/frontend

# Install dependencies (first time only)
npm install

# Start Vite dev server
npm run dev
```

Expected output:
```
  VITE v8.3.0  ready in 543 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

### Open the Application

Open your browser and navigate to:
```
http://localhost:5173
```

## Testing the Conversational Interface

### Step 1: Upload a Dataset

1. Click the upload area or drag a CSV/Excel file
2. Example: Use `backend/sample_data/sales.csv`
3. The dataset preview will appear on the left
4. The chat interface will appear on the right

### Step 2: Ask Initial Question

1. You'll see suggested questions (chips) at the bottom of the chat
2. Click a suggestion or type your own question
3. Example: "What is the total sales amount?"
4. Press Enter or click the send button

### Step 3: Ask Follow-up Questions

Now test the conversation context:

**Example Conversation:**

```
You: What is the total revenue?
AI: The total revenue is $1,250,000 [VERIFIED ✓]

You: What about just Q1?
AI: Q1 revenue is $320,000 [VERIFIED ✓]
    (AI understood "Q1" and "revenue" from context)

You: How does that compare to last year?
AI: Q1 last year was $285,000, so this year is up 12.3% [VERIFIED ✓]
    (AI maintained multi-turn context)

You: Show me the top selling product
AI: The top selling product is "Widget Pro" with 450 units sold [VERIFIED ✓]
```

### Step 4: Test Context Awareness

Try these follow-up patterns to verify context is working:

**Pronoun References:**
```
You: What is the average order value?
AI: The average order value is $278.50

You: What about the median?  ← "median" of what? (context: order value)
AI: The median order value is $245.00
```

**Comparative Questions:**
```
You: How many orders were placed in January?
AI: There were 145 orders in January

You: And in February?  ← AI knows you're still asking about orders
AI: There were 132 orders in February
```

**Chained Analysis:**
```
You: What's the total revenue?
AI: $1,250,000

You: Break that down by region
AI: North: $450k, South: $320k, East: $280k, West: $200k

You: Which region had the highest growth?  ← Uses previous breakdown
AI: North region had 18% growth year-over-year
```

## Features to Test

### ✅ Verification Badges

- **Green (VERIFIED)**: Answer is verified by executing code
- **Yellow (REFUSED)**: System cannot verify (ambiguous data, missing fields)
- **Red (ERROR)**: Execution error

### ✅ Data Quality Warnings

Upload a dataset with issues (missing values, duplicates) and see inline warnings.

### ✅ Analysis Mode Tags

- **🤖 AI Analysis**: Gemini/Groq generated code
- **⚡ Local Analysis**: Deterministic fallback when AI unavailable

### ✅ Typing Indicator

Watch the animated dots while the AI processes your question.

### ✅ Clear Conversation

Click the trash icon in the chat header to reset the conversation.

### ✅ Message Timestamps

Each message shows when it was sent.

### ✅ Auto-scroll

Automatically scrolls to the latest message.

## Troubleshooting

### Backend Not Responding

**Error:** `Failed to analyze your question`

**Check:**
```bash
# Is backend running?
curl http://localhost:8000/

# Expected response:
{"status":"ok","service":"ProofAI"}
```

**Solution:**
- Make sure backend is running on port 8000
- Check backend terminal for errors
- Verify .env file has API keys

### CORS Errors

**Error:** `Access to fetch at 'http://localhost:8000/api/analyze' from origin 'http://localhost:5173' has been blocked by CORS policy`

**Solution:**
Backend is configured for localhost:5173. If using a different port, update `backend/main.py`:
```python
allow_origins=[
    "http://localhost:5173",
    "http://localhost:YOUR_PORT",  # Add your port
],
```

### Context Not Working

**Symptom:** AI doesn't understand follow-up questions

**Check:**
1. Open browser DevTools (F12) → Network tab
2. Click on the `/api/analyze` request
3. In the Request payload, verify `context_history` field contains previous Q&A pairs

**Example context_history:**
```json
[
  {"question": "What is total revenue?", "answer": "$1,250,000"},
  {"question": "What about Q1?", "answer": "$320,000"}
]
```

If empty `[]`, the frontend isn't building context correctly.

### Upload Fails

**Error:** `Upload failed. Is the backend running?`

**Check:**
```bash
# Test upload endpoint
curl -X POST http://localhost:8000/api/upload \
  -F "file=@backend/sample_data/sales.csv"
```

**Solution:**
- Verify file type is supported (CSV, Excel, JSON, etc.)
- Check file isn't corrupted
- Verify backend logs for parsing errors

### Missing API Keys

**Error:** Backend starts but analysis fails with authentication errors

**Solution:**
```bash
cd backend
cp .env.example .env
nano .env  # or use your favorite editor

# Add your keys:
GROQ_API_KEY=your_actual_key_here
# OR
GEMINI_API_KEY=your_actual_key_here
```

## API Endpoint Details

### POST /api/analyze

**Request:**
```
Content-Type: multipart/form-data

Fields:
- question: "What is the total revenue?"
- file: [binary file data]
- context_history: '[{"question":"Previous Q","answer":"Previous A"}]'
```

**Response:**
```json
{
  "status": "success",
  "answer": "$1,250,000",
  "verification": "VERIFIED",
  "verification_detail": "Answer produced by executing code against your data.",
  "generated_code": "result = df['Revenue'].sum()",
  "analysis_mode": "gemini"
}
```

### POST /api/upload

**Request:**
```
Content-Type: multipart/form-data

Fields:
- file: [binary file data]
```

**Response:**
```json
{
  "filename": "sales.csv",
  "file_type": "csv",
  "is_tabular": true,
  "row_count": 1000,
  "col_count": 8,
  "columns": ["Date", "Product", "Revenue", "..."],
  "preview_data": [...],
  "suggestions": [
    "What is the total revenue?",
    "How many unique products are there?",
    "..."
  ]
}
```

## Performance Benchmarks

Typical response times (on M1 Mac with Groq):

- **Upload**: 200-500ms (depending on file size)
- **First Question**: 2-4 seconds (LLM generation + execution)
- **Follow-up**: 2-4 seconds (context doesn't slow it down significantly)
- **UI Rendering**: <50ms per message

## Next Steps

After testing the basic conversation flow:

1. **Try Edge Cases:**
   - Very long questions
   - Many consecutive questions (10+)
   - Switching datasets mid-conversation
   - Ambiguous questions

2. **Test Error Handling:**
   - Ask impossible questions
   - Upload corrupted files
   - Disconnect backend mid-conversation

3. **Test Data Quality:**
   - Upload data with many missing values
   - Upload data with ambiguous dates (MM/DD vs DD/MM)
   - Upload data with multiple currencies

4. **Export Your Conversation:**
   - Copy messages manually (export feature coming soon)
   - Take screenshots of interesting conversations
   - Document any bugs or unexpected behavior

## Stopping the Servers

**Terminal 1 (Backend):**
```
Press Ctrl+C
```

**Terminal 2 (Frontend):**
```
Press Ctrl+C
```

## Additional Resources

- **Backend Documentation**: See `backend/README.md`
- **API Documentation**: Visit `http://localhost:8000/docs` (FastAPI auto-generated)
- **Feature Overview**: See `CONVERSATION_FEATURE.md`
- **Frontend Architecture**: See `frontend/README.md`

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review backend logs in Terminal 1
3. Check browser console (F12) for frontend errors
4. Verify all dependencies are installed
5. Ensure API keys are configured correctly

---

**Happy Testing! 🚀**

The conversational interface makes data analysis feel natural and intuitive. Users can explore their data through dialogue, building on previous insights without repeating context.
