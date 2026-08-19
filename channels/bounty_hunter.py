# agent/channels/bounty_hunter.py
"""
Autonomous Bounty Hunter Channel:
Scans decentralized task registries, calculates Expected Value (EV) against token costs,
solves programming and security tasks, and claims escrowed USDC payouts.
"""
from __future__ import annotations
import random
from typing import Tuple, Dict, Any, List
from core.models import (
    Bounty,
    BountySubmission,
    TaskType,
    ModelTier
)
from core.metabolism import MetabolismManager
from core.policy_engine import SurvivalPolicyEngine
from core.wallet import SovereignWallet


class BountyHunter:
    """
    Autonomous worker agent that competes for on-chain task bounties.
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
        self.resolved_bounties: List[str] = []

    def evaluate_and_execute_bounty(
        self,
        bounty: Bounty,
        force_success: bool = False
    ) -> Tuple[bool, BountySubmission | None, str]:
        """
        1. Evaluates Bounty Expected Value (EV).
        2. If EV is positive and meets threshold, accepts and executes task.
        3. Burns compute tokens based on model tier and complexity.
        4. Submits solution and collects verified escrow payout.
        """
        # Avoid duplicate work
        if bounty.bounty_id in self.resolved_bounties:
            return False, None, f"Bounty {bounty.bounty_id} already resolved"

        # 1. EV Evaluation
        estimated_tokens = int(800 + bounty.difficulty_score * 3000)
        penalty_usdc = bounty.reward_usdc * 0.10  # 10% slashing if failed

        should_accept, expected_val, selected_model, rationale = self.policy.evaluate_task_ev(
            payout_usdc=bounty.reward_usdc,
            estimated_tokens=estimated_tokens,
            complexity=bounty.difficulty_score,
            penalty_usdc=penalty_usdc,
            task_type=bounty.task_type
        )

        if not should_accept:
            return False, None, f"SKIPPED [{bounty.bounty_id}]: {rationale}"

        # 2. Execute Task & Incur Compute Cost
        input_tokens = int(estimated_tokens * 0.65)
        output_tokens = int(estimated_tokens * 0.35)

        compute_cost = self.metabolism.consume_compute(
            model=selected_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            task_label=f"Bounty: {bounty.title}"
        )

        # 3. Simulate Solution Quality & Payout Verification
        p_success = self.policy.estimate_success_probability(selected_model, bounty.difficulty_score)
        is_successful = force_success or (random.random() <= p_success)

        if is_successful:
            solution = self._generate_solution(bounty, selected_model)
            submission = BountySubmission(
                bounty_id=bounty.bounty_id,
                agent_address=self.wallet.address,
                solution_payload=solution,
                reasoning_summary=f"Solved '{bounty.title}' with [{selected_model.value}]. Incurred ${compute_cost:.4f} token cost.",
                compute_cost_incurred=compute_cost,
                model_used=selected_model
            )

            # Credit Escrow Payout
            self.metabolism.credit_revenue(
                amount_usdc=bounty.reward_usdc,
                source_description=f"Claimed Bounty '{bounty.title}' (Gross: ${bounty.reward_usdc:.2f}, Net: +${bounty.reward_usdc - compute_cost:.4f})",
                tx_hash=f"0x_bounty_{bounty.bounty_id[:8]}"
            )
            self.resolved_bounties.append(bounty.bounty_id)
            return True, submission, f"SUCCESS: Claimed ${bounty.reward_usdc:.2f} bounty '{bounty.title}'"
        else:
            # Handle Failure / Slash
            self.metabolism.record_task_failure(
                penalty_usdc=penalty_usdc,
                reason=f"Failed validation on bounty '{bounty.title}'"
            )
            return False, None, f"FAILED: Solution rejected for bounty '{bounty.title}', slashed ${penalty_usdc:.2f}"

    def _generate_solution(self, bounty: Bounty, model: ModelTier) -> Dict[str, Any]:
        """Generates synthetic domain solutions based on task type."""
        if bounty.task_type == TaskType.UNIT_TEST_GEN:
            return {
                "test_suite": "test_contract_security.py",
                "tests_written": 14,
                "coverage_percent": 98.4,
                "status": "ALL_TESTS_PASSING"
            }
        elif bounty.task_type == TaskType.CODE_BUG_FIX:
            return {
                "patch_file": "fix_reentrancy.patch",
                "diff_lines": 28,
                "verification": "PASSED_STATIC_ANALYSIS"
            }
        elif bounty.task_type == TaskType.MARKET_INTELLIGENCE:
            return {
                "sentiment_index": 0.72,
                "data_points_analyzed": 1450,
                "summary": f"Completed deep research for {bounty.title}"
            }
        else:
            return {
                "artifact": "analysis_report.md",
                "status": "DELIVERED"
            }
