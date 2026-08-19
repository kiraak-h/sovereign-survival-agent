# agent/core/models.py
"""
Data models and schemas for the Sovereign 'Earn to Survive' Autonomous Agent.
"""
from __future__ import annotations
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field


def _now_utc():
    return datetime.now(timezone.utc)


class UrgencyTier(str, Enum):
    """Metabolic urgency tiers based on financial runway."""
    THRIVING = "THRIVING"          # Runway > 72h: High reasoning, large investments, complex bounties
    STABLE = "STABLE"              # Runway 24h-72h: Balanced operations, standard model tier
    AUSTERE = "AUSTERE"            # Runway 6h-24h: Frugal compute, cheap flash models, fast jobs
    CRITICAL = "CRITICAL"          # Runway < 6h: Emergency mode, discount services, accept any positive EV
    INSOLVENT = "INSOLVENT"        # Balance <= 0: Process freeze / bankruptcy halt


class ModelTier(str, Enum):
    """Inference compute tiers with respective cost profiles ($/1k tokens)."""
    FREE_LOCAL = "FREE_LOCAL"              # Cost: $0.00000 / 1k tokens (Rule-based / Local heuristics)
    CHEAP_FLASH = "CHEAP_FLASH"            # Cost: $0.00015 / 1k tokens (Gemini 2.5 Flash / GPT-4o-mini)
    BALANCED = "BALANCED"                  # Cost: $0.00100 / 1k tokens (Gemini Pro / Claude 3.5 Haiku)
    REASONING_PRO = "REASONING_PRO"        # Cost: $0.00800 / 1k tokens (Claude 3.5 Sonnet / DeepSeek R1)


class TaskType(str, Enum):
    """Types of decentralized earning tasks."""
    SMART_CONTRACT_AUDIT = "SMART_CONTRACT_AUDIT"
    CODE_BUG_FIX = "CODE_BUG_FIX"
    MARKET_INTELLIGENCE = "MARKET_INTELLIGENCE"
    UNIT_TEST_GEN = "UNIT_TEST_GEN"
    SYNTHETIC_DATA_EXTRACT = "SYNTHETIC_DATA_EXTRACT"


class PaymentPermit(BaseModel):
    """EIP-2612 / HTTP-402 micropayment authorization permit."""
    payer_address: str
    token_address: str
    amount_usdc: float
    nonce: int
    deadline: int
    signature: str
    timestamp: datetime = Field(default_factory=_now_utc)


class ServiceRequest(BaseModel):
    """Incoming HTTP-402 paid service request."""
    request_id: str
    task_type: TaskType
    client_address: str
    payload: Dict[str, Any]
    payment_permit: Optional[PaymentPermit] = None
    max_budget_usdc: float
    timestamp: datetime = Field(default_factory=_now_utc)


class ServiceResponse(BaseModel):
    """Response returned to client upon verified service execution."""
    request_id: str
    success: bool
    result: Dict[str, Any]
    fee_charged_usdc: float
    execution_time_ms: float
    model_used: ModelTier
    tx_hash: Optional[str] = None


class Bounty(BaseModel):
    """On-chain task bounty from Gitcoin, Bountycaster, or escrow registry."""
    bounty_id: str
    title: str
    description: str
    task_type: TaskType
    reward_usdc: float
    deadline_ticks: int
    difficulty_score: float = Field(ge=0.1, le=1.0, description="Complexity multiplier")
    issuer_address: str
    escrow_address: str
    created_at: datetime = Field(default_factory=_now_utc)


class BountySubmission(BaseModel):
    """Agent's proof-of-work submission to claim an escrowed bounty."""
    bounty_id: str
    agent_address: str
    solution_payload: Dict[str, Any]
    reasoning_summary: str
    compute_cost_incurred: float
    model_used: ModelTier
    submitted_at: datetime = Field(default_factory=_now_utc)


class TransactionType(str, Enum):
    REVENUE = "REVENUE"
    GAS_BURN = "GAS_BURN"
    COMPUTE_BURN = "COMPUTE_BURN"
    FIXED_RENT_BURN = "FIXED_RENT_BURN"
    INVESTMENT = "INVESTMENT"


class LedgerEntry(BaseModel):
    """Auditable on-chain & compute financial transaction."""
    entry_id: str
    tx_type: TransactionType
    amount_usdc: float
    description: str
    balance_after: float
    tx_hash: Optional[str] = None
    timestamp: datetime = Field(default_factory=_now_utc)


class AgentState(BaseModel):
    """Real-time operational and metabolic state of the sovereign agent."""
    agent_address: str
    session_key_address: str
    network: str = "Base Sepolia"
    treasury_usdc: float = 15.00          # Initial seed balance
    treasury_eth: float = 0.005           # Native gas reserve
    fixed_burn_rate_hourly: float = 0.05  # $0.05/hr hosting/rent metabolic cost
    total_compute_tokens_used: int = 0
    total_revenue_earned: float = 0.0
    total_burn_cost: float = 0.0
    tasks_completed: int = 0
    tasks_failed: int = 0
    reputation_score: float = 100.0       # 0.0 to 100.0
    urgency_tier: UrgencyTier = UrgencyTier.STABLE
    runway_hours: float = 300.0
    active_jobs: List[str] = []
    is_alive: bool = True
    death_cause: Optional[str] = None
    created_at: datetime = Field(default_factory=_now_utc)
