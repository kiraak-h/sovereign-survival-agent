# sovereign-survival-agent/tests/test_github_dispatch.py
"""
Test Suite for GitHub Pull Request Dispatch & Fallback Mechanics.
"""
import pytest
from core.github_solver import GitHubSolverEngine, PullRequestPayload


def test_github_dispatch_generates_preview_when_unauthenticated():
    engine = GitHubSolverEngine(agent_address="0x3C187eC3757e1C76aAC4D83f97608b3cA3191FcA")
    pr = PullRequestPayload(
        repo_owner="base-org",
        repo_name="staking-vault",
        issue_number=10,
        branch_name="agent-fix/staking-vault-10",
        pr_title="fix: Reentrancy vulnerability",
        pr_body="Detailed PR description with Base L2 payout address",
        diff_patch="--- a/Vault.sol\n+++ b/Vault.sol",
        target_payout_address="0x3C187eC3757e1C76aAC4D83f97608b3cA3191FcA"
    )

    info = engine.dispatch_pull_request(pr)
    assert info is not None
    assert "pr_preview_url" in info
    assert "https://github.com/base-org/staking-vault/pull/new/agent-fix/staking-vault-10" in info["pr_preview_url"]
