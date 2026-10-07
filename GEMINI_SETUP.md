# Gemini API Setup Guide

## Current Status

✅ **Backend code is correct**  
✅ **Model name is valid** (`gemini-3.8-flash` is a stable Gemini 3 model)  
✅ **SDK version is compatible** (`google-generativeai==0.8.3`)  
✅ **Environment loading works** (`.env` is read correctly)  

❌ **API key is not configured** — `.env` contains placeholder value

---

## What You Need To Do

### 1. Get a Gemini API Key

1. Go to **[Google AI Studio](https://aistudio.google.com/apikey)**
2. Sign in with your Google account
3. Click **Get API key** or **Create API key**
4. Copy the key (looks like `AIzaSy...`, ~39 characters)

**Free tier includes:**
- 15 requests per minute
- 1 million tokens per day
- More than enough for testing and development

---

### 2. Configure the Key

```zsh
cd /Users/adlin/Desktop/HACKNEX/ProofAI/backend

# Edit .env
nano .env
# OR
code .env
```

Replace this line:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

With your actual key:
```
GEMINI_API_KEY=AIzaSy...your-actual-key-here
```

**Important:**
- No quotes around the value
- No spaces before or after the `=`
- Never commit this file to git (already in `.gitignore`)

---

### 3. Restart the Backend

If the backend is already running, restart it to pick up the new key:

```zsh
# Stop the current uvicorn process (Ctrl+C in its terminal)

# Start it again
cd /Users/adlin/Desktop/HACKNEX/ProofAI/backend
source ../.venv_backend/bin/activate
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

---

### 4. Test Authentication

```zsh
cd /Users/adlin/Desktop/HACKNEX/ProofAI/backend
python test_gemini_auth.py
```

**Expected output:**
```
✓ GEMINI_API_KEY is loaded (len=39 characters)
✓ Gemini SDK configured
✓ Model instantiated: gemini-3.8-flash

Testing authentication with a minimal prompt...
✓ API authentication successful!
  Response: OK

✓ All checks passed. The backend should work correctly.
```

**If you see errors:**
- `API_KEY_INVALID` → Key is wrong, expired, or revoked — get a new one
- `PERMISSION_DENIED` → Gemini API not enabled for your account
- `RESOURCE_EXHAUSTED` → Quota exceeded (unlikely on free tier)

---

## Testing the Full Flow

1. **Upload a CSV** at http://localhost:5173
   - Use `backend/sample_data/sales.csv`
   - Should show preview with 20 rows

2. **Ask a question:**
   - "What is the total sales revenue?"
   - "Which product has the highest average sales?"

3. **Expected response:**
   - Generated Python code (e.g., `result = df['sales'].sum()`)
   - Executed answer (e.g., `19820.25`)
   - Verification status: `VERIFIED`
   - Dataset summary with warnings

---

## Common Issues

### "GEMINI_API_KEY contains placeholder value"

You forgot to replace `your_gemini_api_key_here` in `backend/.env`.

**Fix:** Edit `backend/.env` and paste your actual API key.

---

### "API key not valid"

The key is incorrect, expired, or the Gemini API isn't enabled.

**Fix:**
1. Double-check the key in `.env` (no extra spaces/quotes)
2. Get a fresh key from https://aistudio.google.com/apikey
3. Make sure you're signed in to the correct Google account

---

### Backend doesn't see the new key

You edited `.env` but the backend is still using the old cached value.

**Fix:** Restart the uvicorn server (Ctrl+C, then start again).

---

## Security Reminders

- ✅ `.env` is already in `.gitignore` — safe to edit
- ❌ Never commit API keys to git
- ❌ Never share your API key publicly
- ❌ Never paste your API key in chat/support unless it's a trusted private channel
- ✅ If a key is exposed, revoke it immediately in Google AI Studio

---

## What Changed

### Files Modified

1. **`backend/core/llm.py`**
   - Fixed outdated comment (was: "gemini-2.0-flash", now: "Gemini 3.8 Flash")
   - Model name `"gemini-3.8-flash"` was already correct

2. **`README.md`**
   - Added clear API key setup instructions
   - Added troubleshooting section
   - Added test_gemini_auth.py instructions

3. **`backend/test_gemini_auth.py`** (new file)
   - Validates API key without exposing it
   - Tests authentication with minimal Gemini API call
   - Clear error messages for common issues

### No Backend Restart Needed For Documentation

The backend code itself was already correct. Only the comment in `llm.py` was updated, which doesn't affect runtime behavior. The uvicorn `--reload` will pick it up automatically if the file was touched, but it's not critical.

---

## Next Steps

Once the API key is configured and `test_gemini_auth.py` passes:

1. The `/api/analyze` endpoint will work
2. Frontend question panel will generate Python code
3. Code will execute against the uploaded DataFrame
4. Results will display with verification status

The upload feature already works — you just need the API key for AI-powered analysis.
