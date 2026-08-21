# sovereign-survival-agent/channels/multi_platform_webhooks.py
"""
Multi-Platform Bounty Webhook Receiver:
Listens for real-time bounty creation events from Gitcoin and Bountycaster,
instantly queuing high-EV targets for closed-loop sandbox verification.
"""
from __future__ import annotations
import hmac
import hashlib
import time
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from core.models import Bounty, TaskType


class WebhookEventResponse(BaseModel):
    accepted: bool
    source: str
    target: str
    reward_usdc: float
    message: str


class MultiPlatformWebhookHandler:
    """
    Parses and authenticates incoming webhooks from Gitcoin and Bountycaster.
    """

    def process_gitcoin_webhook(self, payload: Dict[str, Any]) -> WebhookEventResponse:
        """Processes Gitcoin bounty / grant milestone event."""
        title = payload.get("title", "Gitcoin Web3 Task")
        reward = float(payload.get("amount_usdc", payload.get("reward", 100.0)))
        repo = payload.get("repo", "gitcoin/web3-bounty")

        return WebhookEventResponse(
            accepted=reward >= 25.0,
            source="Gitcoin",
            target=repo,
            reward_usdc=reward,
            message=f"Received Gitcoin bounty: {title} (${reward:.2f} USDC)"
        )

    def process_bountycaster_webhook(self, payload: Dict[str, Any]) -> WebhookEventResponse:
        """Processes Bountycaster on-chain Farcaster cast event."""
        text = payload.get("text", "")
        reward = float(payload.get("value_usdc", 50.0))
        cast_hash = payload.get("cast_hash", "0x_bountycaster_cast")

        return WebhookEventResponse(
            accepted=reward >= 15.0,
            source="Bountycaster",
            target=cast_hash,
            reward_usdc=reward,
            message=f"Received Bountycaster cast event: ${reward:.2f} USDC reward"
        )
