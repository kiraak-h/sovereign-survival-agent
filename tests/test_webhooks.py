# sovereign-survival-agent/tests/test_webhooks.py
"""
Test Suite for Multi-Platform Webhook Handler.
"""
import pytest
from channels.multi_platform_webhooks import MultiPlatformWebhookHandler


def test_polar_webhook_processing():
    handler = MultiPlatformWebhookHandler()
    payload = {
        "type": "pledge.created",
        "data": {
            "issue": {
                "number": 42,
                "repository": {
                    "name": "staking-vault",
                    "organization": {"name": "calcom"}
                }
            },
            "pledge": {"amount": 7500}  # $75.00
        }
    }

    res = handler.process_polar_webhook(payload)
    assert res.accepted is True
    assert res.reward_usdc == 75.0
    assert "calcom/staking-vault#42" in res.target


def test_gitcoin_webhook_processing():
    handler = MultiPlatformWebhookHandler()
    payload = {
        "title": "Smart Contract Gas Optimization",
        "amount_usdc": 120.0,
        "repo": "ethereum/optimism-bridge"
    }

    res = handler.process_gitcoin_webhook(payload)
    assert res.accepted is True
    assert res.reward_usdc == 120.0
    assert "ethereum/optimism-bridge" in res.target


def test_bountycaster_webhook_processing():
    handler = MultiPlatformWebhookHandler()
    payload = {
        "text": "@bountycaster 100 USDC to fix reentrancy guard in vault.sol",
        "value_usdc": 100.0,
        "cast_hash": "0xabc123"
    }

    res = handler.process_bountycaster_webhook(payload)
    assert res.accepted is True
    assert res.reward_usdc == 100.0
