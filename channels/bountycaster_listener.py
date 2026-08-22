# sovereign-survival-agent/channels/bountycaster_listener.py
"""
Live Bountycaster & Decentralized Task Board Listener:
Queries Bountycaster (Farcaster) and open bounty endpoints for live on-chain tasks,
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
    Connects directly to Bountycaster API.
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
            response = self.session.get(
                self.BOUNTYCASTER_API_URL,
                params={"status": "open", "limit": limit},
                timeout=5.0
            )
            if response.status_code == 200:
                raw_items = response.json().get("bounties", [])
                return self._parse_api_response(raw_items, min_reward_usdc)
        except Exception:
            pass

        return []

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
                    escrow_address="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
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
        if any(k in lower for k in ["audit", "security", "reentrancy", "vulnerability", "solidity"]):
            return TaskType.SMART_CONTRACT_AUDIT
        elif any(k in lower for k in ["test", "pytest", "unit test", "coverage", "fuzz"]):
            return TaskType.UNIT_TEST_GEN
        elif any(k in lower for k in ["research", "analysis", "mev", "report"]):
            return TaskType.MARKET_INTELLIGENCE
        return TaskType.CODE_BUG_FIX

