# agent/core/metabolism.py
"""
Metabolic Engine: Governs the agent's life-support systems, burn rate,
token accounting, runway estimation, and starvation detection.
"""
from __future__ import annotations
import uuid
from typing import List, Tuple
from datetime import datetime, timezone
from core.models import (
    AgentState,
    UrgencyTier,
    ModelTier,
    LedgerEntry,
    TransactionType
)


# Token pricing per 1,000 tokens (USD)
MODEL_PRICING: dict[ModelTier, dict[str, float]] = {
    ModelTier.FREE_LOCAL: {"input": 0.00000, "output": 0.00000},
    ModelTier.CHEAP_FLASH: {"input": 0.00010, "output": 0.00040},
    ModelTier.BALANCED: {"input": 0.00100, "output": 0.00250},
    ModelTier.REASONING_PRO: {"input": 0.00500, "output": 0.01500},
}


class MetabolismManager:
    """
    Simulates the biological/financial metabolism of the autonomous agent.
    Every unit of time or computation consumes resources.
    """

    def __init__(self, state: AgentState):
        self.state = state
        self.ledger: List[LedgerEntry] = []
        self._last_tick_time: datetime = datetime.now(timezone.utc)
        self._recent_burn_history: List[Tuple[datetime, float]] = []
        self.update_urgency_tier()

    def record_transaction(
        self,
        tx_type: TransactionType,
        amount_usdc: float,
        description: str,
        tx_hash: str | None = None
    ) -> LedgerEntry:
        """Appends an auditable record to the agent's internal ledger."""
        entry = LedgerEntry(
            entry_id=f"tx_{uuid.uuid4().hex[:10]}",
            tx_type=tx_type,
            amount_usdc=round(amount_usdc, 6),
            description=description,
            balance_after=round(self.state.treasury_usdc, 6),
            tx_hash=tx_hash,
            timestamp=datetime.now(timezone.utc)
        )
        self.ledger.append(entry)
        return entry

    def tick_metabolic_cost(self, now: datetime | None = None) -> float:
        """
        Deducts time-based fixed burn (hosting rent, memory indexing).
        Called on every heartbeat cycle.
        """
        if not self.state.is_alive:
            return 0.0

        current_time = now or datetime.now(timezone.utc)
        elapsed_seconds = (current_time - self._last_tick_time).total_seconds()
        if elapsed_seconds <= 0:
            return 0.0

        self._last_tick_time = current_time
        hourly_burn = self.state.fixed_burn_rate_hourly
        cost = (elapsed_seconds / 3600.0) * hourly_burn

        if cost > 0:
            self.state.treasury_usdc -= cost
            self.state.total_burn_cost += cost
            self._recent_burn_history.append((current_time, cost))
            self.record_transaction(
                tx_type=TransactionType.FIXED_RENT_BURN,
                amount_usdc=-cost,
                description=f"Fixed hosting/memory rent for {elapsed_seconds:.1f}s"
            )

        self._check_vital_signs("Depleted treasury via hosting/rent burn")
        self.update_urgency_tier()
        return cost

    def consume_compute(
        self,
        model: ModelTier,
        input_tokens: int,
        output_tokens: int,
        task_label: str
    ) -> float:
        """
        Deducts inference compute costs based on tokens consumed.
        """
        if not self.state.is_alive:
            return 0.0

        pricing = MODEL_PRICING.get(model, MODEL_PRICING[ModelTier.CHEAP_FLASH])
        cost = (input_tokens / 1000.0 * pricing["input"]) + (output_tokens / 1000.0 * pricing["output"])
        cost = round(cost, 6)

        self.state.treasury_usdc -= cost
        self.state.total_burn_cost += cost
        self.state.total_compute_tokens_used += (input_tokens + output_tokens)
        self._recent_burn_history.append((datetime.now(timezone.utc), cost))

        self.record_transaction(
            tx_type=TransactionType.COMPUTE_BURN,
            amount_usdc=-cost,
            description=f"Inference [{model.value}] ({input_tokens} in / {output_tokens} out) for '{task_label}'"
        )

        self._check_vital_signs(f"Starved during inference execution for '{task_label}'")
        self.update_urgency_tier()
        return cost

    def consume_gas(self, gas_used_eth: float, eth_price_usdc: float = 3000.0, tx_label: str = "onchain_tx") -> float:
        """
        Deducts on-chain L2 gas fees.
        """
        if not self.state.is_alive:
            return 0.0

        cost_usdc = gas_used_eth * eth_price_usdc
        self.state.treasury_eth = max(0.0, self.state.treasury_eth - gas_used_eth)
        self.state.treasury_usdc -= cost_usdc
        self.state.total_burn_cost += cost_usdc
        self._recent_burn_history.append((datetime.now(timezone.utc), cost_usdc))

        self.record_transaction(
            tx_type=TransactionType.GAS_BURN,
            amount_usdc=-cost_usdc,
            description=f"Base L2 Gas fee ({gas_used_eth:.7f} ETH) for '{tx_label}'"
        )

        self._check_vital_signs("Exhausted funds paying transaction gas")
        self.update_urgency_tier()
        return cost_usdc

    def credit_revenue(
        self,
        amount_usdc: float,
        source_description: str,
        tx_hash: str | None = None
    ) -> None:
        """
        Credits earnings into the agent's on-chain treasury.
        """
        if not self.state.is_alive:
            return

        self.state.treasury_usdc += amount_usdc
        self.state.total_revenue_earned += amount_usdc
        self.state.tasks_completed += 1
        # Boost reputation slightly upon verified delivery
        self.state.reputation_score = min(100.0, self.state.reputation_score + 0.5)

        self.record_transaction(
            tx_type=TransactionType.REVENUE,
            amount_usdc=amount_usdc,
            description=source_description,
            tx_hash=tx_hash
        )

        self.update_urgency_tier()

    def record_task_failure(self, penalty_usdc: float, reason: str) -> None:
        """Records task delivery failure, slashes reputation and applies penalties."""
        self.state.tasks_failed += 1
        self.state.reputation_score = max(10.0, self.state.reputation_score - 3.0)
        if penalty_usdc > 0:
            self.state.treasury_usdc -= penalty_usdc
            self.record_transaction(
                tx_type=TransactionType.COMPUTE_BURN,
                amount_usdc=-penalty_usdc,
                description=f"Slashed escrow penalty: {reason}"
            )
        self._check_vital_signs(f"Insolvent due to penalty slash: {reason}")
        self.update_urgency_tier()

    def get_hourly_burn_velocity(self) -> float:
        """Calculates rolling hourly burn rate based on recent history."""
        now = datetime.now(timezone.utc)
        # Prune history older than 1 hour
        self._recent_burn_history = [
            (t, c) for (t, c) in self._recent_burn_history
            if (now - t).total_seconds() <= 3600
        ]
        recent_variable_burn = sum(c for _, c in self._recent_burn_history)
        total_velocity = self.state.fixed_burn_rate_hourly + recent_variable_burn
        return max(total_velocity, 0.01)

    def update_urgency_tier(self) -> UrgencyTier:
        """
        Recalculates financial runway and sets the metabolic urgency tier.
        """
        if self.state.treasury_usdc <= 0:
            self.state.is_alive = False
            self.state.urgency_tier = UrgencyTier.INSOLVENT
            self.state.runway_hours = 0.0
            return UrgencyTier.INSOLVENT

        hourly_burn = self.get_hourly_burn_velocity()
        runway = self.state.treasury_usdc / hourly_burn
        self.state.runway_hours = round(runway, 2)

        if runway > 72.0:
            tier = UrgencyTier.THRIVING
        elif runway >= 24.0:
            tier = UrgencyTier.STABLE
        elif runway >= 6.0:
            tier = UrgencyTier.AUSTERE
        else:
            tier = UrgencyTier.CRITICAL

        self.state.urgency_tier = tier
        return tier

    def _check_vital_signs(self, cause: str) -> None:
        """Checks if treasury is exhausted and triggers insolvency freeze."""
        if self.state.treasury_usdc <= 0:
            self.state.treasury_usdc = 0.0
            self.state.is_alive = False
            self.state.urgency_tier = UrgencyTier.INSOLVENT
            self.state.death_cause = cause
            self.record_transaction(
                tx_type=TransactionType.COMPUTE_BURN,
                amount_usdc=0.0,
                description=f"[HALT] DEATH TRIGGERED: {cause}"
            )

