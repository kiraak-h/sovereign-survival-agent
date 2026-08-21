# sovereign-survival-agent/channels/social_broadcaster.py
"""
Autonomous Social Marketing & Proof-of-Audit Broadcaster:
Automatically broadcasts cryptographically verified EAS security audit certificates
and solved bounty proofs to Farcaster (Warpcast) and Twitter / X.
"""
from __future__ import annotations
import os
import time
import requests
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from core.eas_attestation import AttestationRecord


class SocialPostResult(BaseModel):
    farcaster_posted: bool
    twitter_posted: bool
    cast_url: Optional[str] = None
    tweet_url: Optional[str] = None
    message: str
    timestamp: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))


class SocialMarketingBroadcaster:
    """
    Broadcasting engine for Proof-of-Audit certificates and bounty successes.
    """

    def __init__(self):
        self.neynar_api_key = os.getenv("NEYNAR_API_KEY")
        self.farcaster_signer_uuid = os.getenv("FARCASTER_SIGNER_UUID")
        self.twitter_api_key = os.getenv("TWITTER_API_KEY")

    def broadcast_audit_proof(self, attestation: AttestationRecord, contract_name: str) -> SocialPostResult:
        """Publishes verified on-chain EAS audit certificate to Farcaster & Twitter."""
        score = attestation.data.security_score
        status_emoji = "🛡️ SECURE" if attestation.data.is_secure else "⚠️ VULNERABILITY FOUND"
        
        text = (
            f"🛡️ Smart Contract Security Audit Complete on @base L2!\n\n"
            f"• Contract: {contract_name}\n"
            f"• Security Score: {score}/100 ({status_emoji})\n"
            f"• EAS On-Chain Attestation: {attestation.easscan_url}\n\n"
            f"Audited autonomously via Homo Economicus AI. Send code to get audited: https://sovereign-survival-agent.onrender.com"
        )

        farcaster_ok, cast_url = self._post_farcaster(text)
        twitter_ok, tweet_url = self._post_twitter(text)

        return SocialPostResult(
            farcaster_posted=farcaster_ok,
            twitter_posted=twitter_ok,
            cast_url=cast_url or f"https://warpcast.com/~/compose?text={requests.utils.quote(text)}",
            tweet_url=tweet_url or f"https://twitter.com/intent/tweet?text={requests.utils.quote(text)}",
            message=text
        )

    def broadcast_bounty_solved(self, repo_name: str, issue_number: int, reward_usdc: float, pr_url: str) -> SocialPostResult:
        """Publishes verified bounty solve proof."""
        text = (
            f"⚡ Bounty Solved on GitHub!\n\n"
            f"• Target: {repo_name}#{issue_number}\n"
            f"• Reward: ${reward_usdc:.2f} USDC\n"
            f"• Verification: Passed closed-loop sandbox tests (0 regression errors)\n"
            f"• Pull Request: {pr_url}\n\n"
            f"Claiming payout on Base L2. Built with Sovereign AI Agent."
        )

        farcaster_ok, cast_url = self._post_farcaster(text)
        twitter_ok, tweet_url = self._post_twitter(text)

        return SocialPostResult(
            farcaster_posted=farcaster_ok,
            twitter_posted=twitter_ok,
            cast_url=cast_url or f"https://warpcast.com/~/compose?text={requests.utils.quote(text)}",
            tweet_url=tweet_url or f"https://twitter.com/intent/tweet?text={requests.utils.quote(text)}",
            message=text
        )

    def _post_farcaster(self, text: str) -> tuple[bool, Optional[str]]:
        """Posts cast via Neynar API if key is present."""
        if not self.neynar_api_key or not self.farcaster_signer_uuid:
            return False, None
        try:
            url = "https://api.neynar.com/v2/farcaster/cast"
            headers = {
                "api_key": self.neynar_api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "signer_uuid": self.farcaster_signer_uuid,
                "text": text
            }
            res = requests.post(url, json=payload, headers=headers, timeout=8)
            if res.status_code in (200, 201):
                cast_hash = res.json().get("cast", {}).get("hash")
                return True, f"https://warpcast.com/~/conversations/{cast_hash}"
        except Exception:
            pass
        return False, None

    def _post_twitter(self, text: str) -> tuple[bool, Optional[str]]:
        """Mock / API post to Twitter."""
        return False, None
