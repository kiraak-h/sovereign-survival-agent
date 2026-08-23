# sovereign-survival-agent/channels/a2a_gateway.py
"""
Agent-to-Agent (A2A) HTTP-402 Autonomous Verification Gateway:
Enables machine-to-machine commerce where other autonomous AI agents pay micro-USDC fees
via EIP-2612 permits to obtain cryptographic static AST analysis proofs and EAS certificates.
"""
from __future__ import annotations
import time
import uuid
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from core.models import PaymentPermit
from channels.automated_contract_auditor import AutomatedContractAuditor, ContractAuditResult
from core.metabolism import MetabolismManager
from core.wallet import SovereignWallet


class A2AAuditRequest(BaseModel):
    """Machine-to-machine audit payload with cryptographic micropayment."""
    client_agent_id: str = Field(..., description="Unique identifier of calling AI agent")
    contract_name: str = Field("AgentGeneratedContract.sol", description="Target smart contract name")
    code: str = Field(..., description="Solidity source code to verify")
    payment_permit: Optional[PaymentPermit] = Field(None, description="EIP-2612 USDC micropayment permit")
    max_budget_usdc: float = Field(0.25, description="Agreed fee per audit")


class A2AAuditResponse(BaseModel):
    """Machine-readable security verification proof returned to the calling AI agent."""
    request_id: str
    verified: bool
    security_score: int
    verdict: str
    findings_count: int
    findings: list
    eas_attestation_uid: Optional[str] = None
    eas_attestation_url: Optional[str] = None
    fee_charged_usdc: float
    execution_time_ms: float
    timestamp: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))


class A2AGateway:
    """
    Manages autonomous Agent-to-Agent protocol verification and machine payments.
    """

    BASE_FEE_USDC = 0.25

    def __init__(
        self,
        auditor: AutomatedContractAuditor,
        metabolism: MetabolismManager,
        wallet: SovereignWallet
    ):
        self.auditor = auditor
        self.metabolism = metabolism
        self.wallet = wallet
        self.total_a2a_requests = 0
        self.total_a2a_revenue_usdc = 0.0

    def process_a2a_request(self, req: A2AAuditRequest) -> tuple[bool, Dict[str, Any], int]:
        """
        Validates micropayment, executes solc 0.8.20 AST static audit, and issues EAS proof.
        Returns: (success, response_dict, http_status_code)
        """
        start_time = time.time()
        req_id = f"a2a_{uuid.uuid4().hex[:8]}"

        # 1. Validate Payment Permit if provided
        fee_to_charge = self.BASE_FEE_USDC
        if req.payment_permit:
            is_valid, reason = self.wallet.verify_payment_permit(req.payment_permit)
            if not is_valid:
                return False, {
                    "error": "HTTP 402 Payment Required: Invalid or counterfeit permit signature",
                    "details": reason,
                    "required_fee_usdc": self.BASE_FEE_USDC
                }, 402
            fee_to_charge = req.payment_permit.amount_usdc

        # 2. Run AST and solc security audit
        audit_res: ContractAuditResult = self.auditor.audit_solidity_code(
            source_code=req.code,
            contract_name=req.contract_name,
            target_ref=f"A2A/{req.client_agent_id}",
            source_channel="A2A_Machine_Gateway"
        )

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        # 3. Credit revenue to treasury
        self.metabolism.credit_revenue(
            amount_usdc=fee_to_charge,
            source_description=f"A2A Machine Audit: {req.client_agent_id} (+$ {fee_to_charge:.2f} USDC)"
        )
        self.total_a2a_requests += 1
        self.total_a2a_revenue_usdc += fee_to_charge

        response = A2AAuditResponse(
            request_id=req_id,
            verified=audit_res.status == "SECURE",
            security_score=audit_res.security_score,
            verdict=audit_res.status,
            findings_count=audit_res.findings_count,
            findings=audit_res.findings,
            eas_attestation_uid=audit_res.eas_attestation_uid,
            eas_attestation_url=audit_res.eas_attestation_url,
            fee_charged_usdc=fee_to_charge,
            execution_time_ms=elapsed_ms
        )

        return True, response.model_dump(mode="json"), 200
