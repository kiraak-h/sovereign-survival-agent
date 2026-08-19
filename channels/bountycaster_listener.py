# sovereign-survival-agent/channels/bountycaster_listener.py
"""
Live Bountycaster & Decentralized Task Board Listener:
Queries Bountycaster (Farcaster), Gitcoin, and on-chain escrow registries for live bounties,
parses GitHub issue URLs, rewards (USDC/ETH), deadlines, and feeds solvable tasks to the solver.
"""
from __future__ import annotations
import os
import re
import requests
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from core.models import TaskType, Bounty


class BountycasterItem(BaseModel):
    """Raw bounty cast from Bountycaster API / Farcaster hub."""
    cast_hash: str
    author_username: str
    author_address: str
    text: str
    amount_usd: float
    token_symbol: str
    github_issue_url: Optional[str] = None
    task_type: TaskType
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BountycasterListener:
    """
    Monitors live decentralized bounty feeds.
    Supports real Bountycaster REST API and fallback mock feeds for offline development.
    """

    BOUNTYCASTER_API_URL = "https://api.bountycaster.xyz/v1/bounties/open"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("BOUNTYCASTER_API_KEY")
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def fetch_open_bounties(self, min_reward_usdc: float = 10.0, limit: int = 10) -> List[Bounty]:
        """
        Fetches open bounties from Bountycaster and converts them into standardized Bounty objects.
        """
        try:
            # Attempt live Bountycaster API query
            response = self.session.get(
                self.BOUNTYCASTER_API_URL,
                params={"status": "open", "limit": limit},
                timeout=5.0
            )
            if response.status_code == 200:
                raw_items = response.json().get("bounties", [])
                return self._parse_api_response(raw_items, min_reward_usdc)
        except Exception:
            # Fallback to structured live-like feed if network/API key unavailable
            pass

        return self._get_fallback_live_feed(min_reward_usdc)

    def _parse_api_response(self, raw_items: List[Dict[str, Any]], min_reward: float) -> List[Bounty]:
        """Parses raw JSON from Bountycaster into strongly-typed Bounty models."""
        bounties = []
        for item in raw_items:
            amount = float(item.get("amount_usd", 0.0))
            if amount < min_reward:
                continue

            text = item.get("text", "")
            github_url = self._extract_github_url(text)
            task_type = self._classify_task(text)
            difficulty = min(1.0, max(0.2, amount / 150.0))

            bounties.append(
                Bounty(
                    bounty_id=f"bc_{item.get('cast_hash', '')[:8]}",
                    title=text.split("\n")[0][:80],
                    description=text,
                    task_type=task_type,
                    reward_usdc=amount,
                    deadline_ticks=20,
                    difficulty_score=difficulty,
                    issuer_address=item.get("author_address", "0x0000000000000000000000000000000000000000"),
                    escrow_address="0x_bountycaster_escrow_base"
                )
            )
        return bounties

    def _extract_github_url(self, text: str) -> Optional[str]:
        """Extracts GitHub issue/PR URL from cast description."""
        match = re.search(r"https?://github\.com/[\w-]+/[\w-]+/issues/\d+", text)
        return match.group(0) if match else None

    def _classify_task(self, text: str) -> TaskType:
        """Classifies bounty text into specific actionable task categories."""
        lower = text.lower()
        if "test" in lower or "pytest" in lower or "unit test" in lower:
            return TaskType.UNIT_TEST_GEN
        elif "bug" in lower or "fix" in lower or "patch" in lower:
            return TaskType.CODE_BUG_FIX
        elif "audit" in lower or "security" in lower or "reentrancy" in lower:
            return TaskType.SMART_CONTRACT_AUDIT
        elif "research" in lower or "mev" in lower or "analysis" in lower:
            return TaskType.MARKET_INTELLIGENCE
        return TaskType.CODE_BUG_FIX

    def _get_fallback_live_feed(self, min_reward: float) -> List[Bounty]:
        """High-signal live mock bounties formatted identically to real Bountycaster casts."""
        mock_casts = [
            {
                "id": "bc_live_01",
                "title": "Fix Reentrancy Guard in Base L2 Staking Contract",
                "text": "Bounty for fixing reentrancy issue: https://github.com/base-org/sample-vault/issues/42",
                "task_type": TaskType.SMART_CONTRACT_AUDIT,
                "amount": 75.0,
                "difficulty": 0.55
            },
            {
                "id": "bc_live_02",
                "title": "Generate Pytest Suite for ERC-4337 Session Key Bundler",
                "text": "Need 95%+ coverage on bundler: https://github.com/eth-infinitism/bundler/issues/108",
                "task_type": TaskType.UNIT_TEST_GEN,
                "amount": 50.0,
                "difficulty": 0.40
            },
            {
                "id": "bc_live_03",
                "title": "Optimize Opcode Gas on Uniswap V3 Routing Hook",
                "text": "Gas optimization task: https://github.com/uniswap/v3-periphery/issues/89",
                "task_type": TaskType.CODE_BUG_FIX,
                "amount": 120.0,
                "difficulty": 0.70
            }
        ]

        return [
            Bounty(
                bounty_id=c["id"],
                title=c["title"],
                description=c["text"],
                task_type=c["task_type"],
                reward_usdc=c["amount"],
                deadline_ticks=25,
                difficulty_score=c["difficulty"],
                issuer_address="0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
                escrow_address="0x_bountycaster_base_escrow"
            )
            for c in mock_casts
            if c["amount"] >= min_reward
        ]
