# agent/tests/test_subcontracting.py
"""
Test Suite for Agent-to-Agent (A2A) Autonomous Subcontracting.
"""
import pytest
from core.models import AgentState, Bounty, TaskType, UrgencyTier
from core.metabolism import MetabolismManager
from core.policy_engine import SurvivalPolicyEngine
from core.wallet import SovereignWallet
from channels.subcontracting_engine import A2ASubcontractingEngine


@pytest.fixture
def a2a_setup():
    state = AgentState(
        agent_address="0x1111111111111111111111111111111111111111",
        session_key_address="0x2222222222222222222222222222222222222222",
        treasury_usdc=15.00,
        treasury_eth=0.01,
        fixed_burn_rate_hourly=0.05
    )
    metabolism = MetabolismManager(state)
    policy = SurvivalPolicyEngine(state)
    wallet = SovereignWallet(state)
    engine = A2ASubcontractingEngine(metabolism, policy, wallet)
    return metabolism, wallet, engine


def test_should_subcontract_high_yield_bounties(a2a_setup):
    metabolism, wallet, engine = a2a_setup

    high_yield_bounty = Bounty(
        bounty_id="b_high",
        title="Audit & Optimize Complex Vault",
        description="Complex audit",
        task_type=TaskType.CODE_BUG_FIX,
        reward_usdc=4.50,
        deadline_ticks=10,
        difficulty_score=0.75,
        issuer_address="0xclient",
        escrow_address="0xescrow"
    )
    assert engine.should_subcontract(high_yield_bounty) is True

    low_yield_bounty = Bounty(
        bounty_id="b_low",
        title="Quick Typo Fix",
        description="Low reward",
        task_type=TaskType.CODE_BUG_FIX,
        reward_usdc=0.50,
        deadline_ticks=5,
        difficulty_score=0.20,
        issuer_address="0xclient",
        escrow_address="0xescrow"
    )
    assert engine.should_subcontract(low_yield_bounty) is False


def test_execute_with_subcontractors_captures_profit_spread(a2a_setup):
    metabolism, wallet, engine = a2a_setup
    initial_treasury = metabolism.state.treasury_usdc

    bounty = Bounty(
        bounty_id="b_contract_test",
        title="Generate Tests & Audit Staking Pool",
        description="Comprehensive audit",
        task_type=TaskType.UNIT_TEST_GEN,
        reward_usdc=4.00,
        deadline_ticks=15,
        difficulty_score=0.65,
        issuer_address="0xclient",
        escrow_address="0xescrow"
    )

    success, submission, net_spread, note = engine.execute_with_subcontractors(bounty)
    assert success is True
    assert submission is not None
    assert net_spread > 2.00  # Captures > 50% profit spread
    assert metabolism.state.treasury_usdc > initial_treasury
    assert len(submission.solution_payload["subcontractor_modules"]) == 2
