"""
file_parser.py — ProofAI file parsing layer.

Accepts raw bytes + filename and returns a dict with:
  - df:           pd.DataFrame (or None if not applicable)
  - text_content: str (for PDF/TXT/HTML fallback)
  - file_type:    str (csv, excel, json, html, txt, pdf)
  - parse_error:  str or None
  - row_count:    int
  - col_count:    int
  - columns:      list[str]
  - dtypes:       dict
  - missing_values: dict
  - preview:      list[dict]
  - is_tabular:   bool
"""

import io
import json
import traceback
import pandas as pd


SUPPORTED_EXTENSIONS = {
    ".csv": "csv",
    ".xlsx": "excel",
    ".xls": "excel",
    ".json": "json",
    ".html": "html",
    ".htm": "html",
    ".txt": "txt",
    ".pdf": "pdf",
}

MAX_PREVIEW_ROWS = 10


def get_file_type(filename: str) -> str | None:
    """Return normalised file type string or None if unsupported."""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return SUPPORTED_EXTENSIONS.get(ext)


def parse_file(contents: bytes, filename: str) -> dict:
    """
    Parse uploaded file bytes into an analysis-ready structure.
    Always returns a dict — never raises.
    """
    file_type = get_file_type(filename)

    if file_type is None:
        return _error_result(
            filename=filename,
            file_type="unknown",
            message=(
                f"Unsupported file type. Supported formats: "
                f"{', '.join(sorted(SUPPORTED_EXTENSIONS.keys()))}"
            ),
        )

    try:
        if file_type == "csv":
            return _parse_csv(contents, filename)
        elif file_type == "excel":
            return _parse_excel(contents, filename)
        elif file_type == "json":
            return _parse_json(contents, filename)
        elif file_type == "html":
            return _parse_html(contents, filename)
        elif file_type == "txt":
            return _parse_txt(contents, filename)
        elif file_type == "pdf":
            return _parse_pdf(contents, filename)
    except Exception:
        return _error_result(
            filename=filename,
            file_type=file_type,
            message=f"Unexpected error during parsing: {traceback.format_exc()}",
        )

    return _error_result(filename=filename, file_type=file_type, message="Unhandled file type.")


# ─── Individual parsers ────────────────────────────────────────────────────────

def _parse_csv(contents: bytes, filename: str) -> dict:
    try:
        df = pd.read_csv(io.BytesIO(contents))
        return _tabular_result(df, filename, "csv")
    except Exception as e:
        return _error_result(filename, "csv", f"Failed to parse CSV: {e}")


def _parse_excel(contents: bytes, filename: str) -> dict:
    try:
        df = pd.read_excel(io.BytesIO(contents))
        return _tabular_result(df, filename, "excel")
    except Exception as e:
        return _error_result(filename, "excel", f"Failed to parse Excel file: {e}")


def _parse_json(contents: bytes, filename: str) -> dict:
    try:
        text = contents.decode("utf-8", errors="replace")
        data = json.loads(text)

        # Try to convert to DataFrame
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            # Try records orientation
            try:
                df = pd.DataFrame.from_dict(data)
            except Exception:
                # Wrap as single-row dict
                df = pd.DataFrame([data])
        else:
            return _error_result(
                filename, "json",
                "JSON content is not a list or object — cannot convert to tabular data."
            )

        if df.empty or len(df.columns) == 0:
            return _error_result(filename, "json", "JSON parsed to an empty table.")

        return _tabular_result(df, filename, "json")
    except json.JSONDecodeError as e:
        return _error_result(filename, "json", f"Invalid JSON: {e}")
    except Exception as e:
        return _error_result(filename, "json", f"Failed to parse JSON: {e}")


def _parse_html(contents: bytes, filename: str) -> dict:
    try:
        tables = pd.read_html(io.BytesIO(contents))
        if not tables:
            return _error_result(
                filename, "html",
                "No HTML tables found in the file. Cannot extract structured data."
            )
        # Use the largest table
        df = max(tables, key=lambda t: t.size)
        return _tabular_result(df, filename, "html")
    except ValueError as e:
        # pd.read_html raises ValueError when no tables found
        text_preview = contents.decode("utf-8", errors="replace")[:2000]
        return {
            **_base_result(filename, "html"),
            "is_tabular": False,
            "text_content": text_preview,
            "parse_error": f"No HTML tables found: {e}. Showing raw text preview.",
        }
    except Exception as e:
        return _error_result(filename, "html", f"Failed to parse HTML: {e}")


def _parse_txt(contents: bytes, filename: str) -> dict:
    text = contents.decode("utf-8", errors="replace")

    # Try CSV-style parsing first (tab or comma separated)
    for sep in ["\t", ",", "|", ";"]:
        try:
            df = pd.read_csv(io.StringIO(text), sep=sep, engine="python")
            if len(df.columns) >= 2 and len(df) >= 1:
                return _tabular_result(df, filename, "txt")
        except Exception:
            continue

    # Fall back to plain text
    return {
        **_base_result(filename, "txt"),
        "is_tabular": False,
        "text_content": text[:3000],
        "parse_error": (
            "Text file does not appear to contain structured tabular data. "
            "Analytical questions cannot be answered reliably from unstructured text."
        ),
    }


def _parse_pdf(contents: bytes, filename: str) -> dict:
    """Attempt text+table extraction from PDF using pdfplumber if available."""
    try:
        import pdfplumber  # optional dependency
        import io as _io

        all_text = []
        all_tables = []

        with pdfplumber.open(_io.BytesIO(contents)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                all_text.append(page_text)
                page_tables = page.extract_tables()
                for tbl in page_tables:
                    if tbl:
                        all_tables.append(tbl)

        # Try tables first
        if all_tables:
            best = max(all_tables, key=lambda t: len(t))
            if len(best) > 1:
                header = [str(c) if c else f"col_{i}" for i, c in enumerate(best[0])]
                rows = [[str(c) if c is not None else "" for c in row] for row in best[1:]]
                df = pd.DataFrame(rows, columns=header)
                # Try numeric conversion — only replace a column when every
                # existing non-null value converts successfully.  This preserves
                # text columns such as "Region" (South/North) and currency
                # strings like "INR 184,000" that would become NaN with
                # errors="coerce" on a mixed/text column.
                # Compatible with pandas ≥ 3.0 (errors="ignore" was removed).
                for col in df.columns:
                    converted = pd.to_numeric(df[col], errors="coerce")
                    original_non_null = df[col].notna().sum()
                    converted_non_null = converted.notna().sum()
                    if converted_non_null == original_non_null:
                        # All non-null values survived → safe to use numeric
                        df[col] = converted
                    # Otherwise keep the original column unchanged
                return _tabular_result(df, filename, "pdf")

        # Fall back to text
        full_text = "\n".join(all_text).strip()
        if not full_text:
            return _error_result(
                filename, "pdf",
                "PDF appears to be image-based or empty. Text extraction failed."
            )

        return {
            **_base_result(filename, "pdf"),
            "is_tabular": False,
            "text_content": full_text[:3000],
            "parse_error": (
                "No structured tables found in PDF. Showing extracted text. "
                "Precise analytical questions cannot be reliably answered."
            ),
        }

    except ImportError:
        # pdfplumber not installed
        return {
            **_base_result(filename, "pdf"),
            "is_tabular": False,
            "text_content": "",
            "parse_error": (
                "PDF parsing requires the 'pdfplumber' library which is not installed. "
                "Install it with: pip install pdfplumber"
            ),
        }
    except Exception as e:
        return _error_result(filename, "pdf", f"Failed to parse PDF: {e}")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _base_result(filename: str, file_type: str) -> dict:
    return {
        "filename": filename,
        "file_type": file_type,
        "is_tabular": False,
        "df": None,
        "text_content": "",
        "parse_error": None,
        "row_count": 0,
        "col_count": 0,
        "columns": [],
        "dtypes": {},
        "missing_values": {},
        "preview": [],
    }


def _error_result(filename: str, file_type: str, message: str) -> dict:
    return {
        **_base_result(filename, file_type),
        "parse_error": message,
    }


def _tabular_result(df: pd.DataFrame, filename: str, file_type: str) -> dict:
    # Sanitise column names
    df.columns = [str(c) for c in df.columns]

    preview_rows = df.head(MAX_PREVIEW_ROWS).copy()
    # Convert non-serialisable types for JSON
    for col in preview_rows.columns:
        preview_rows[col] = preview_rows[col].astype(object).where(
            preview_rows[col].notna(), None
        )

    return {
        "filename": filename,
        "file_type": file_type,
        "is_tabular": True,
        "df": df,
        "text_content": "",
        "parse_error": None,
        "row_count": len(df),
        "col_count": len(df.columns),
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "missing_values": {col: int(v) for col, v in df.isnull().sum().items()},
        "preview": preview_rows.to_dict(orient="records"),
    }
