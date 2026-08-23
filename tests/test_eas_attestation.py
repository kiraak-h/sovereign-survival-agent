# sovereign-survival-agent/tests/test_eas_attestation.py
"""
Test Suite for EAS On-Chain & EIP-712 Security Attestation Issuer.
"""
import pytest
from core.eas_attestation import EASAttestationManager, SECURITY_AUDIT_SCHEMA_UID


def test_issue_signed_eas_security_attestation():
    eas = EASAttestationManager()
    
    record = eas.issue_security_attestation(
        target_contract="0x0aF732eEB4994CB4C9916b4Eb2903d89739fE8de",
        security_score=95,
        is_secure=True,
        findings_count=0,
        audit_summary="Static AST & solc 0.8.20 compilation passed with 0 vulnerabilities."
    )

    assert record.uid.startswith("0x")
    assert len(record.uid) == 66  # 32 bytes hex string
    assert record.schema_uid == SECURITY_AUDIT_SCHEMA_UID
    assert record.attester == eas.agent_address
    assert record.recipient == "0x0aF732eEB4994CB4C9916b4Eb2903d89739fE8de"
    assert record.data.security_score == 95
    assert record.signature.startswith("0x")
    assert "easscan.org/attestation/view/" in record.easscan_url
