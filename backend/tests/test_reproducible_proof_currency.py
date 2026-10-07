"""
tests/test_reproducible_proof_currency.py — Test currency conversion reproducible proof execution.

Ensures that generated proof code for INR/USD conversions can run standalone.
"""

import pytest
import pandas as pd
import tempfile
import os
from core.analyst import DataAnalyst


@pytest.mark.anyio
async def test_inr_conversion_proof_executes():
    """Test that INR conversion proof code can execute standalone."""
    # Create sample dataset with mixed currencies
    df = pd.DataFrame({
        "Transaction_ID": [1, 2, 3],
        "Paid_Amount": [100.0, 1000.0, 50.0],
        "Currency": ["USD", "INR", "USD"]
    })
    
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        df.to_csv(f.name, index=False)
        csv_path = f.name
        filename = os.path.basename(csv_path)
    
    try:
        # Generate analysis with INR conversion
        analyst = DataAnalyst()
        result = await analyst.analyze(
            question="What is the total paid amount?",
            df=df,
            filename=filename,
            target_currency="INR"
        )
        
        assert result["status"] == "success"
        assert result["verification"] == "VERIFIED"
        assert "reproducible_proof" in result
        
        proof_code = result["reproducible_proof"]
        
        # Verify proof contains required elements
        assert "import pandas as pd" in proof_code
        assert "USD_TO_INR = 83.50" in proof_code
        assert "Amount_INR" in proof_code
        assert ".apply(" in proof_code or "apply(convert" in proof_code
        assert "def convert" in proof_code or "lambda row:" in proof_code
        
        # Execute the proof code
        exec_globals = {}
        # Replace filename in proof with actual path
        proof_code_executable = proof_code.replace(f'"{filename}"', f'"{csv_path}"')
        exec(proof_code_executable, exec_globals)
        
        # Verify execution succeeded (no exceptions thrown)
        # The proof should have executed without errors
        
    finally:
        # Cleanup
        if os.path.exists(csv_path):
            os.unlink(csv_path)


@pytest.mark.anyio
async def test_usd_conversion_proof_executes():
    """Test that USD conversion proof code can execute standalone."""
    # Create sample dataset with mixed currencies
    df = pd.DataFrame({
        "Transaction_ID": [1, 2, 3],
        "Paid_Amount": [100.0, 8350.0, 50.0],
        "Currency": ["USD", "INR", "USD"]
    })
    
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        df.to_csv(f.name, index=False)
        csv_path = f.name
        filename = os.path.basename(csv_path)
    
    try:
        # Generate analysis with USD conversion
        analyst = DataAnalyst()
        result = await analyst.analyze(
            question="What is the total paid amount?",
            df=df,
            filename=filename,
            target_currency="USD"
        )
        
        assert result["status"] == "success"
        assert result["verification"] == "VERIFIED"
        assert "reproducible_proof" in result
        
        proof_code = result["reproducible_proof"]
        
        # Verify proof contains required elements
        assert "import pandas as pd" in proof_code
        assert "USD_TO_INR = 83.50" in proof_code
        assert "Amount_USD" in proof_code
        assert ".apply(" in proof_code or "apply(convert" in proof_code
        assert "def convert" in proof_code or "lambda row:" in proof_code
        
        # Execute the proof code
        exec_globals = {}
        # Replace filename in proof with actual path
        proof_code_executable = proof_code.replace(f'"{filename}"', f'"{csv_path}"')
        exec(proof_code_executable, exec_globals)
        
        # Verify execution succeeded (no exceptions thrown)
        
    finally:
        # Cleanup
        if os.path.exists(csv_path):
            os.unlink(csv_path)


@pytest.mark.anyio
async def test_proof_code_format():
    """Test that proof code follows the required clean format."""
    df = pd.DataFrame({
        "Transaction_ID": [1, 2],
        "Paid_Amount": [100.0, 1000.0],
        "Currency": ["USD", "INR"]
    })
    
    analyst = DataAnalyst()
    result = await analyst.analyze(
        question="What is the total paid amount?",
        df=df,
        filename="test.csv",
        target_currency="INR"
    )
    
    proof_code = result["reproducible_proof"]
    
    # Verify clean formatting
    # Currency conversion proofs have a simpler format without docstring
    assert "import pandas as pd" in proof_code
    assert "\\#" not in proof_code  # No escaped markdown
    assert "\\*" not in proof_code  # No escaped markdown
    assert "pd.to_numeric" in proof_code  # Should include numeric conversion
    assert "errors='coerce'" in proof_code  # Should handle non-numeric gracefully
    assert "USD_TO_INR" in proof_code  # Should have conversion rate
    
    # Verify no markdown formatting in executable code
    lines = proof_code.split('\n')
    for line in lines:
        if line.strip() and not line.strip().startswith('#'):
            # Executable lines should not have markdown
            assert not line.startswith('```')
            assert not line.startswith('*')
