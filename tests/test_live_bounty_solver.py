# sovereign-survival-agent/tests/test_live_bounty_solver.py
"""
Test Suite for Bountycaster Listener and GitHub Autonomous PR Solver.
"""
import pytest
from core.models import AgentState, Bounty, TaskType
from channels.bountycaster_listener import BountycasterListener
from core.github_solver import GitHubSolverEngine


def test_bountycaster_listener_parses_live_api_response():
    listener = BountycasterListener()
    sample_raw = [
        {
            "cast_hash": "0x1234567890abcdef",
            "author_username": "bountyhunter",
            "author_address": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
            "text": "Fix vulnerability on github.com/community/smart-vault/issues/10 (Reward: 75 USDC)",
            "amount_usd": 75.0,
            "token_symbol": "USDC"
        }
    ]
    bounties = listener._parse_api_response(sample_raw, min_reward=25.0)
    
    assert len(bounties) == 1
    b = bounties[0]
    assert b.reward_usdc == 75.0
    assert b.difficulty_score > 0.0
    assert b.issuer_address.startswith("0x")
    assert b.task_type == TaskType.SMART_CONTRACT_AUDIT


def test_github_solver_engine_generates_valid_pull_request():
    agent_addr = "0x3C187eC3757e1C76aAC4D83f97608b3cA3191FcA"
    solver = GitHubSolverEngine(agent_address=agent_addr)

    bounty = Bounty(
        bounty_id="bc_live_01",
        title="Fix Reentrancy Guard in Staking Contract",
        description="Bounty for fixing reentrancy issue: https://github.com/community/staking-vault/issues/42",
        task_type=TaskType.SMART_CONTRACT_AUDIT,
        reward_usdc=75.0,
        deadline_ticks=25,
        difficulty_score=0.55,
        issuer_address="0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
        escrow_address="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    )

    success, pr, note = solver.solve_bounty_issue(bounty)
    
    assert success is True
    assert pr is not None
    assert pr.repo_owner == "community"
    assert pr.repo_name == "staking-vault"
    assert pr.issue_number == 42
    assert "Checks-Effects-Interactions" in pr.pr_body
    assert pr.target_payout_address == agent_addr
    assert len(pr.diff_patch) > 0
