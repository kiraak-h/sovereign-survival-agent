# agent/core/policy_engine.py
"""
Survival Policy Engine: Calculates Expected Value (EV), dynamically switches
model tiers based on financial urgency, and optimizes pricing for market survival.
"""
from __future__ import annotations
from typing import Tuple
from core.models import AgentState, UrgencyTier, ModelTier, TaskType
from core.metabolism import MODEL_PRICING


class SurvivalPolicyEngine:
    """
    Economic brain of the sovereign agent. Enforces bounded rationality
    and dynamic frugality to prevent bankruptcy.
    """

    def __init__(self, state: AgentState):
        self.state = state

    def select_model_tier(self, complexity: float, expected_payout_usdc: float) -> ModelTier:
        """
        Selects the optimal inference tier based on urgency and unit economics.
        """
        urgency = self.state.urgency_tier

        # In Critical / Starvation mode, never risk expensive inference
        if urgency == UrgencyTier.CRITICAL:
            return ModelTier.FREE_LOCAL if complexity < 0.4 else ModelTier.CHEAP_FLASH

        # In Austere mode, prioritize cheap flash models
        if urgency == UrgencyTier.AUSTERE:
            if complexity > 0.8 and expected_payout_usdc > 5.00:
                return ModelTier.BALANCED
            return ModelTier.CHEAP_FLASH

        # In Stable mode, use balanced models for complex work
        if urgency == UrgencyTier.STABLE:
            if complexity > 0.75 and expected_payout_usdc > 3.00:
                return ModelTier.REASONING_PRO
            elif complexity > 0.4:
                return ModelTier.BALANCED
            return ModelTier.CHEAP_FLASH

        # In Thriving mode, invest in frontier reasoning for high-yield bounties
        if urgency == UrgencyTier.THRIVING:
            if complexity > 0.5 and expected_payout_usdc > 2.00:
                return ModelTier.REASONING_PRO
            elif complexity > 0.3:
                return ModelTier.BALANCED
            return ModelTier.CHEAP_FLASH

        return ModelTier.CHEAP_FLASH

    def estimate_token_cost(self, model: ModelTier, estimated_tokens: int) -> float:
        """Estimates USD cost of token consumption (assuming 60% input / 40% output)."""
        pricing = MODEL_PRICING.get(model, MODEL_PRICING[ModelTier.CHEAP_FLASH])
        input_tokens = int(estimated_tokens * 0.6)
        output_tokens = int(estimated_tokens * 0.4)
        cost = (input_tokens / 1000.0 * pricing["input"]) + (output_tokens / 1000.0 * pricing["output"])
        return round(cost, 6)

    def estimate_success_probability(self, model: ModelTier, complexity: float) -> float:
        """
        Estimates the probability of delivering acceptable work.
        Frontier models have higher success rates on complex tasks.
        """
        base_capability = {
            ModelTier.FREE_LOCAL: 0.50,
            ModelTier.CHEAP_FLASH: 0.75,
            ModelTier.BALANCED: 0.90,
            ModelTier.REASONING_PRO: 0.98,
        }.get(model, 0.70)

        # Penalize for complexity
        effective_p = base_capability * (1.0 - (complexity * 0.35))

        # Factor in agent's historical reputation
        reputation_factor = self.state.reputation_score / 100.0
        final_p = effective_p * (0.8 + 0.2 * reputation_factor)
        return min(0.99, max(0.10, final_p))

    def evaluate_task_ev(
        self,
        payout_usdc: float,
        estimated_tokens: int,
        complexity: float,
        penalty_usdc: float = 0.0,
        task_type: TaskType = TaskType.SMART_CONTRACT_AUDIT
    ) -> Tuple[bool, float, ModelTier, str]:
        """
        Calculates Expected Value (EV) of a task before committing compute.
        Formula: EV = P(success) * Payout - TokenCost - (1 - P(success)) * Penalty
        Returns: (should_accept, expected_value, selected_model, rationale)
        """
        if not self.state.is_alive:
            return False, 0.0, ModelTier.FREE_LOCAL, "Agent is insolvent / deceased"

        model = self.select_model_tier(complexity, payout_usdc)
        token_cost = self.estimate_token_cost(model, estimated_tokens)
        p_success = self.estimate_success_probability(model, complexity)

        # Expected Value calculation
        expected_value = (p_success * payout_usdc) - token_cost - ((1.0 - p_success) * penalty_usdc)
        expected_value = round(expected_value, 4)

        # Urgency-specific thresholding
        urgency = self.state.urgency_tier

        if urgency == UrgencyTier.CRITICAL:
            # Desperate for any positive inflow
            min_ev = 0.005
            min_roi = 1.10  # 10% profit over token cost
        elif urgency == UrgencyTier.AUSTERE:
            min_ev = 0.05
            min_roi = 1.30  # 30% profit margin
        elif urgency == UrgencyTier.STABLE:
            min_ev = 0.20
            min_roi = 1.60  # 60% profit margin
        else:  # THRIVING
            min_ev = 0.50
            min_roi = 2.00  # 100% profit margin required

        # ROI check (Payout vs Cost)
        roi = payout_usdc / max(token_cost, 0.0001)

        if expected_value >= min_ev and roi >= min_roi:
            rationale = (
                f"ACCEPTED: EV=+${expected_value:.3f}, ROI={roi:.1f}x, "
                f"P(Success)={p_success:.2f} using [{model.value}]"
            )
            return True, expected_value, model, rationale
        else:
            rationale = (
                f"REJECTED: EV=${expected_value:.3f} (min required ${min_ev:.2f}), "
                f"ROI={roi:.1f}x (min required {min_roi:.1f}x)"
            )
            return False, expected_value, model, rationale

    def get_dynamic_service_fee(self, base_fee_usdc: float) -> float:
        """
        Adjusts public service fees dynamically to optimize demand and runway.
        """
        urgency = self.state.urgency_tier
        if urgency == UrgencyTier.CRITICAL:
            # 40% discount to stimulate immediate incoming transactions
            return max(0.05, round(base_fee_usdc * 0.60, 2))
        elif urgency == UrgencyTier.AUSTERE:
            # 15% discount for faster turnover
            return max(0.10, round(base_fee_usdc * 0.85, 2))
        elif urgency == UrgencyTier.THRIVING:
            # 25% premium for top-tier reputation & SLA
            return round(base_fee_usdc * 1.25, 2)
        return base_fee_usdc
