# sovereign-survival-agent/tests/test_multi_sandbox.py
"""
Test Suite for Multi-Language Sandbox Runner.
"""
import pytest
import tempfile
from pathlib import Path
from core.multi_sandbox_runner import MultiSandboxRunner
from core.models import TaskType


def test_multi_sandbox_validates_python():
    runner = MultiSandboxRunner()
    with tempfile.TemporaryDirectory() as td:
        code = "def add(a, b):\n    return a + b\n\ndef test_add():\n    assert add(2, 3) == 5\n"
        is_valid, lang, msg = runner.validate_code(TaskType.UNIT_TEST_GEN, code, Path(td))
        assert is_valid is True
        assert "Python" in lang


def test_multi_sandbox_validates_javascript_typescript():
    runner = MultiSandboxRunner()
    with tempfile.TemporaryDirectory() as td:
        code = "const calculateFee = (amount) => { return amount * 0.05; };\nexport default calculateFee;\n"
        is_valid, lang, msg = runner.validate_code(TaskType.CODE_BUG_FIX, code, Path(td))
        assert is_valid is True
        assert "JavaScript" in lang or "TypeScript" in lang


def test_multi_sandbox_validates_solidity():
    runner = MultiSandboxRunner()
    with tempfile.TemporaryDirectory() as td:
        code = "// SPDX-License-Identifier: MIT\npragma solidity 0.8.20;\ncontract Token { string public name = 'T'; }\n"
        is_valid, lang, msg = runner.validate_code(TaskType.SMART_CONTRACT_AUDIT, code, Path(td))
        assert is_valid is True
        assert "Solidity" in lang
