#!/usr/bin/env python3
"""Test that reproducible proof is correctly generated."""

import sys
import pandas as pd
from core.analyst import DataAnalyst

# Create a small test dataframe
df = pd.DataFrame({
    "product": ["Widget A", "Widget B", "Gadget X"],
    "sales": [100.5, 85.0, 220.0],
    "quantity": [10, 7, 15]
})

# Sample generated code (what the LLM would return)
generated_code = 'result = df["sales"].sum()'

# Test the reproducible proof builder
analyst = DataAnalyst()
proof = analyst._build_reproducible_proof(
    generated_code=generated_code,
    filename="test_sales.csv"
)

print("=== Reproducible Proof Generated ===")
print(proof)
print("\n=== Verification ===")

# Check that it contains required elements
checks = {
    "imports pandas": "import pandas as pd" in proof,
    "imports numpy": "import numpy as np" in proof,
    "loads CSV": 'pd.read_csv("test_sales.csv")' in proof,
    "contains generated code": generated_code in proof,
    "prints result": 'print("Result:", result)' in proof,
    "has docstring": '"""' in proof,
}

all_pass = all(checks.values())
for check, passed in checks.items():
    symbol = "✓" if passed else "✗"
    print(f"{symbol} {check}")

if all_pass:
    print("\n✓ All checks passed!")
    sys.exit(0)
else:
    print("\n✗ Some checks failed")
    sys.exit(1)
