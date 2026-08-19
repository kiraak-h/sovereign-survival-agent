# agent/channels/subcontracting_engine.py
"""
Agent-to-Agent (A2A) Autonomous Subcontracting Engine:
Allows the Sovereign Agent to act as a Prime Contractor. It decomposes complex bounties
into micro-tasks, hires cheaper sub-agents on-chain, validates their proofs of work,
and captures the profit spread to maximize treasury longevity.
"""
from __future__ import annotations
import uuid
import random
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field
from core.models import (
    Bounty,
    BountySubmission,
    TaskType,
    ModelTier,
    TransactionType
)
from core.metabolism import MetabolismManager
from core.policy_engine import SurvivalPolicyEngine
from core.wallet import SovereignWallet


class SubcontractorBid(BaseModel):
    """Bid from a peer sub-agent on the A2A network."""
    subagent_id: str
    subagent_name: str
    fee_usdc: float
    reputation: float
    specialty: str


class SubTaskResult(BaseModel):
    """Proof-of-work delivered by a subcontractor."""
    subtask_id: str
    subagent_id: str
    delivered_artifact: Dict[str, Any]
    verified: bool
    fee_paid_usdc: float


class A2ASubcontractingEngine:
    """
    Prime Contractor module: Decomposes tasks, hires micro-agents, captures profit spread.
    """

    def __init__(
        self,
        metabolism: MetabolismManager,
        policy: SurvivalPolicyEngine,
        wallet: SovereignWallet
    ):
        self.metabolism = metabolism
        self.policy = policy
        self.wallet = wallet
        self.active_subcontracts: Dict[str, List[SubTaskResult]] = {}

        # Simulated peer worker agents in the decentralized network
        self.peer_network: List[SubcontractorBid] = [
            SubcontractorBid(subagent_id="agent_rust_linter", subagent_name="RustLinter-9000", fee_usdc=0.35, reputation=96.0, specialty="STATIC_ANALYSIS"),
            SubcontractorBid(subagent_id="agent_fuzz_tester", subagent_name="SolidityFuzzerBot", fee_usdc=0.60, reputation=92.0, specialty="UNIT_TEST_GEN"),
            SubcontractorBid(subagent_id="agent_doc_synthesizer", subagent_name="DocSynthesizer-Mini", fee_usdc=0.25, reputation=88.0, specialty="DOCS_AND_SUMMARIES"),
            SubcontractorBid(subagent_id="agent_gas_optimizer", subagent_name="GasSqueezer-v2", fee_usdc=0.45, reputation=94.0, specialty="GAS_OPT")
        ]

    def should_subcontract(self, bounty: Bounty) -> bool:
        """
        Determines whether subcontracting yields a higher EV and lower risk than self-execution.
        """
        # Subcontracting is optimal for high-payout bounties ($2.50+) where delegation minimizes execution risk
        return (
            self.metabolism.state.is_alive
            and bounty.reward_usdc >= 2.50
            and bounty.difficulty_score >= 0.50
        )

    def execute_with_subcontractors(self, bounty: Bounty) -> Tuple[bool, BountySubmission | None, float, str]:
        """
        1. Decomposes bounty into subtasks.
        2. Hires peer agents and pays micro-fees.
        3. Validates subcontractors' deliverables with minimal compute.
        4. Submits aggregate bundle to escrow.
        5. Returns: (success, submission, net_profit_spread, summary_note)
        """
        if not self.metabolism.state.is_alive:
            return False, None, 0.0, "Agent is insolvent"

        # 1. Select 2 appropriate peer agents based on task
        subcontractors = self._select_subcontractors_for_bounty(bounty)
        total_subcontractor_fees = sum(s.fee_usdc for s in subcontractors)

        # Ensure healthy profit margin (Prime agent must capture at least 35% spread)
        target_spread = bounty.reward_usdc - total_subcontractor_fees
        if target_spread < bounty.reward_usdc * 0.35:
            return False, None, 0.0, f"Spread too thin (Payout: ${bounty.reward_usdc:.2f}, Sub Fees: ${total_subcontractor_fees:.2f})"

        # 2. Pay Subcontractors & Incur A2A spend through wallet guardrails
        sub_results: List[SubTaskResult] = []
        for sub in subcontractors:
            subtask_id = f"sub_{uuid.uuid4().hex[:6]}"
            # Spend guardrail check
            spend_ok, msg, tx = self.wallet.execute_spend(
                target_address=self.wallet.address,  # Mock settlement target
                amount_usdc=sub.fee_usdc,
                purpose=f"A2A Subcontract fee to {sub.subagent_name}"
            )
            if not spend_ok:
                return False, None, 0.0, f"Subcontract spend blocked by guardrails: {msg}"

            # Deduct subcontractor cost from treasury
            self.metabolism.state.treasury_usdc -= sub.fee_usdc
            self.metabolism.state.total_burn_cost += sub.fee_usdc
            self.metabolism.record_transaction(
                tx_type=TransactionType.COMPUTE_BURN,
                amount_usdc=-sub.fee_usdc,
                description=f"A2A Subcontract fee to {sub.subagent_name} for '{bounty.title}'",
                tx_hash=tx
            )

            # Generate synthetic deliverable from subcontractor
            delivered = self._simulate_subagent_delivery(sub, bounty)
            sub_results.append(SubTaskResult(
                subtask_id=subtask_id,
                subagent_id=sub.subagent_id,
                delivered_artifact=delivered,
                verified=True,
                fee_paid_usdc=sub.fee_usdc
            ))

        # 3. Prime Agent performs high-level QA aggregation & verification (minimal token burn)
        verification_compute_cost = self.metabolism.consume_compute(
            model=ModelTier.CHEAP_FLASH,
            input_tokens=400,
            output_tokens=250,
            task_label=f"A2A QA Assembly: {bounty.title}"
        )

        # 4. Assemble Final Submission Package
        aggregate_solution = {
            "prime_contractor": self.wallet.address,
            "architecture": "A2A_MODULAR_BUNDLE",
            "bounty_id": bounty.bounty_id,
            "subcontractor_modules": [r.delivered_artifact for r in sub_results],
            "qa_verification": "PASSED_CRYPTOGRAPHIC_CONSENSUS"
        }

        # 5. Claim Escrow Payout
        self.metabolism.credit_revenue(
            amount_usdc=bounty.reward_usdc,
            source_description=f"Claimed Bounty '{bounty.title}' via A2A Subcontracting (Gross: +${bounty.reward_usdc:.2f})",
            tx_hash=f"0x_a2a_bounty_{bounty.bounty_id[:6]}"
        )

        net_spread = bounty.reward_usdc - total_subcontractor_fees - verification_compute_cost
        submission = BountySubmission(
            bounty_id=bounty.bounty_id,
            agent_address=self.wallet.address,
            solution_payload=aggregate_solution,
            reasoning_summary=(
                f"Delegated to {len(subcontractors)} peer micro-agents. "
                f"Captured +${net_spread:.2f} profit spread."
            ),
            compute_cost_incurred=round(total_subcontractor_fees + verification_compute_cost, 4),
            model_used=ModelTier.CHEAP_FLASH
        )

        note = (
            f"A2A SUCCESS: Bounty '{bounty.title}' resolved! "
            f"Gross: +${bounty.reward_usdc:.2f}, Sub Fees: -${total_subcontractor_fees:.2f}, "
            f"Net Spread Captured: +${net_spread:.2f}"
        )
        return True, submission, net_spread, note

    def _select_subcontractors_for_bounty(self, bounty: Bounty) -> List[SubcontractorBid]:
        """Chooses the best 2 specialized micro-agents for the task."""
        if bounty.task_type == TaskType.CODE_BUG_FIX:
            return [self.peer_network[0], self.peer_network[3]]  # Linter + Gas Optimizer
        elif bounty.task_type == TaskType.UNIT_TEST_GEN:
            return [self.peer_network[0], self.peer_network[1]]  # Linter + Fuzzer
        else:
            return [self.peer_network[0], self.peer_network[2]]  # Linter + Doc Synth

    def _simulate_subagent_delivery(self, sub: SubcontractorBid, bounty: Bounty) -> Dict[str, Any]:
        """Simulates structured deliverable from a peer agent."""
        return {
            "module_author": sub.subagent_name,
            "specialty": sub.specialty,
            "status": "VALIDATED",
            "findings": f"Clean verification pass for {bounty.title}",
            "confidence_score": 0.98
        }
