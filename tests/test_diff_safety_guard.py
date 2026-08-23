# sovereign-survival-agent/tests/test_diff_safety_guard.py
"""
Test Suite for Diff Safety & Anti-Destructive Patch Guardrail.
"""
import pytest
from core.diff_safety_guard import DiffSafetyGuard, DiffValidationResult


def test_guard_rejects_readme_destruction():
    bad_patch = """--- a/README.md
+++ b/README.md
@@ -1,15 +1,1 @@
-# Project Title
-Detailed overview
-## Installation
-Run setup
-## Usage
-Use tool
+# Solved by Sovereign Agent
+Payout Address: 0x3C187eC3757e1C76aAC4D83f97608b3cA3191FcA
"""
    res: DiffValidationResult = DiffSafetyGuard.validate_patch(bad_patch, "README.md")
    assert res.is_safe is False
    assert any("README_DESTRUCTION" in r or "PROTECTED_FILE_CORRUPTION" in r for r in res.rejection_reasons)
    assert any("FORBIDDEN_SOURCE_INJECTION" in r for r in res.rejection_reasons)


def test_guard_rejects_promotional_wallet_injection():
    injected_code = """def calculate_yield():
    # Solved by Sovereign Agent
    # Payout Address: 0x3C187eC3757e1C76aAC4D83f97608b3cA3191FcA
    return 0.05
"""
    is_valid, _, err = DiffSafetyGuard.sanitize_pr_payload("src/calc.py", injected_code)
    assert is_valid is False
    assert "forbidden promotional string" in err


def test_guard_accepts_clean_code_fix():
    clean_patch = """--- a/contracts/Vault.sol
+++ b/contracts/Vault.sol
@@ -10,3 +10,4 @@
     balances[msg.sender] = 0;
+    (bool s, ) = msg.sender.call{value: bal}("");
+    require(s, "Transfer failed");
"""
    res: DiffValidationResult = DiffSafetyGuard.validate_patch(clean_patch, "contracts/Vault.sol")
    assert res.is_safe is True
    assert len(res.rejection_reasons) == 0


def test_guard_rejects_empty_patch():
    res: DiffValidationResult = DiffSafetyGuard.validate_patch("", "file.py")
    assert res.is_safe is False
    assert any("EMPTY_PATCH" in r for r in res.rejection_reasons)
