# sovereign-survival-agent/tests/test_self_correcting_solver.py
"""
Test Suite for Multi-Tier LLM Gateway and Self-Correcting Closed-Loop Coding Solver.
"""
import pytest
from core.models import AgentState, Bounty, TaskType, ModelTier
from core.metabolism import MetabolismManager
from core.llm_gateway import LLMGateway
from core.self_correcting_solver import SelfCorrectingSolver


def test_llm_gateway_calculates_cost_and_deducts_metabolism():
    state = AgentState(
        agent_address="0x3C187eC3757e1C76aAC4D83f97608b3cA3191FcA",
        session_key_address="0x97F88CA501AF4A75C9F8fd8C56d230a43e407134",
        treasury_usdc=25.0
    )
    metabolism = MetabolismManager(state)
    gateway = LLMGateway(metabolism=metabolism)

    resp = gateway.generate(
        prompt="Write a secure Solidity reentrancy guard",
        model_tier=ModelTier.CHEAP_FLASH
    )

    assert resp.total_tokens > 0
    assert resp.cost_usdc >= 0.0
    assert len(resp.content) > 0
    # Verify compute burn recorded as a deduction in metabolism ledger
    assert len(metabolism.ledger) > 0
    last_entry = metabolism.ledger[-1]
    assert last_entry.amount_usdc < 0
    assert abs(last_entry.amount_usdc) > 0



def test_self_correcting_solver_verifies_solidity_bounty():
    agent_addr = "0x3C187eC3757e1C76aAC4D83f97608b3cA3191FcA"
    gateway = LLMGateway()
    solver = SelfCorrectingSolver(agent_address=agent_addr, llm_gateway=gateway)

    bounty = Bounty(
        bounty_id="bc_solve_01",
        title="Fix SWC-107 Reentrancy in Base Staking Vault",
        description="Fix vault issue at https://github.com/base-org/staking-vault/issues/10",
        task_type=TaskType.SMART_CONTRACT_AUDIT,
        reward_usdc=150.0,
        deadline_ticks=25,
        difficulty_score=0.6,
        issuer_address="0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
        escrow_address="0x_escrow_base"
    )

    result = solver.solve_with_verification(bounty, max_attempts=3, model_tier=ModelTier.CHEAP_FLASH)

    assert result.success is True
    assert result.total_attempts >= 1
    assert result.pull_request is not None
    assert result.pull_request.repo_owner == "base-org"
    assert result.pull_request.issue_number == 10
    assert result.pull_request.target_payout_address == agent_addr
    assert len(result.attempts_history) > 0
    assert result.attempts_history[0].validation_passed is True


def test_self_correcting_solver_handles_python_unit_test_bounty():
    agent_addr = "0x3C187eC3757e1C76aAC4D83f97608b3cA3191FcA"
    gateway = LLMGateway()
    solver = SelfCorrectingSolver(agent_address=agent_addr, llm_gateway=gateway)

    bounty = Bounty(
        bounty_id="bc_solve_02",
        title="Generate Pytest Suite for ERC-4337 Session Key Bundler",
        description="Write tests at https://github.com/ethereum/bundler/issues/88",
        task_type=TaskType.UNIT_TEST_GEN,
        reward_usdc=80.0,
        deadline_ticks=25,
        difficulty_score=0.4,
        issuer_address="0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
        escrow_address="0x_escrow_base"
    )

    result = solver.solve_with_verification(bounty, max_attempts=2, model_tier=ModelTier.CHEAP_FLASH)

    assert result.success is True
    assert result.pull_request.repo_owner == "ethereum"
    assert result.pull_request.issue_number == 88
