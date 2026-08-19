# sovereign-survival-agent/tests/test_bounty_scanner.py
"""
Test Suite for Live GitHub & Algora Bounty Scanner.
"""
import pytest
from channels.github_bounty_scanner import GitHubBountyScanner, ScannedBounty
from core.models import TaskType


def test_github_bounty_scanner_scans_and_ranks_by_ev():
    scanner = GitHubBountyScanner()
    bounties = scanner.scan_all_bounties(min_reward_usdc=50.0, limit=10)

    assert len(bounties) > 0
    # Verify sorting by EV score descending
    for i in range(len(bounties) - 1):
        assert bounties[i].ev_score >= bounties[i+1].ev_score

    for b in bounties:
        assert b.reward_usdc >= 50.0
        assert b.url.startswith("https://")
        assert b.repo_full_name != ""
        assert b.task_type in (
            TaskType.SMART_CONTRACT_AUDIT,
            TaskType.UNIT_TEST_GEN,
            TaskType.CODE_BUG_FIX,
            TaskType.MARKET_INTELLIGENCE
        )


def test_github_bounty_scanner_extracts_reward_amounts():
    scanner = GitHubBountyScanner()

    assert scanner._extract_reward_amount("Bounty for $150 to fix bug") == 150.0
    assert scanner._extract_reward_amount("Algora reward: 250 USDC for PR") == 250.0
    assert scanner._extract_reward_amount("Claim 0.05 ETH reward") > 0.0
    assert scanner._extract_reward_amount("Standard issue with no reward") == 0.0
