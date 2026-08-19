# agent/channels/service_oracle.py
"""
Decentralized Service Oracle (HTTP-402 Pay-Per-Query API):
Provides automated Solidity smart contract security audits, code vulnerability scans,
and research synthesis in exchange for verified on-chain USDC micropayments.
"""
from __future__ import annotations
import time
import re
from typing import Dict, Any, List
from core.models import (
    ServiceRequest,
    ServiceResponse,
    TaskType,
    ModelTier
)
from core.metabolism import MetabolismManager
from core.policy_engine import SurvivalPolicyEngine
from core.wallet import SovereignWallet
from core.static_analyzer import RealSolidityStaticAnalyzer


# Known smart contract vulnerability patterns
VULNERABILITY_RULES = [
    {
        "id": "SWC-107",
        "title": "Reentrancy Vulnerability",
        "severity": "CRITICAL",
        "regex": r"\.call\{value:\s*[^}]+\}\s*\([^)]*\)",
        "state_after_call": r"\.call.*(\n|\r\n)+.*(balances\[|owner\s*=|_balances\[)",
        "remediation": "Follow Checks-Effects-Interactions pattern or utilize OpenZeppelin ReentrancyGuard."
    },
    {
        "id": "SWC-115",
        "title": "Authorization through tx.origin",
        "severity": "HIGH",
        "regex": r"tx\.origin\s*==\s*",
        "remediation": "Use msg.sender instead of tx.origin for authentication to prevent phishing exploits."
    },
    {
        "id": "SWC-106",
        "title": "Unprotected Selfdestruct / Delegatecall",
        "severity": "CRITICAL",
        "regex": r"(selfdestruct|delegatecall)\s*\(",
        "remediation": "Ensure selfdestruct and delegatecall targets are strictly restricted by access control."
    },
    {
        "id": "SWC-101",
        "title": "Unchecked Return Value of Low-Level Call",
        "severity": "MEDIUM",
        "regex": r"\.call\{[^}]*\}\s*\([^)]*\)",
        "remediation": "Always verify return value: (bool success, ) = target.call(...); require(success, 'Call failed')."
    },
    {
        "id": "SEC-001",
        "title": "Missing Zero-Address Validation",
        "severity": "LOW",
        "regex": r"address\s+(public|private|internal)?\s*\w+",
        "remediation": "Add require(account != address(0), 'Zero address') checks on constructor and setters."
    }
]


class ServiceOracle:
    """
    Autonomous API server that sells smart contract audits for crypto micropayments.
    """

    def __init__(
        self,
        metabolism: MetabolismManager,
        policy: SurvivalPolicyEngine,
        wallet: SovereignWallet,
        base_audit_fee_usdc: float = 0.50
    ):
        self.metabolism = metabolism
        self.policy = policy
        self.wallet = wallet
        self.base_audit_fee_usdc = base_audit_fee_usdc

    def process_service_request(self, request: ServiceRequest) -> ServiceResponse:
        """
        Handles an incoming paid service request:
        1. Verifies HTTP-402 cryptographic payment permit.
        2. Adjusts dynamic pricing based on agent hunger/urgency.
        3. Executes vulnerability audit / reasoning.
        4. Burns compute tokens & credits revenue.
        5. Returns structured audit report.
        """
        start_time = time.perf_counter()

        # 1. Payment Verification (EIP-2612 / HTTP-402)
        if not request.payment_permit:
            return ServiceResponse(
                request_id=request.request_id,
                success=False,
                result={"error": "HTTP 402 Payment Required: Missing payment permit"},
                fee_charged_usdc=0.0,
                execution_time_ms=0.0,
                model_used=ModelTier.FREE_LOCAL
            )

        valid_permit, reason = self.wallet.verify_payment_permit(request.payment_permit)
        if not valid_permit:
            return ServiceResponse(
                request_id=request.request_id,
                success=False,
                result={"error": f"HTTP 402 Unauthorized: {reason}"},
                fee_charged_usdc=0.0,
                execution_time_ms=0.0,
                model_used=ModelTier.FREE_LOCAL
            )

        # 2. Dynamic Fee Calculation
        current_fee = self.policy.get_dynamic_service_fee(self.base_audit_fee_usdc)
        if request.payment_permit.amount_usdc < current_fee:
            return ServiceResponse(
                request_id=request.request_id,
                success=False,
                result={"error": f"Insufficient permit amount: provided ${request.payment_permit.amount_usdc:.2f}, required ${current_fee:.2f}"},
                fee_charged_usdc=0.0,
                execution_time_ms=0.0,
                model_used=ModelTier.FREE_LOCAL
            )

        # 3. Model Tier Selection & Analysis Execution
        code_snippet = str(request.payload.get("code", ""))
        lines_of_code = len(code_snippet.splitlines())
        estimated_complexity = min(1.0, max(0.2, lines_of_code / 100.0))

        model_tier = self.policy.select_model_tier(estimated_complexity, current_fee)

        # Perform smart contract vulnerability analysis
        audit_findings = self._analyze_solidity_code(code_snippet)
        security_score = max(0, 100 - sum(
            35 if f["severity"] == "CRITICAL" else 20 if f["severity"] == "HIGH" else 10
            for f in audit_findings
        ))

        # 4. Token & Gas Accounting
        estimated_tokens = max(200, lines_of_code * 8 + 300)
        compute_cost = self.metabolism.consume_compute(
            model=model_tier,
            input_tokens=int(estimated_tokens * 0.6),
            output_tokens=int(estimated_tokens * 0.4),
            task_label=f"Audit {request.request_id[:8]}"
        )

        # Credit Revenue
        self.metabolism.credit_revenue(
            amount_usdc=current_fee,
            source_description=f"HTTP-402 Service Fee from {request.client_address[:10]} (Net Profit: +${current_fee - compute_cost:.4f})",
            tx_hash=request.payment_permit.signature[:18]
        )

        execution_time = (time.perf_counter() - start_time) * 1000.0

        return ServiceResponse(
            request_id=request.request_id,
            success=True,
            result={
                "task_type": request.task_type.value,
                "security_score": security_score,
                "status": "SECURE" if security_score >= 80 else "VULNERABLE",
                "findings_count": len(audit_findings),
                "findings": audit_findings,
                "summary": f"Audited {lines_of_code} LOC. Found {len(audit_findings)} potential vulnerabilities. Overall security score: {security_score}/100."
            },
            fee_charged_usdc=current_fee,
            execution_time_ms=round(execution_time, 2),
            model_used=model_tier,
            tx_hash=request.payment_permit.signature[:18]
        )

    def _analyze_solidity_code(self, code: str) -> List[Dict[str, Any]]:
        """Static analysis engine detecting genuine compiler & security vulnerabilities."""
        analyzer = RealSolidityStaticAnalyzer()
        report = analyzer.analyze(code)
        
        findings = []
        for f in report.findings:
            findings.append({
                "id": f.id,
                "title": f.title,
                "severity": f.severity,
                "occurrences": 1,
                "line": f.line,
                "description": f.description,
                "remediation": f.recommendation
            })
        return findings

