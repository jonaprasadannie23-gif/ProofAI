#!/usr/bin/env python3
"""
Test Gemini API authentication without exposing the API key.
Run from backend/: python test_gemini_auth.py
"""
import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv(".env")
api_key = os.getenv("GEMINI_API_KEY", "")

# Check key status
if not api_key:
    print("❌ ERROR: GEMINI_API_KEY is not set")
    print("   Set it in backend/.env")
    sys.exit(1)
elif api_key == "your_gemini_api_key_here":
    print("❌ ERROR: GEMINI_API_KEY contains placeholder value")
    print("   Replace it with your actual API key from https://aistudio.google.com/apikey")
    sys.exit(1)
elif len(api_key) < 30:
    print(f"⚠️  WARNING: GEMINI_API_KEY seems too short (len={len(api_key)})")
    print("   Google API keys are typically 39 characters starting with 'AIzaSy'")
else:
    print(f"✓ GEMINI_API_KEY is loaded (len={len(api_key)} characters)")

# Try to authenticate
try:
    genai.configure(api_key=api_key)
    print("✓ Gemini SDK configured")
    
    # Try to instantiate a model
    model = genai.GenerativeModel(model_name="gemini-3.8-flash")
    print("✓ Model instantiated: gemini-3.8-flash")
    
    # Try a minimal test generation (synchronous for simplicity)
    print("\nTesting authentication with a minimal prompt...")
    response = model.generate_content("Say 'OK' if you can read this.")
    
    if response and response.text:
        print(f"✓ API authentication successful!")
        print(f"  Response: {response.text.strip()[:50]}")
    else:
        print("⚠️  Got response but no text")
        
except Exception as e:
    error_msg = str(e)
    print(f"\n❌ API call failed:")
    
    if "API_KEY_INVALID" in error_msg or "API key not valid" in error_msg:
        print("   The API key was rejected by Google.")
        print("   Possible reasons:")
        print("   - Key is expired or revoked")
        print("   - Key was copied incorrectly (check for extra spaces)")
        print("   - Key doesn't have Gemini API access enabled")
        print("\n   Get a new key at: https://aistudio.google.com/apikey")
    elif "quota" in error_msg.lower():
        print("   API quota exceeded. Wait or check your quota limits.")
    else:
        print(f"   Error: {error_msg}")
    
    sys.exit(1)

print("\n✓ All checks passed. The backend should work correctly.")
