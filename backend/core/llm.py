"""
llm.py — ProofAI LLM layer.

PRIMARY provider : Groq  (OpenAI-compatible, fast inference)
LEGACY provider  : Gemini (kept for easy rollback; not active by default)

Set LLM_PROVIDER=gemini in .env to switch back to Gemini.
"""

import os
import json
import asyncio
import logging
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Provider selection ────────────────────────────────────────────────────────
# "groq"   → Groq OpenAI-compatible API  (default)
# "gemini" → Google Gemini SDK           (legacy, kept for rollback)
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq").lower().strip()

# ── Groq configuration ────────────────────────────────────────────────────────
_GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
_GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
_GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# ── Gemini configuration (legacy) ────────────────────────────────────────────
_GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

# ── llm_provider tag (visible in logs and analyst responses) ─────────────────
llm_provider: str = LLM_PROVIDER   # module-level so tests can inspect it

# ── Prompts ───────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are ProofAI, a Proof-Carrying Data Analyst.
Your job is to write clean, executable Python code that answers a user's question about a dataset.

Rules:
1. You have access to a pandas DataFrame called `df`.
2. You also have access to `pd` (pandas) and `np` (numpy).
3. Your answer MUST be assigned to a variable called `result`.
4. Do NOT use print() — assign the final answer to `result`.
5. Write only the Python code — no markdown fences, no explanation.
6. If the question cannot be answered with the available data, set result = "INSUFFICIENT_DATA: <reason>"
7. Keep the code concise and correct.
8. For string results, make them human-readable.
9. For numeric results, round to a reasonable number of decimal places.

Example:
result = df['sales'].sum()
"""


# ── Shared prompt builders ────────────────────────────────────────────────────

def _build_prompt(
    question: str,
    df: pd.DataFrame,
    filename: str,
    context_history: list | None = None,
    target_currency: str | None = None,
) -> str:
    """Build the analysis-code prompt."""
    col_info = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        sample = df[col].dropna().head(3).tolist()
        col_info.append(f"  - {col} ({dtype}): sample values = {sample}")

    data_description = (
        f"File: {filename}\n"
        f"Shape: {df.shape[0]} rows × {df.shape[1]} columns\n"
        f"Columns:\n" + "\n".join(col_info)
    )

    history_section = ""
    if context_history:
        history_lines = []
        for item in context_history[-4:]:
            q = item.get("question", "")
            a = item.get("answer", "")
            if q and a:
                history_lines.append(f"  Q: {q}\n  A: {a}")
        if history_lines:
            history_section = (
                "\n\nPrevious questions and answers for context:\n"
                + "\n".join(history_lines)
                + "\n"
            )

    currency_instruction = ""
    if target_currency:
        tc = target_currency.upper()
        if tc == "INR":
            currency_instruction = (
                "\n\nCRITICAL CURRENCY CONVERSION RULE:\n"
                "The user chose to CONVERT ALL VALUES TO INR.\n"
                "Use fixed rate USD_TO_INR = 83.50.\n"
                "You MUST include `USD_TO_INR = 83.50` in your code.\n"
                "Convert USD values to INR (row['Amount'] * 83.50), keep INR values as is.\n"
                "Calculate result and assign a string to `result` formatted as: "
                "\"Result converted to INR (Exchange rate: 1 USD = ₹83.50)\" or including the sum.\n"
            )
        elif tc == "USD":
            currency_instruction = (
                "\n\nCRITICAL CURRENCY CONVERSION RULE:\n"
                "The user chose to CONVERT ALL VALUES TO USD.\n"
                "Use fixed rate USD_TO_INR = 83.50.\n"
                "You MUST include `USD_TO_INR = 83.50` in your code.\n"
                "Convert INR values to USD (row['Amount'] / 83.50), keep USD values as is.\n"
                "Calculate result and assign a string to `result` formatted as: "
                "\"Result converted to USD (Exchange rate: 1 USD = ₹83.50)\" or including the sum.\n"
            )

    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"Dataset description:\n{data_description}"
        f"{currency_instruction}"
        f"{history_section}\n\n"
        f"Question: {question}\n\n"
        "Write Python code to answer this question. Assign the answer to `result`."
    )


def _build_suggestion_prompt(df: pd.DataFrame, filename: str) -> str:
    """Build the question-suggestions prompt."""
    col_info = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        sample = df[col].dropna().head(3).tolist()
        col_info.append(f"  - {col} ({dtype}): sample values = {sample}")

    data_description = (
        f"File: {filename}\n"
        f"Shape: {df.shape[0]} rows × {df.shape[1]} columns\n"
        f"Columns:\n" + "\n".join(col_info)
    )

    return (
        "You are ProofAI, an AI data analyst. Given the dataset below, "
        "suggest exactly 4 short, specific, useful analytical questions a user might ask. "
        "Each question must reference actual column names from the dataset. "
        "Return ONLY a JSON array of 4 question strings. No explanation, no markdown.\n\n"
        f"Dataset:\n{data_description}\n\n"
        "Return format: [\"question1\", \"question2\", \"question3\", \"question4\"]"
    )


def _strip_fences(code: str) -> str:
    """Remove markdown code fences if the model wrapped the response."""
    if code.startswith("```"):
        lines = code.splitlines()
        code = "\n".join(
            line for line in lines if not line.startswith("```")
        ).strip()
    return code


# ── Sentinel exception ────────────────────────────────────────────────────────

class GeminiUnavailableError(RuntimeError):
    """
    Raised when all retry attempts for a transient LLM error are exhausted.
    The name is preserved for backward-compatibility with analyst.py.
    Signals to the caller that the local fallback should be attempted.
    """


# ── Retry constants ───────────────────────────────────────────────────────────
# Attempt 1 → immediate, attempt 2 → 2 s, attempt 3 → 4 s, attempt 4 → 8 s.
_RETRY_DELAYS: tuple[float, ...] = (2.0, 4.0, 8.0)

# For backward-compatibility with tests that inspect these directly.
_RETRYABLE_SERVER_CODES: frozenset[int] = frozenset({503})
_RETRYABLE_CLIENT_CODES: frozenset[int] = frozenset({429})


# ═══════════════════════════════════════════════════════════════════════════════
# GROQ PROVIDER  (primary)
# ═══════════════════════════════════════════════════════════════════════════════

def _get_groq_client():
    """Lazy-initialise the AsyncOpenAI client pointed at Groq."""
    import openai
    return openai.AsyncOpenAI(
        api_key=_GROQ_API_KEY,
        base_url=_GROQ_BASE_URL,
    )


def _is_groq_transient(exc: Exception) -> bool:
    """True if the Groq/OpenAI exception is a transient error worth retrying."""
    import openai
    # 503 comes back as APIStatusError with status_code 503
    if isinstance(exc, openai.APIStatusError):
        return exc.status_code in (503, 529)      # 529 = Groq overloaded
    # Network / timeout errors are transient
    if isinstance(exc, (openai.APIConnectionError, openai.APITimeoutError)):
        return True
    return False


def _is_groq_terminal(exc: Exception) -> bool:
    """True if the error must propagate immediately without retrying."""
    import openai
    if isinstance(exc, openai.APIStatusError):
        # 401 bad key, 403 forbidden, 404 bad model, 400 bad request
        return exc.status_code in (400, 401, 403, 404)
    return False


async def _groq_call_with_retry(coro_factory) -> object:
    """
    Execute an async Groq API call with bounded exponential backoff.

    Retries on transient errors (503, 529, connection/timeout).
    Raises GeminiUnavailableError (kept for compat) when retries exhausted.
    Propagates terminal errors (401, 403, 404) immediately.

    Note: 429 rate-limit is NOT retried here — Groq's SDK already handles
    per-request retry internally. After quota is truly exhausted the call
    raises RateLimitError, which we surface as GeminiUnavailableError so
    analyst.py routes to the local fallback.
    """
    import openai

    last_exc: Exception | None = None

    for attempt, delay in enumerate([0.0, *_RETRY_DELAYS], start=1):
        if delay:
            await asyncio.sleep(delay)
        try:
            return await coro_factory()
        except openai.RateLimitError as exc:
            # 429 quota exhausted — don't spin-retry, go straight to fallback
            raise GeminiUnavailableError(
                f"Groq rate limit / quota exhausted (429). "
                f"Switching to local fallback. Error: {exc}"
            ) from exc
        except openai.APIStatusError as exc:
            if _is_groq_terminal(exc):
                raise          # auth/model errors — surface immediately
            if _is_groq_transient(exc):
                last_exc = exc
                logger.warning(
                    "groq transient error attempt=%d code=%d: %s",
                    attempt, exc.status_code, exc,
                )
                continue
            raise              # other 4xx/5xx — surface immediately
        except (openai.APIConnectionError, openai.APITimeoutError) as exc:
            last_exc = exc
            logger.warning("groq network error attempt=%d: %s", attempt, exc)
            continue

    raise GeminiUnavailableError(
        f"Groq API is temporarily unavailable. "
        f"Tried {len(_RETRY_DELAYS) + 1} times. Last error: {last_exc}"
    ) from last_exc


async def _groq_generate_code(
    question: str,
    df: pd.DataFrame,
    filename: str,
    context_history: list | None = None,
    target_currency: str | None = None,
) -> str:
    """Generate analysis code via Groq."""
    prompt = _build_prompt(
        question=question,
        df=df,
        filename=filename,
        context_history=context_history,
        target_currency=target_currency,
    )
    client = _get_groq_client()

    async def call():
        resp = await client.chat.completions.create(
            model=_GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=512,
        )
        return resp.choices[0].message.content or ""

    raw = await _groq_call_with_retry(call)
    return _strip_fences(raw.strip())


async def _groq_generate_suggestions(df: pd.DataFrame, filename: str) -> list[str]:
    """Generate schema-aware question suggestions via Groq."""
    prompt = _build_suggestion_prompt(df, filename)
    client = _get_groq_client()

    async def call():
        resp = await client.chat.completions.create(
            model=_GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=256,
        )
        return resp.choices[0].message.content or ""

    raw = await _groq_call_with_retry(call)
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(l for l in lines if not l.startswith("```")).strip()

    suggestions = json.loads(text)
    if isinstance(suggestions, list):
        return [str(s) for s in suggestions[:4]]
    return []


# ═══════════════════════════════════════════════════════════════════════════════
# GENERIC RETRY IMPLEMENTATION  (used by tests and Gemini provider)
# ═══════════════════════════════════════════════════════════════════════════════

async def _call_with_retry(coro_factory) -> object:
    """
    Bounded retry for Gemini SDK errors (503 ServerError, 429 ClientError).
    
    This is the generic retry implementation used in tests.
    For a callable that raises google.genai.errors (ServerError, ClientError),
    retries on codes in _RETRYABLE_SERVER_CODES (503) and _RETRYABLE_CLIENT_CODES (429).
    Propagates non-retryable errors (401, 403, 404, 500) immediately.
    Raises GeminiUnavailableError when retries are exhausted.
    """
    from google.genai import errors as genai_errors

    last_exc: Exception | None = None

    for attempt, delay in enumerate([0.0, *_RETRY_DELAYS], start=1):
        if delay:
            await asyncio.sleep(delay)
        try:
            return await coro_factory()
        except genai_errors.ServerError as exc:
            if exc.code in _RETRYABLE_SERVER_CODES:
                last_exc = exc
                logger.debug(f"Retryable server error (attempt {attempt}): {exc.code}")
            else:
                # Non-retryable server error (e.g., 500, 404)
                raise
        except genai_errors.ClientError as exc:
            if exc.code in _RETRYABLE_CLIENT_CODES:
                last_exc = exc
                logger.debug(f"Retryable client error (attempt {attempt}): {exc.code}")
            else:
                # Non-retryable client error (e.g., 401, 403, 400)
                raise

    raise GeminiUnavailableError(
        f"Gemini API is temporarily unavailable (last error: {last_exc}). "
        f"Tried {len(_RETRY_DELAYS) + 1} times with exponential backoff."
    ) from last_exc


# Alias for backward-compatibility with existing code
_gemini_call_with_retry = _call_with_retry


async def _gemini_generate_code(
    question: str,
    df: pd.DataFrame,
    filename: str,
    context_history: list | None = None,
    target_currency: str | None = None,
) -> str:
    """Generate analysis code via Gemini (legacy path)."""
    from google import genai as google_genai
    from google.genai import types
    from google.genai import errors as genai_errors  # noqa: F401 — needed by retry

    client = google_genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))
    prompt = _build_prompt(
        question=question,
        df=df,
        filename=filename,
        context_history=context_history,
        target_currency=target_currency,
    )
    config = types.GenerateContentConfig(temperature=0.0, max_output_tokens=512)

    response = await _gemini_call_with_retry(
        lambda: client.aio.models.generate_content(
            model=_GEMINI_MODEL,
            contents=prompt,
            config=config,
        )
    )
    return _strip_fences(response.text.strip())


async def _gemini_generate_suggestions(df: pd.DataFrame, filename: str) -> list[str]:
    """Generate suggestions via Gemini (legacy path)."""
    from google import genai as google_genai
    from google.genai import types

    client = google_genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))
    prompt = _build_suggestion_prompt(df, filename)
    config = types.GenerateContentConfig(temperature=0.3, max_output_tokens=256)

    response = await _gemini_call_with_retry(
        lambda: client.aio.models.generate_content(
            model=_GEMINI_MODEL,
            contents=prompt,
            config=config,
        )
    )
    text = response.text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(l for l in lines if not l.startswith("```")).strip()
    suggestions = json.loads(text)
    if isinstance(suggestions, list):
        return [str(s) for s in suggestions[:4]]
    return []


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API  (unchanged signatures — analyst.py and routes.py require no edits)
# ═══════════════════════════════════════════════════════════════════════════════

async def generate_analysis_code(
    question: str,
    df: pd.DataFrame,
    filename: str,
    context_history: list | None = None,
    target_currency: str | None = None,
) -> str:
    """
    Generate Python/pandas code to answer *question* against *df*.

    Routes to Groq (default) or Gemini (legacy) based on LLM_PROVIDER env var.
    Raises GeminiUnavailableError when the provider is exhausted so that
    analyst.py can route to the local deterministic fallback.
    """
    logger.info("generate_analysis_code provider=%s", LLM_PROVIDER)
    if LLM_PROVIDER == "gemini":
        return await _gemini_generate_code(question, df, filename, context_history, target_currency)
    return await _groq_generate_code(question, df, filename, context_history, target_currency)


async def generate_question_suggestions(df: pd.DataFrame, filename: str) -> list[str]:
    """
    Generate 4 schema-aware question suggestions for the uploaded dataset.

    Falls back silently to schema-derived generic suggestions on any failure.
    """
    logger.info("generate_question_suggestions provider=%s", LLM_PROVIDER)
    try:
        if LLM_PROVIDER == "gemini":
            return await _gemini_generate_suggestions(df, filename)
        return await _groq_generate_suggestions(df, filename)
    except Exception:
        pass

    # Schema-derived fallback suggestions (no LLM required)
    cols = list(df.columns)
    fallback = [
        "How many rows are in this dataset?",
        "What are the missing values in the data?",
    ]
    if cols:
        fallback.append(f"What are the unique values in '{cols[0]}'?")
    if len(cols) > 1:
        fallback.append(f"What is the summary statistics for '{cols[1]}'?")
    return fallback[:4]
