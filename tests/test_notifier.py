# sovereign-survival-agent/tests/test_notifier.py
"""
Test Suite for Agent Alert & Notifier.
"""
import pytest
from core.notifier import AgentNotifier


def test_agent_notifier_records_and_dispatches_alerts():
    notifier = AgentNotifier()
    alert = notifier.dispatch_alert(
        title="[TEST] Agent Heartbeat",
        message="Running automated unit test suite.",
        level="INFO"
    )

    assert alert.title == "[TEST] Agent Heartbeat"
    assert len(notifier.recent_alerts) > 0
    assert notifier.recent_alerts[-1].title == "[TEST] Agent Heartbeat"


def test_agent_notifier_formats_bounty_solved_alert():
    notifier = AgentNotifier()
    alert = notifier.notify_bounty_solved(
        bounty_title="Fix Reentrancy Guard in Vault",
        reward_usdc=150.0,
        repo_name="base-org/staking-vault",
        issue_number=10,
        pr_preview_url="https://github.com/base-org/staking-vault/pull/1",
        attempts=1,
        cost_usdc=0.00005
    )

    assert "150.00" in alert.title
    assert "base-org/staking-vault#10" in alert.title
    assert alert.level == "SUCCESS"
