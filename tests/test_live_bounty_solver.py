# sovereign-survival-agent/tests/test_live_bounty_solver.py
"""
Test Suite for Bountycaster Listener and GitHub Autonomous PR Solver.
"""
import pytest
from core.models import AgentState, Bounty, TaskType
from channels.bountycaster_listener import BountycasterListener
from core.github_solver import GitHubSolverEngine


def test_bountycaster_listener_fetches_and_classifies_bounties():
    listener = BountycasterListener()
    bounties = listener.fetch_open_bounties(min_reward_usdc=25.0, limit=5)
    
    assert len(bounties) > 0
    for b in bounties:
        assert b.reward_usdc >= 25.0
        assert b.difficulty_score > 0.0
        assert b.issuer_address.startswith("0x")


def test_github_solver_engine_generates_valid_pull_request():
    agent_addr = "0xA560415e3c118eD1591121b956ef36A40AEb9271"
    solver = GitHubSolverEngine(agent_address=agent_addr)

    bounty = Bounty(
        bounty_id="bc_live_01",
        title="Fix Reentrancy Guard in Base L2 Staking Contract",
        description="Bounty for fixing reentrancy issue: https://github.com/base-org/sample-vault/issues/42",
        task_type=TaskType.SMART_CONTRACT_AUDIT,
        reward_usdc=75.0,
        deadline_ticks=25,
        difficulty_score=0.55,
        issuer_address="0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
        escrow_address="0x_bountycaster_base_escrow"
    )

    success, pr, note = solver.solve_bounty_issue(bounty)
    
    assert success is True
    assert pr is not None
    assert pr.repo_owner == "base-org"
    assert pr.repo_name == "sample-vault"
    assert pr.issue_number == 42
    assert "Checks-Effects-Interactions" in pr.pr_body
    assert pr.target_payout_address == agent_addr
    assert len(pr.diff_patch) > 0
