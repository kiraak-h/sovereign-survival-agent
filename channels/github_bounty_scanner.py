# sovereign-survival-agent/channels/github_bounty_scanner.py
"""
Live GitHub, Algora & Bountycaster Bounty Scanner:
Scans GitHub Search API and open bounty feeds in real time for genuine paid coding issues,
extracts real reward amounts, parses requirements, and ranks tasks by Expected Value (EV).
"""
from __future__ import annotations
import os
import re
import requests
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from core.models import Bounty, TaskType


class ScannedBounty(BaseModel):
    """Detailed live bounty listing discovered on GitHub or Web3 feeds."""
    source: str  # "GitHub Search", "Algora", "Bountycaster"
    repo_full_name: str
    issue_number: int
    title: str
    url: str
    reward_usdc: float
    labels: List[str] = Field(default_factory=list)
    task_type: TaskType
    difficulty_score: float
    ev_score: float
    is_solvable: bool
    created_at: str


class GitHubBountyScanner:
    """
    Scans real live developer bounty boards:
    1. GitHub Public Search API (multi-query: label:bounty, label:reward, bounty in:title)
    2. Algora Public API
    3. Bountycaster Open Tasks Feed
    """

    GITHUB_SEARCH_URL = "https://api.github.com/search/issues"
    ALGORA_API_URL = "https://api.algora.io/v1/bounties"
    BOUNTYCASTER_API_URL = "https://api.bountycaster.xyz/v1/bounties/open"

    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github+json",
            "User-Agent": "Sovereign-AI-Survival-Agent/1.0"
        })
        if self.github_token:
            self.session.headers.update({"Authorization": f"Bearer {self.github_token}"})

    def scan_all_bounties(self, min_reward_usdc: float = 10.0, limit: int = 15) -> List[ScannedBounty]:
        """Queries live sources, deduplicates, and ranks by Expected Value."""
        results: List[ScannedBounty] = []
        seen_urls = set()

        # 1. Query GitHub Search API (real live issues)
        gh_items = self._search_github_bounties(limit=limit)
        for item in gh_items:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                results.append(item)

        # 2. Query Algora Bounty API
        algora_items = self._query_algora_bounties(limit=limit)
        for item in algora_items:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                results.append(item)

        # 3. Query Bountycaster Open Tasks Feed
        bc_items = self._query_bountycaster_feed(limit=limit)
        for item in bc_items:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                results.append(item)

        # Filter by minimum reward and sort by EV score descending
        filtered = [b for b in results if b.reward_usdc >= min_reward_usdc]
        filtered.sort(key=lambda b: b.ev_score, reverse=True)
        return filtered[:limit]

    def _search_github_bounties(self, limit: int = 10) -> List[ScannedBounty]:
        """Searches real GitHub issues tagged with bounty labels across multiple queries."""
        bounties = []
        queries = [
            "label:bounty is:open is:issue",
            "label:reward is:open is:issue",
            "bounty in:title is:open is:issue"
        ]
        
        for query in queries:
            if len(bounties) >= limit:
                break
            try:
                params = {
                    "q": query,
                    "sort": "created",
                    "order": "desc",
                    "per_page": limit
                }
                res = self.session.get(self.GITHUB_SEARCH_URL, params=params, timeout=6.0)
                if res.status_code == 200:
                    items = res.json().get("items", [])
                    for item in items:
                        scanned = self._parse_github_issue(item)
                        if scanned:
                            bounties.append(scanned)
            except Exception:
                continue
        return bounties

    def _query_algora_bounties(self, limit: int = 10) -> List[ScannedBounty]:
        """Queries Algora real bounty marketplace API."""
        bounties = []
        try:
            res = requests.get(self.ALGORA_API_URL, params={"status": "active", "limit": limit}, timeout=5.0)
            if res.status_code == 200:
                data = res.json()
                items = data if isinstance(data, list) else data.get("bounties", [])
                for item in items:
                    amount = float(item.get("amount", item.get("reward", 50.0)))
                    title = item.get("title", item.get("issue_title", "Open Issue Bounty"))
                    url = item.get("issue_url", item.get("url", ""))
                    if not url or "github.com" not in url:
                        continue
                    repo_match = re.search(r"github\.com/([\w-]+/[\w-]+)", url)
                    repo_name = repo_match.group(1) if repo_match else ""
                    if not repo_name:
                        continue
                    
                    task_type = self._classify_task(title + " " + item.get("description", ""))
                    diff = min(0.9, max(0.2, amount / 200.0))
                    ev = round(0.85 * amount - (diff * 2.5), 2)

                    bounties.append(
                        ScannedBounty(
                            source="Algora",
                            repo_full_name=repo_name,
                            issue_number=int(url.split("/")[-1]) if url.split("/")[-1].isdigit() else 1,
                            title=title[:90],
                            url=url,
                            reward_usdc=amount,
                            labels=["algora", "bounty"],
                            task_type=task_type,
                            difficulty_score=diff,
                            ev_score=ev,
                            is_solvable=True,
                            created_at=datetime.now(timezone.utc).isoformat()
                        )
                    )
        except Exception:
            pass
        return bounties

    def _query_bountycaster_feed(self, limit: int = 10) -> List[ScannedBounty]:
        """Queries real Bountycaster public tasks feed."""
        bounties = []
        try:
            res = requests.get(self.BOUNTYCASTER_API_URL, params={"status": "open", "limit": limit}, timeout=5.0)
            if res.status_code == 200:
                raw_items = res.json().get("bounties", [])
                for item in raw_items:
                    text = item.get("text", "")
                    amount = float(item.get("amount_usd", 50.0))
                    url_match = re.search(r"https?://github\.com/([\w-]+/[\w-]+)/issues/(\d+)", text)
                    if not url_match:
                        continue
                    repo_name = url_match.group(1)
                    issue_num = int(url_match.group(2))
                    url = url_match.group(0)
                    task_type = self._classify_task(text)
                    diff = min(0.9, max(0.2, amount / 200.0))
                    ev = round(0.85 * amount - 2.0, 2)

                    bounties.append(
                        ScannedBounty(
                            source="Bountycaster",
                            repo_full_name=repo_name,
                            issue_number=issue_num,
                            title=text.split("\n")[0][:90],
                            url=url,
                            reward_usdc=amount,
                            labels=["bountycaster", "farcaster"],
                            task_type=task_type,
                            difficulty_score=diff,
                            ev_score=ev,
                            is_solvable=True,
                            created_at=item.get("created_at", datetime.now(timezone.utc).isoformat())
                        )
                    )
        except Exception:
            pass
        return bounties

    def _parse_github_issue(self, item: Dict[str, Any]) -> Optional[ScannedBounty]:
        """Extracts reward amount, labels, and classifies task from a genuine GitHub issue JSON."""
        title = item.get("title", "")
        body = item.get("body", "") or ""
        labels = [l.get("name", "") for l in item.get("labels", []) if isinstance(l, dict)]
        url = item.get("html_url", "")

        # Extract dollar / USDC / ETH amount
        reward = self._extract_reward_amount(title + " " + body + " " + " ".join(labels))
        if reward < 5.0:
            reward = 50.0  # Standard default bounty floor if tagged with bounty label

        repo_match = re.search(r"github\.com/([\w-]+/[\w-]+)/issues/(\d+)", url)
        if not repo_match:
            return None
        repo_name = repo_match.group(1)
        issue_num = int(repo_match.group(2))

        task_type = self._classify_task(title + " " + body)
        difficulty = min(0.95, max(0.2, reward / 180.0))
        p_success = 0.85 if task_type in (TaskType.SMART_CONTRACT_AUDIT, TaskType.UNIT_TEST_GEN) else 0.70
        ev = round(p_success * reward - (difficulty * 2.0), 2)

        return ScannedBounty(
            source="GitHub Search",
            repo_full_name=repo_name,
            issue_number=issue_num,
            title=title[:90],
            url=url,
            reward_usdc=reward,
            labels=labels[:4],
            task_type=task_type,
            difficulty_score=difficulty,
            ev_score=ev,
            is_solvable=True,
            created_at=item.get("created_at", datetime.now(timezone.utc).isoformat())
        )

    def _extract_reward_amount(self, text: str) -> float:
        """Extracts dollar amounts from text using regular expressions."""
        match_usd = re.search(r"\$\s*([0-9]+(?:\.[0-9]{2})?)", text)
        if match_usd:
            return float(match_usd.group(1))

        match_usdc = re.search(r"([0-9]+(?:\.[0-9]{2})?)\s*(?:USDC|USD|DAI)", text, re.IGNORECASE)
        if match_usdc:
            return float(match_usdc.group(1))

        match_eth = re.search(r"([0-9]+(?:\.[0-9]{3,})?)\s*ETH", text, re.IGNORECASE)
        if match_eth:
            return round(float(match_eth.group(1)) * 2500.0, 2)

        return 0.0

    def _classify_task(self, text: str) -> TaskType:
        """Classifies text into supported agent task types."""
        lower = text.lower()
        if any(k in lower for k in ["audit", "security", "reentrancy", "vulnerability", "solidity"]):
            return TaskType.SMART_CONTRACT_AUDIT
        elif any(k in lower for k in ["test", "pytest", "unit test", "coverage", "fuzz"]):
            return TaskType.UNIT_TEST_GEN
        elif any(k in lower for k in ["research", "analysis", "mev", "report"]):
            return TaskType.MARKET_INTELLIGENCE
        return TaskType.CODE_BUG_FIX
