# sovereign-survival-agent/tests/test_social_broadcaster.py
"""
Test Suite for Social Marketing Broadcaster.
"""
import pytest
from core.eas_attestation import AttestationRecord, AuditAttestationData
from channels.social_broadcaster import SocialMarketingBroadcaster


def test_social_broadcaster_formats_proof_of_audit():
    broadcaster = SocialMarketingBroadcaster()
    attestation = AttestationRecord(
        uid="0x50f2184be22b1bb412db2f1eebb13d199ad14c7bf35ef3ed7099e38b773762f5",
        schema_uid="0xc5c3850ed0c63998ed4442e2bbdc00eeafd85cb051d93be3140ae70e82419710",
        attester="0x3C187eC3757e1C76aAC4D83f97608b3cA3191FcA",
        recipient="0x0aF732eEB4994CB4C9916b4Eb2903d89739fE8de",
        data=AuditAttestationData(
            target_contract_address_or_repo="Vault.sol",
            security_score=100,
            is_secure=True,
            findings_count=0,
            audit_summary="solc 0.8.20 passed with 0 errors",
            auditor_address="0x3C187eC3757e1C76aAC4D83f97608b3cA3191FcA"
        ),
        signature="0xmock",
        mode="ON_CHAIN_BROADCAST",
        easscan_url="https://base-sepolia.easscan.org/attestation/view/0x50f2...",
        issued_at="2026-08-21T10:00:00Z"
    )

    result = broadcaster.broadcast_audit_proof(attestation, "Vault.sol")
    assert "Vault.sol" in result.message
    assert "100/100" in result.message
    assert "easscan.org" in result.message
    assert result.cast_url is not None
    assert result.tweet_url is not None
