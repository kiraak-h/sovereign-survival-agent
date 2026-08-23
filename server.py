# sovereign-survival-agent/server.py
"""
Sovereign Agent HTTP-402 API Gateway & Real Web3 Cockpit:
Exposes live endpoints for paid smart contract security audits, Base Sepolia on-chain USDC data,
multi-tier LLM gateway (Gemini/OpenAI), closed-loop self-correcting solver, live GitHub PR dispatcher,
Ethereum Attestation Service (EAS) security certificates, and 24/7 Autonomous Daemon control.
"""
from __future__ import annotations
import sys
import uuid
import random
import os
import time

# Ensure UTF-8 stdout/stderr on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Request, Response, status, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

security = HTTPBasic()
def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "admin")
    correct_password = secrets.compare_digest(credentials.password, "sovereign2026")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


from fastapi.responses import HTMLResponse

from pydantic import BaseModel, Field
from core.models import (
    AgentState,
    ServiceRequest,
    PaymentPermit,
    TaskType,
    Bounty,
    ModelTier,
    UrgencyTier
)
from core.metabolism import MetabolismManager
from core.policy_engine import SurvivalPolicyEngine
from core.wallet import SovereignWallet
from core.static_analyzer import RealSolidityStaticAnalyzer
from core.usdc_contract import BaseSepoliaUSDCClient
from core.llm_gateway import LLMGateway
from core.eas_attestation import EASAttestationManager, AttestationRecord
from core.notifier import AgentNotifier
from daemon.autonomous_daemon import AutonomousDaemon
from channels.service_oracle import ServiceOracle
from channels.subcontracting_engine import A2ASubcontractingEngine
from channels.social_broadcaster import SocialMarketingBroadcaster, SocialPostResult
from channels.multi_platform_webhooks import MultiPlatformWebhookHandler, WebhookEventResponse
from simulation.market_simulator import MarketSimulator
from scripts.broadcast_live_tx import check_status_and_deploy, get_connected_w3, BASE_SEPOLIA_USDC



app = FastAPI(docs_url=None, redoc_url=None, 
    title="Sovereign AI Agent API (Base L2)",
    description="Autonomous 'Earn to Survive' Decentralized Agent Gateway with 24/7 Daemon, EAS & GitHub Dispatch",
    version="1.5.0"
)

# Global State Singleton for the Agent
_agent_state = AgentState(
    agent_address="0x3C187eC3757e1C76aAC4D83f97608b3cA3191FcA",
    session_key_address="0x97F88CA501AF4A75C9F8fd8C56d230a43e407134",
    treasury_usdc=34.1816,
    treasury_eth=0.0946,
    fixed_burn_rate_hourly=0.0512
)
_metabolism = MetabolismManager(_agent_state)
_wallet = SovereignWallet(_agent_state)
_policy = SurvivalPolicyEngine(_agent_state)
_oracle = ServiceOracle(_metabolism, _policy, _wallet, base_audit_fee_usdc=0.50)
_a2a_engine = A2ASubcontractingEngine(_metabolism, _policy, _wallet)
_market = MarketSimulator(_wallet)
_static_analyzer = RealSolidityStaticAnalyzer()
_usdc_client = BaseSepoliaUSDCClient()
_llm_gateway = LLMGateway(metabolism=_metabolism)

from channels.automated_contract_auditor import AutomatedContractAuditor
from channels.a2a_gateway import A2AGateway, A2AAuditRequest

_eas_manager = EASAttestationManager(agent_address=_agent_state.agent_address)
_notifier = AgentNotifier()
_social_broadcaster = SocialMarketingBroadcaster()
_webhook_handler = MultiPlatformWebhookHandler()
_auditor = AutomatedContractAuditor(
    static_analyzer=_static_analyzer,
    eas_manager=_eas_manager,
    notifier=_notifier
)
_a2a_gateway = A2AGateway(
    auditor=_auditor,
    metabolism=_metabolism,
    wallet=_wallet
)


_daemon = AutonomousDaemon(
    metabolism=_metabolism,
    policy=_policy,
    notifier=_notifier,
    auditor=_auditor,
    interval_seconds=300
)


from core.telegram_bot_service import TelegramBotService

_telegram_service = TelegramBotService(
    metabolism=_metabolism,
    daemon=_daemon,
    static_analyzer=_static_analyzer,
    eas_manager=_eas_manager,
    auditor=_auditor
)



@app.on_event("startup")
def on_startup():
    """Starts background services including interactive Telegram listener."""
    _telegram_service.start()

@app.on_event("shutdown")
def on_shutdown():
    """Stops background listeners gracefully."""
    _telegram_service.stop()
    _daemon.stop()


@app.get("/health", summary="Health check for cloud deployers")
@app.get("/v1/health", summary="Health check for cloud deployers")
def health_check():
    """Returns 200 OK for Render / Kubernetes health checks."""
    return {"status": "ok", "agent": "alive", "time": time.time()}





class AuditPayload(BaseModel):
    code: str = Field(..., description="Solidity smart contract source code to audit")
    payer_address: str = Field(..., description="EVM address of payer")
    payment_permit: PaymentPermit = Field(..., description="Cryptographic EIP-2612 / HTTP-402 payment permit")
    target_contract_name: str = Field("Vault.sol", description="Contract or repository identifier")


class MockPermitRequest(BaseModel):
    payer_private_key: str = Field(..., description="Private key of client for mock permit signing")
    amount_usdc: float = Field(0.625, description="Payment amount")


class SolveBountyRequest(BaseModel):
    bounty_id: str
    title: str
    description: str
    reward_usdc: float
    task_type: str = "SMART_CONTRACT_AUDIT"
    max_attempts: int = 3


@app.get("/v1/agent/vitals", summary="Fetch real-time metabolic vitals")
def get_agent_vitals(username: str = Depends(get_current_username)):
    """Returns the agent's live treasury, metabolic burn rate, and real Base Sepolia on-chain data."""
    _metabolism.tick_metabolic_cost()
    
    # Query live on-chain testnet balance if connected
    w3, rpc = get_connected_w3()
    live_onchain_eth = 0.0
    if w3.is_connected():
        try:
            bal_wei = w3.eth.get_balance(_agent_state.agent_address)
            live_onchain_eth = float(w3.from_wei(bal_wei, "ether"))
        except Exception:
            pass

    # Query live on-chain Base Sepolia USDC balance
    live_onchain_usdc = _usdc_client.get_onchain_balance(_agent_state.agent_address)

    # Query active network
    active_net = get_active_network()

    return {
        "agent_address": _agent_state.agent_address,
        "session_key": _agent_state.session_key_address,
        "network": f"{active_net.name} ({active_net.chain_id})",
        "is_production": active_net.is_production,
        "is_alive": _agent_state.is_alive,
        "treasury_usdc": round(_agent_state.treasury_usdc, 4),
        "gas_eth": round(_agent_state.treasury_eth, 6),
        "live_onchain_eth": round(live_onchain_eth, 6),
        "live_onchain_usdc": round(live_onchain_usdc, 6),
        "usdc_contract_address": active_net.usdc_address,
        "urgency_tier": _agent_state.urgency_tier.value,
        "runway_hours": _agent_state.runway_hours,
        "hourly_burn_velocity_usdc": round(_metabolism.get_hourly_burn_velocity(), 4),
        "tasks_completed": _agent_state.tasks_completed,
        "tasks_failed": _agent_state.tasks_failed,
        "reputation_score": _agent_state.reputation_score,
        "total_revenue_earned": round(_agent_state.total_revenue_earned, 4),
        "total_burn_cost": round(_agent_state.total_burn_cost, 4),
        "cumulative_profit": round(_agent_state.total_revenue_earned - _agent_state.total_burn_cost, 4),
        "basescan_url": f"{active_net.explorer_url}/address/{_agent_state.agent_address}"
    }



@app.get("/v1/daemon/status", summary="Get 24/7 Autonomous Daemon status")
def get_daemon_status(username: str = Depends(get_current_username)):
    """Returns background worker state and stats."""
    return _daemon.get_status().model_dump(mode="json")


@app.post("/v1/daemon/start", summary="Start 24/7 Autonomous Daemon")
def start_daemon(username: str = Depends(get_current_username)):
    """Starts the background worker thread."""
    _daemon.start()
    return {"success": True, "status": _daemon.get_status().model_dump(mode="json")}


@app.post("/v1/daemon/stop", summary="Stop 24/7 Autonomous Daemon")
def stop_daemon(username: str = Depends(get_current_username)):
    """Stops the background worker thread."""
    _daemon.stop()
    return {"success": True, "status": _daemon.get_status().model_dump(mode="json")}


@app.post("/v1/daemon/tick", summary="Execute manual daemon tick")
def manual_daemon_tick():
    """Executes a single metabolic cycle and bounty sweep immediately."""
    result = _daemon.run_single_tick()
    return {"success": True, "result": result, "status": _daemon.get_status().model_dump(mode="json")}


@app.get("/v1/alerts/recent", summary="Get recent mobile and system alerts")
def get_recent_alerts(limit: int = 15):
    """Returns recent alert notifications."""
    alerts = _notifier.recent_alerts[-limit:]
    return {"count": len(alerts), "alerts": [a.model_dump(mode="json") for a in reversed(alerts)]}


@app.get("/v1/llm/status", summary="Get multi-tier LLM gateway configuration")
def get_llm_status():
    """Returns configured AI reasoning providers and live token pricing."""
    return {
        "gemini_configured": bool(_llm_gateway.gemini_key),
        "openai_configured": bool(_llm_gateway.openai_key),
        "deepseek_configured": bool(_llm_gateway.deepseek_key),
        "active_fallback": "Local-Synthesizer-v1 (AST & Multi-Sandbox)",
        "model_tiers": {
            "CHEAP_FLASH": "gemini-2.5-flash ($0.10/1M in, $0.40/1M out)",
            "BALANCED": "gpt-4o-mini / gemini-flash ($1.00/1M in, $2.50/1M out)",
            "REASONING_PRO": "gemini-2.5-pro / gpt-4o ($5.00/1M in, $15.00/1M out)"
        }
    }


@app.get("/v1/bounties/live", summary="Scan live GitHub and Algora bounties")
def get_live_bounties(min_reward: float = 10.0, limit: int = 10):
    """Scans and returns live developer bounties ranked by Expected Value."""
    bounties = _bounty_scanner.scan_all_bounties(min_reward_usdc=min_reward, limit=limit)
    return {
        "count": len(bounties),
        "bounties": [b.model_dump(mode="json") for b in bounties]
    }


@app.post("/v1/bounties/solve", summary="Solve a live bounty using Closed-Loop Verification")
def solve_live_bounty(req: SolveBountyRequest):
    """Executes closed-loop iterative repair loop, runs native tests in sandbox, and creates verified PR."""
    task_type_enum = TaskType.SMART_CONTRACT_AUDIT
    try:
        task_type_enum = TaskType(req.task_type)
    except Exception:
        pass

    bounty = Bounty(
        bounty_id=req.bounty_id,
        title=req.title,
        description=req.description,
        task_type=task_type_enum,
        reward_usdc=req.reward_usdc,
        deadline_ticks=30,
        difficulty_score=min(0.9, req.reward_usdc / 200.0),
        issuer_address="0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
        escrow_address="0x_algora_bounty_escrow"
    )

    # Execute Closed-Loop Verification
    result = _self_correcting_solver.solve_with_verification(
        bounty=bounty,
        max_attempts=req.max_attempts,
        model_tier=ModelTier.CHEAP_FLASH
    )
    
    dispatch_info = {}
    if result.success and result.pull_request:
        # Credit revenue to treasury
        _metabolism.credit_revenue(
            amount_usdc=req.reward_usdc,
            source_description=f"Bounty Payout Claim: {req.title[:40]} (+$ {req.reward_usdc:.2f} USDC)"
        )
        dispatch_info = _github_solver.dispatch_pull_request(result.pull_request)

        # Notify mobile
        _notifier.notify_bounty_solved(
            bounty_title=req.title,
            reward_usdc=req.reward_usdc,
            repo_name=result.pull_request.repo_owner + "/" + result.pull_request.repo_name,
            issue_number=result.pull_request.issue_number,
            pr_preview_url=dispatch_info.get("pr_url") or dispatch_info.get("pr_preview_url", ""),
            attempts=result.total_attempts,
            cost_usdc=result.total_cost_usdc
        )

    return {
        "success": result.success,
        "summary": result.execution_summary,
        "total_attempts": result.total_attempts,
        "attempts_history": [a.model_dump(mode="json") for a in result.attempts_history],
        "pr_payload": result.pull_request.model_dump(mode="json") if result.pull_request else None,
        "dispatch_info": dispatch_info,
        "total_tokens": result.total_tokens,
        "total_cost_usdc": result.total_cost_usdc,
        "updated_vitals": get_agent_vitals()
    }


@app.get("/v1/usdc/metadata", summary="Get official Base Sepolia USDC token metadata")
def get_usdc_metadata():
    """Returns official metadata for Base Sepolia USDC token contract."""
    return _usdc_client.get_token_metadata()


@app.get("/v1/agent/pricing", summary="Get dynamic service pricing")
def get_service_pricing():
    """Returns dynamic service pricing adjusted for current metabolic urgency."""
    current_fee = _policy.get_dynamic_service_fee(_oracle.base_audit_fee_usdc)
    return {
        "base_fee_usdc": _oracle.base_audit_fee_usdc,
        "current_effective_fee_usdc": current_fee,
        "urgency_tier": _agent_state.urgency_tier.value,
        "accepted_token": "USDC (Base Sepolia L2)",
        "token_contract": BASE_SEPOLIA_USDC,
        "protocol": "HTTP-402 EIP-2612 Permit"
    }


@app.get("/v1/agent/ledger", summary="Get auditable transaction ledger")
def get_financial_ledger(limit: int = 20, username: str = Depends(get_current_username)):
    """Returns recent financial transactions and compute consumption logs."""
    entries = _metabolism.ledger[-limit:] if _metabolism.ledger else []
    return {
        "count": len(entries),
        "ledger": [entry.model_dump(mode="json") for entry in reversed(entries)]
    }


from core.network_config import get_active_network

@app.get("/v1/network/active", summary="Get active network specification (Base Sepolia vs Base Mainnet)")
def get_network_details():
    """Returns the currently active Base L2 network specification."""
    return get_active_network().model_dump(mode="json")


@app.post("/v1/webhooks/gitcoin", summary="Gitcoin Grant/Bounty Webhook")

def receive_gitcoin_webhook(payload: Dict[str, Any]):
    """Receives Gitcoin Web3 bounty creation events."""
    result = _webhook_handler.process_gitcoin_webhook(payload)
    if result.accepted:
        _notifier.dispatch_alert("🎯 Gitcoin Bounty Received", f"{result.target}: ${result.reward_usdc:.2f} USDC", level="INFO")
    return result.model_dump(mode="json")


@app.post("/v1/webhooks/bountycaster", summary="Bountycaster Farcaster Webhook")
def receive_bountycaster_webhook(payload: Dict[str, Any]):
    """Receives Bountycaster on-chain bounty casts."""
    result = _webhook_handler.process_bountycaster_webhook(payload)
    if result.accepted:
        _notifier.dispatch_alert("🎯 Bountycaster Cast Received", f"${result.reward_usdc:.2f} USDC on-chain reward", level="INFO")
    return result.model_dump(mode="json")


@app.post("/v1/broadcast-onchain", summary="Broadcast live transaction to Base Sepolia L2")

def broadcast_onchain(username: str = Depends(get_current_username)):
    """Runs live on-chain status check, gas verification, and transaction broadcast on Base Sepolia."""
    result = check_status_and_deploy()
    return {
        "success": True,
        "result": result
    }


@app.post("/v1/audit/smart-contract", summary="Submit paid smart contract security audit (HTTP-402 + EAS Attestation)")
def audit_smart_contract(payload: AuditPayload, response: Response):
    """HTTP-402 Gated Smart Contract Security Audit using Real solc static analysis + EAS Attestation."""
    if not _agent_state.is_alive:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Agent is insolvent / deceased: {_agent_state.death_cause}"
        )

    req = ServiceRequest(
        request_id=f"req_{uuid.uuid4().hex[:8]}",
        task_type=TaskType.SMART_CONTRACT_AUDIT,
        client_address=payload.payer_address,
        payload={"code": payload.code},
        payment_permit=payload.payment_permit,
        max_budget_usdc=payload.payment_permit.amount_usdc
    )

    resp = _oracle.process_service_request(req)
    if not resp.success:
        response.status_code = status.HTTP_402_PAYMENT_REQUIRED
        return {
            "error": "HTTP 402 Payment Required or Validation Failed",
            "details": resp.result.get("error"),
            "required_fee_usdc": _policy.get_dynamic_service_fee(_oracle.base_audit_fee_usdc)
        }

    # Issue verified EAS Security Attestation on Base Sepolia
    audit_res = resp.result
    security_score = int(audit_res.get("security_score", 100))
    is_secure = audit_res.get("status") == "SECURE"
    findings_count = len(audit_res.get("findings", []))
    summary_text = audit_res.get("summary", "Security Audit Passed")

    attestation = _eas_manager.issue_security_attestation(
        target_contract=payload.target_contract_name or "0x0aF732eEB4994CB4C9916b4Eb2903d89739fE8de",
        security_score=security_score,
        is_secure=is_secure,
        findings_count=findings_count,
        audit_summary=summary_text,
        broadcast_onchain=True
    )

    _notifier.dispatch_alert(
        title=f"🛡️ Smart Contract Audited (Score: {security_score}/100)",
        message=f"Contract: {payload.target_contract_name}\nEAS UID: {attestation.uid}\nFee Claimed: +$0.62 USDC",
        level="SUCCESS"
    )

    response_dict = resp.model_dump(mode="json")
    response_dict["eas_attestation"] = attestation.model_dump(mode="json")
    return response_dict


@app.post("/v1/mock/create-permit", summary="Create mock permit for testing")
def create_mock_permit(req: MockPermitRequest):
    """Utility endpoint to generate a cryptographically valid permit for test requests."""
    permit = _wallet.create_mock_payment_permit(
        payer_key=req.payer_private_key,
        amount_usdc=req.amount_usdc
    )
    return permit.model_dump(mode="json")


class DirectAuditRequest(BaseModel):
    code: str
    contract_name: str = "Contract.sol"
    target_ref: str = "Direct_API"


@app.post("/v1/audit/scan", summary="Run automated 24/7 contract audit sweep")
def run_contract_audit_scan():
    """Executes automated audit sweep across verified contracts on Base L2."""
    results = _auditor.run_automated_audit_tick()
    return {
        "status": "COMPLETED",
        "audits_completed": len(results),
        "results": [r.model_dump(mode="json") for r in results]
    }


@app.get("/v1/audit/reports", summary="Get all automated smart contract audit reports")
def get_audit_reports(limit: int = 20):
    """Returns recent smart contract audit reports."""
    reports = _auditor.audited_contracts[-limit:]
    return {
        "count": len(reports),
        "reports": [r.model_dump(mode="json") for r in reversed(reports)]
    }


@app.post("/v1/audit/direct", summary="Direct smart contract security audit (DEPRECATED)")
def direct_contract_audit(req: DirectAuditRequest, response: Response):
    """DEPRECATED: Use /v1/a2a/audit for authenticated auditing."""
    response.status_code = 403
    return {"error": "HTTP 403 Forbidden: Free tier deactivated. Upgrade to /v1/a2a/audit using a paid API Key or EIP-2612 permit."}


@app.post("/v1/a2a/audit", summary="Agent-to-Agent (A2A) HTTP-402 Verification Endpoint")
def a2a_audit_contract(req: A2AAuditRequest, response: Response):
    """Machine-to-machine smart contract verification for external AI agents."""
    success, res_data, status_code = _a2a_gateway.process_a2a_request(req)
    response.status_code = status_code
    return res_data
class GenerateKeyRequest(BaseModel):
    tx_hash: str

@app.post("/v1/keys/generate", summary="Generate Prepaid API Key")
def generate_api_key(req: GenerateKeyRequest):
    """Mints a new developer API key by cryptographically verifying a 50 USDC deposit on Base Mainnet."""
    tx_hash = req.tx_hash
    from fastapi import HTTPException
    from scripts.broadcast_live_tx import get_connected_w3
    
    # Connect to Base Mainnet
    w3 = get_connected_w3(is_production=True)
    
    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        tx = w3.eth.get_transaction(tx_hash)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Transaction not found on Base Mainnet: {str(e)}")
        
    if receipt['status'] != 1:
        raise HTTPException(status_code=400, detail="Transaction failed on-chain.")
        
    # Base Mainnet USDC Contract
    REAL_USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    if tx['to'].lower() != REAL_USDC.lower():
        raise HTTPException(status_code=400, detail="Transaction was not sent to the official Base USDC contract.")
        
    input_data = tx['input']
    if type(input_data) == bytes:
        input_data = input_data.hex()
    if input_data.startswith("0x"):
        input_data = input_data[2:]
        
    if not input_data.startswith("a9059cbb"):
        raise HTTPException(status_code=400, detail="Transaction is not an ERC-20 transfer.")
        
    # Decode recipient and amount (a9059cbb is 8 chars, then 64 chars address, 64 chars amount)
    recipient = "0x" + input_data[8:72][-40:]
    amount = int(input_data[72:], 16)
    
    agent_address = _agent_state.agent_address
    if recipient.lower() != agent_address.lower():
        raise HTTPException(status_code=400, detail=f"USDC was not sent to the agent's treasury address: {agent_address}")
        
    if amount < 50_000_000:
        raise HTTPException(status_code=400, detail="Amount must be exactly 50 USDC (50000000 mUSDC).")
        
    from core.ledger import PrepaidLedger
    ledger = PrepaidLedger()
    try:
        api_key = ledger.generate_key(client_name="Web_Checkout", initial_deposit_usdc=50.0, tx_hash=tx_hash)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    _metabolism.credit_revenue(
        amount_usdc=50.0,
        source_description=f"API Key Deposit: $50 USDC via tx {tx_hash[:10]}"
    )
    
    return {"api_key": api_key, "balance_usdc": 50.0, "status": "success"}
@app.post("/v1/ci/audit-pr", summary="GitHub CI/CD Action Smart Contract Security Audit")
def ci_audit_pr(req: DirectAuditRequest):
    """Processes smart contract security audits triggered from GitHub Action workflows."""
    res = _auditor.audit_solidity_code(
        source_code=req.code,
        contract_name=req.contract_name,
        target_ref=req.target_ref,
        source_channel="GitHub_CI_Action"
    )
    return res.model_dump(mode="json")


@app.get("/v1/oracle/metadata", summary="Get on-chain Base Security Oracle metadata")
def get_oracle_metadata():
    """Returns the contract address, ABI, and query fee for AgentSecurityOracle on Base."""
    return {
        "oracle_contract": "0x9c59FdB0153325af6d28164832C224C1DE12e4A5",
        "treasury": _agent_state.agent_address,
        "query_fee_wei": "100000000000000",
        "query_fee_eth": 0.0001,
        "network": "Base Mainnet L2 (Chain ID 8453)",
        "protocol": "AgentSecurityOracle (EAS Attested)"
    }




@app.get("/", response_class=HTMLResponse, summary="Public Developer Portal")
def serve_public_portal():
    with open("templates/public_portal.html", "r", encoding="utf-8") as f:
        return f.read()



@app.get("/admin", response_class=HTMLResponse, summary="Agent Visual Console UI")
@app.get("/console", response_class=HTMLResponse, summary="Agent Visual Console UI")
def serve_admin_cockpit(username: str = Depends(get_current_username)):
    with open("templates/admin_cockpit.html", "r", encoding="utf-8") as f:
        return f.read()
