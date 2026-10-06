import sys
import io
import traceback
import pandas as pd
import numpy as np


def execute_code(code: str, df: pd.DataFrame) -> dict:
    """
    Safely execute generated Python code in a restricted environment.
    The code has access to `df` (the DataFrame), pandas, and numpy.
    It should assign its final answer to a variable named `result`.
    """
    # Capture stdout
    stdout_capture = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = stdout_capture

    local_env = {
        "df": df.copy(),
        "pd": pd,
        "np": np,
        "result": None,
    }

    try:
        exec(compile(code, "<generated>", "exec"), {"__builtins__": __builtins__}, local_env)
        output = local_env.get("result")

        # If result was not set, try capturing printed output
        if output is None:
            printed = stdout_capture.getvalue().strip()
            output = printed if printed else "Code ran but produced no output. Did you set `result = ...`?"

        return {"success": True, "output": output, "error": None}

    except Exception:
        return {
            "success": False,
            "output": None,
            "error": traceback.format_exc(),
        }
    finally:
        sys.stdout = old_stdout
