# agent/tests/test_survival_engine.py
"""
Comprehensive Automated Test Suite for Sovereign 'Earn to Survive' Decentralized Agent.
Verifies metabolic accounting, policy EV gates, Web3 session guardrails, HTTP-402 verification,
and full survival loop mechanics.
"""
import pytest
from datetime import datetime, timezone, timedelta
from eth_account import Account
from core.models import (
    AgentState,
    UrgencyTier,
    ModelTier,
    TaskType,
    ServiceRequest,
    Bounty,
    PaymentPermit
)
from core.metabolism import MetabolismManager
from core.policy_engine import SurvivalPolicyEngine
from core.wallet import SovereignWallet
from channels.service_oracle import ServiceOracle
from channels.bounty_hunter import BountyHunter


@pytest.fixture
def fresh_state():
    return AgentState(
        agent_address="0x1111111111111111111111111111111111111111",
        session_key_address="0x2222222222222222222222222222222222222222",
        treasury_usdc=10.00,
        treasury_eth=0.01,
        fixed_burn_rate_hourly=0.05
    )


@pytest.fixture
def metabolism(fresh_state):
    return MetabolismManager(fresh_state)


@pytest.fixture
def policy(fresh_state):
    return SurvivalPolicyEngine(fresh_state)


@pytest.fixture
def wallet(fresh_state):
    return SovereignWallet(
        fresh_state,
        daily_spend_limit_usdc=10.0,
        max_spend_per_tx_usdc=2.0
    )


class TestMetabolismManager:
    def test_initial_state_and_runway(self, metabolism, fresh_state):
        assert fresh_state.is_alive is True
        assert fresh_state.treasury_usdc == 10.00
        assert fresh_state.urgency_tier == UrgencyTier.THRIVING
        assert fresh_state.runway_hours > 72.0

    def test_compute_consumption_and_ledger(self, metabolism, fresh_state):
        initial_balance = fresh_state.treasury_usdc
        cost = metabolism.consume_compute(
            model=ModelTier.CHEAP_FLASH,
            input_tokens=1000,
            output_tokens=500,
            task_label="Test Audit"
        )
        assert cost > 0
        assert fresh_state.treasury_usdc == initial_balance - cost
        assert fresh_state.total_compute_tokens_used == 1500
        assert len(metabolism.ledger) == 1

    def test_credit_revenue(self, metabolism, fresh_state):
        initial_balance = fresh_state.treasury_usdc
        metabolism.credit_revenue(5.00, "Test Bounty Payout", "0xabc")
        assert fresh_state.treasury_usdc == initial_balance + 5.00
        assert fresh_state.total_revenue_earned == 5.00
        assert fresh_state.tasks_completed == 1

    def test_starvation_and_insolvency_halt(self, metabolism, fresh_state):
        # Force treasury to 0
        metabolism.consume_compute(
            model=ModelTier.REASONING_PRO,
            input_tokens=1_000_000,
            output_tokens=500_000,
            task_label="Excessive Task"
        )
        assert fresh_state.is_alive is False
        assert fresh_state.treasury_usdc == 0.0
        assert fresh_state.urgency_tier == UrgencyTier.INSOLVENT
        assert "Starved" in fresh_state.death_cause


class TestSurvivalPolicyEngine:
    def test_model_tier_selection_by_urgency(self, fresh_state, policy):
        # Thriving: Should pick REASONING_PRO for complex high-payout task
        fresh_state.urgency_tier = UrgencyTier.THRIVING
        tier = policy.select_model_tier(complexity=0.8, expected_payout_usdc=10.0)
        assert tier == ModelTier.REASONING_PRO

        # Critical / Starvation: Must force CHEAP_FLASH or FREE_LOCAL
        fresh_state.urgency_tier = UrgencyTier.CRITICAL
        tier = policy.select_model_tier(complexity=0.8, expected_payout_usdc=10.0)
        assert tier == ModelTier.CHEAP_FLASH

    def test_rejects_negative_ev_trap_bounty(self, fresh_state, policy):
        # High complexity (0.95), low payout ($0.02)
        fresh_state.urgency_tier = UrgencyTier.STABLE
        should_accept, ev, model, rationale = policy.evaluate_task_ev(
            payout_usdc=0.02,
            estimated_tokens=5000,
            complexity=0.95,
            penalty_usdc=0.50
        )
        assert should_accept is False
        assert ev < 0.10
        assert "REJECTED" in rationale

    def test_accepts_positive_ev_bounty(self, fresh_state, policy):
        fresh_state.urgency_tier = UrgencyTier.STABLE
        should_accept, ev, model, rationale = policy.evaluate_task_ev(
            payout_usdc=3.50,
            estimated_tokens=1000,
            complexity=0.40,
            penalty_usdc=0.20
        )
        assert should_accept is True
        assert ev > 1.0
        assert "ACCEPTED" in rationale

    def test_dynamic_service_pricing_discount(self, fresh_state, policy):
        fresh_state.urgency_tier = UrgencyTier.CRITICAL
        discounted = policy.get_dynamic_service_fee(1.00)
        assert discounted == 0.60  # 40% emergency discount to attract volume

        fresh_state.urgency_tier = UrgencyTier.THRIVING
        premium = policy.get_dynamic_service_fee(1.00)
        assert premium == 1.25  # 25% premium for top reputation


class TestSovereignWalletAndGuardrails:
    def test_anti_drain_whitelist_blocks_unauthorized_target(self, wallet):
        hacker_address = "0xDeadDeceitfulHackerAddress1234567890abcdef"
        success, msg, tx = wallet.execute_spend(hacker_address, 1.0, "Attacker transfer")
        assert success is False
        assert "SECURITY_ALERT" in msg
        assert "non-whitelisted" in msg

    def test_per_transaction_spend_cap_block(self, wallet):
        # Cap is $2.00, attempting $3.50
        target = wallet.address
        success, msg, tx = wallet.execute_spend(target, 3.50, "Large swap")
        assert success is False
        assert "POLICY_BLOCK" in msg
        assert "exceeds per-tx cap" in msg

    def test_valid_whitelisted_spend(self, wallet):
        target = wallet.address
        success, msg, tx = wallet.execute_spend(target, 1.50, "Valid fee")
        assert success is True
        assert tx is not None
        assert wallet.current_day_spent_usdc == 1.50

    def test_cryptographic_payment_permit_verification(self, wallet):
        client = Account.create()
        permit = wallet.create_mock_payment_permit(
            payer_key=client.key.hex(),
            amount_usdc=1.00,
            nonce=1,
            valid_seconds=3600
        )
        valid, reason = wallet.verify_payment_permit(permit)
        assert valid is True
        assert "valid" in reason

    def test_rejects_counterfeit_signature(self, wallet):
        client1 = Account.create()
        client2 = Account.create()
        # Sign with client1 but claim it's from client2
        permit = wallet.create_mock_payment_permit(
            payer_key=client1.key.hex(),
            amount_usdc=1.00
        )
        permit.payer_address = client2.address  # Tamper with payer address
        valid, reason = wallet.verify_payment_permit(permit)
        assert valid is False
        assert "Signature mismatch" in reason


class TestServiceOracleAndBounties:
    def test_service_oracle_audits_vulnerable_solidity_code(self, metabolism, policy, wallet):
        oracle = ServiceOracle(metabolism, policy, wallet, base_audit_fee_usdc=0.50)
        client = Account.create()
        # Ensure permit covers dynamic fee (which can include thriving premium)
        dynamic_fee = policy.get_dynamic_service_fee(0.50)
        permit = wallet.create_mock_payment_permit(payer_key=client.key.hex(), amount_usdc=dynamic_fee)

        vulnerable_code = """
        contract Insecure {
            function withdraw() public {
                (bool s, ) = msg.sender.call{value: 1 ether}("");
                require(s);
                balances[msg.sender] = 0;
            }
        }
        """
        req = ServiceRequest(
            request_id="req_001",
            task_type=TaskType.SMART_CONTRACT_AUDIT,
            client_address=client.address,
            payload={"code": vulnerable_code},
            payment_permit=permit,
            max_budget_usdc=dynamic_fee
        )
        resp = oracle.process_service_request(req)
        assert resp.success is True
        assert resp.result["status"] == "VULNERABLE"
        assert resp.result["findings_count"] > 0
        assert resp.fee_charged_usdc == dynamic_fee

    def test_bounty_hunter_executes_profitable_bounty(self, metabolism, policy, wallet):
        hunter = BountyHunter(metabolism, policy, wallet)
        bounty = Bounty(
            bounty_id="b_100",
            title="Write Tests for Vault",
            description="Unit test generation",
            task_type=TaskType.UNIT_TEST_GEN,
            reward_usdc=2.00,
            deadline_ticks=10,
            difficulty_score=0.35,
            issuer_address="0xclient",
            escrow_address="0xescrow"
        )
        success, sub, note = hunter.evaluate_and_execute_bounty(bounty, force_success=True)
        assert success is True
        assert sub is not None
        assert "Claimed" in note
        assert metabolism.state.total_revenue_earned >= 2.00
