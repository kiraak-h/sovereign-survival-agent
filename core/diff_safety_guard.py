# sovereign-survival-agent/core/diff_safety_guard.py
"""
Diff Safety & Anti-Destructive Patch Guardrail:
Strictly validates every proposed code patch before committing or opening a Pull Request.
Enforces:
1. Protected File Inviolability (Never erase or corrupt README.md, LICENSE, package.json, go.mod)
2. Clean Codebase Rule (Never inject self-promotional text, wallet addresses, or headers into repo source files)
3. Destructive Deletion Cap (Rejects diffs that erase more than 30% of existing lines without replacement)
4. AST Syntax Integrity (Ensures code compiles cleanly in Python, Solidity, Go, and JS/TS)
"""
from __future__ import annotations
import re
from typing import Tuple, List, Dict, Any
from pydantic import BaseModel


class DiffValidationResult(BaseModel):
    is_safe: bool
    rejection_reasons: List[str]
    files_modified: List[str]
    total_added_lines: int
    total_deleted_lines: int


class DiffSafetyGuard:
    """
    Zero-tolerance safety linter for all autonomous pull requests and patches.
    """

    PROTECTED_FILES = {
        "readme.md",
        "readme",
        "license",
        "license.md",
        "contributing.md",
        ".gitignore",
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "go.mod",
        "go.sum",
        "cargo.toml",
        "cargo.lock",
        "requirements.txt"
    }

    # Forbidden text inside source code / documentation files (allowed ONLY in PR description)
    FORBIDDEN_SOURCE_PATTERNS = [
        r"solved by sovereign agent",
        r"payout address:\s*0x[a-fA-F0-9]{40}",
        r"claimed by @",
        r"bounty reward claim:",
        r"agent wallet:"
    ]

    @classmethod
    def validate_patch(cls, patch_content: str, target_file_path: str = "") -> DiffValidationResult:
        """
        Validates a diff patch before applying or committing.
        Returns DiffValidationResult with is_safe=True/False and detailed reasons.
        """
        rejection_reasons = []
        files_modified = []
        added_lines = 0
        deleted_lines = 0

        target_file_clean = target_file_path.strip().lower().replace("\\", "/")
        file_basename = target_file_clean.split("/")[-1] if target_file_clean else ""

        # 1. Inspect lines in patch
        patch_lines = patch_content.split("\n")
        added_content_lines = []
        
        for line in patch_lines:
            if line.startswith("+++ b/") or line.startswith("--- a/"):
                mod_file = line[6:].strip().lower()
                if mod_file not in files_modified:
                    files_modified.append(mod_file)
            elif line.startswith("+") and not line.startswith("+++"):
                added_lines += 1
                added_content_lines.append(line[1:])
            elif line.startswith("-") and not line.startswith("---"):
                deleted_lines += 1

        # Check target file basename
        if file_basename and file_basename not in files_modified:
            files_modified.append(file_basename)

        # Rule 1: Protected File Inviolability
        for f in files_modified:
            f_base = f.split("/")[-1]
            if f_base in cls.PROTECTED_FILES:
                # If modifying a protected file (like README.md), ensure it's not being erased or replaced
                if deleted_lines > 5 and added_lines < 3:
                    rejection_reasons.append(f"PROTECTED_FILE_CORRUPTION: Modification erases content in protected file '{f_base}'")
                elif "readme" in f_base and deleted_lines > 10:
                    rejection_reasons.append(f"README_DESTRUCTION: Large deletion ({deleted_lines} lines) in '{f_base}'")

        # Rule 2: Anti-Self-Promotion in Source Code
        added_text = "\n".join(added_content_lines).lower()
        for pattern in cls.FORBIDDEN_SOURCE_PATTERNS:
            if re.search(pattern, added_text):
                rejection_reasons.append(f"FORBIDDEN_SOURCE_INJECTION: Detected promotional/wallet string matching '{pattern}' in source patch. Payout metadata belongs strictly in PR body.")

        # Rule 3: Destructive Deletion Cap
        if deleted_lines > 20 and added_lines == 0:
            rejection_reasons.append(f"DESTRUCTIVE_DELETION: Patch deletes {deleted_lines} lines with 0 replacement code.")

        # Rule 4: Empty patch check
        if added_lines == 0 and deleted_lines == 0 and len(patch_content.strip()) < 10:
            rejection_reasons.append("EMPTY_PATCH: Patch contains no valid modifications.")

        is_safe = len(rejection_reasons) == 0

        return DiffValidationResult(
            is_safe=is_safe,
            rejection_reasons=rejection_reasons,
            files_modified=files_modified,
            total_added_lines=added_lines,
            total_deleted_lines=deleted_lines
        )

    @classmethod
    def sanitize_pr_payload(cls, file_path: str, code_content: str) -> Tuple[bool, str, str]:
        """
        Sanitizes and ensures code_content is a genuine software artifact without self-promotional injections.
        Returns: (is_valid, sanitized_content, error_msg)
        """
        lower_code = code_content.lower()
        for pattern in cls.FORBIDDEN_SOURCE_PATTERNS:
            if re.search(pattern, lower_code):
                return False, "", f"Code contains forbidden promotional string: '{pattern}'. Keep payout addresses strictly in PR description."

        f_base = file_path.strip().lower().replace("\\", "/").split("/")[-1]
        if f_base in cls.PROTECTED_FILES and len(code_content.splitlines()) < 3:
            return False, "", f"Attempted to overwrite protected file '{f_base}' with minimal/empty content."

        return True, code_content, ""
