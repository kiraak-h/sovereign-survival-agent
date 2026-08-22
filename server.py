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
from fastapi import FastAPI, HTTPException, Request, Response, status
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
from core.github_solver import GitHubSolverEngine, PullRequestPayload
from core.llm_gateway import LLMGateway
from core.self_correcting_solver import SelfCorrectingSolver
from core.eas_attestation import EASAttestationManager, AttestationRecord
from core.notifier import AgentNotifier
from daemon.autonomous_daemon import AutonomousDaemon
from channels.service_oracle import ServiceOracle
from channels.bounty_hunter import BountyHunter
from channels.subcontracting_engine import A2ASubcontractingEngine
from channels.github_bounty_scanner import GitHubBountyScanner, ScannedBounty
from channels.social_broadcaster import SocialMarketingBroadcaster, SocialPostResult
from channels.multi_platform_webhooks import MultiPlatformWebhookHandler, WebhookEventResponse
from simulation.market_simulator import MarketSimulator
from scripts.broadcast_live_tx import check_status_and_deploy, get_connected_w3, BASE_SEPOLIA_USDC



app = FastAPI(
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
_bounty_hunter = BountyHunter(_metabolism, _policy, _wallet)
_a2a_engine = A2ASubcontractingEngine(_metabolism, _policy, _wallet)
_market = MarketSimulator(_wallet)
_static_analyzer = RealSolidityStaticAnalyzer()
_usdc_client = BaseSepoliaUSDCClient()
_bounty_scanner = GitHubBountyScanner()
_llm_gateway = LLMGateway(metabolism=_metabolism)

_self_correcting_solver = SelfCorrectingSolver(agent_address=_agent_state.agent_address, llm_gateway=_llm_gateway)
_github_solver = GitHubSolverEngine(agent_address=_agent_state.agent_address)
_eas_manager = EASAttestationManager(agent_address=_agent_state.agent_address)
_notifier = AgentNotifier()
_social_broadcaster = SocialMarketingBroadcaster()
_webhook_handler = MultiPlatformWebhookHandler()
_daemon = AutonomousDaemon(
    metabolism=_metabolism,
    policy=_policy,
    scanner=_bounty_scanner,
    solver=_self_correcting_solver,
    github_solver=_github_solver,
    notifier=_notifier,
    interval_seconds=300
)


from core.telegram_bot_service import TelegramBotService

_telegram_service = TelegramBotService(
    metabolism=_metabolism,
    daemon=_daemon,
    scanner=_bounty_scanner,
    solver=_self_correcting_solver,
    github_solver=_github_solver,
    static_analyzer=_static_analyzer,
    eas_manager=_eas_manager
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
def get_agent_vitals():
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
def get_daemon_status():
    """Returns background worker state and stats."""
    return _daemon.get_status().model_dump(mode="json")


@app.post("/v1/daemon/start", summary="Start 24/7 Autonomous Daemon")
def start_daemon():
    """Starts the background worker thread."""
    _daemon.start()
    return {"success": True, "status": _daemon.get_status().model_dump(mode="json")}


@app.post("/v1/daemon/stop", summary="Stop 24/7 Autonomous Daemon")
def stop_daemon():
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
def get_financial_ledger(limit: int = 20):
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

def broadcast_onchain():
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


@app.get("/", response_class=HTMLResponse, summary="Agent Visual Console UI")
@app.get("/console", response_class=HTMLResponse, summary="Agent Visual Console UI")
def serve_console():
    """Serves the complete interactive Web Visual Cockpit directly from FastAPI."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sovereign AI Agent Cockpit (Base L2)</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body { background-color: #07080D; color: #F3F4F6; font-family: system-ui, -apple-system, sans-serif; }
    .card { background-color: #0E1018; border: 1px solid rgba(51, 65, 85, 0.6); }
    .pulse { animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .4; } }
  </style>
</head>
<body class="min-h-screen pb-20">
  <!-- Top Navigation Bar -->
  <header class="border-b border-slate-800 bg-[#0B0D14]/90 backdrop-blur sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold">
          🧬
        </div>
        <span class="font-bold tracking-tight text-white">
          SOVEREIGN <span class="text-emerald-400">AGENT COCKPIT</span>
        </span>
        <span class="text-slate-600">/</span>
        <div class="flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-400 font-medium">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 pulse"></span>
          Base Sepolia L2 (84532)
        </div>
      </div>

      <div class="flex items-center gap-3">
        <button onclick="toggleDaemon()" id="daemon-toggle-btn" class="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-emerald-600/30 hover:bg-emerald-600/50 border border-emerald-500/40 text-emerald-300 text-xs font-semibold transition-all cursor-pointer">
          ▶ Start 24/7 Autonomous Daemon
        </button>
        <button onclick="triggerDaemonTick()" class="px-3 py-1.5 rounded-lg bg-indigo-600/30 hover:bg-indigo-600/50 border border-indigo-500/40 text-indigo-300 text-xs font-semibold transition-all">
          ⚡ Force Tick
        </button>
        <a href="/docs" target="_blank" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-xs font-medium transition-colors">
          Swagger Docs ↗
        </a>
      </div>
    </div>
  </header>

  <!-- Main Container -->
  <main class="max-w-7xl mx-auto px-6 pt-8 space-y-8">
    <!-- Identity Header Banner -->
    <div class="p-6 rounded-2xl bg-gradient-to-br from-[#0F121C] to-[#0A0C14] border border-slate-800 relative overflow-hidden shadow-2xl">
      <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 relative z-10">
        <div>
          <div class="flex items-center gap-3">
            <h1 class="text-2xl sm:text-3xl font-bold tracking-tight text-white flex items-center gap-2">
              Homo Economicus AI
              <span id="tier-badge" class="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 font-semibold uppercase tracking-wider">
                THRIVING
              </span>
            </h1>
          </div>
          <p class="text-xs text-slate-400 mt-2 font-mono flex items-center gap-2 flex-wrap">
            <span>Base L2 Smart Account:</span>
            <span id="agent-addr" class="text-slate-200">0x3C187eC3757e1C76aAC4D83f97608b3cA3191FcA</span>
            <button onclick="copyAddress()" class="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white" title="Copy Address">📋 Copy</button>
            <a id="basescan-link" href="https://sepolia.basescan.org/address/0x3C187eC3757e1C76aAC4D83f97608b3cA3191FcA" target="_blank" class="text-emerald-400 hover:underline flex items-center gap-1">
              BaseScan ↗
            </a>
          </p>
        </div>

        <div class="text-right flex items-center gap-3">
          <button onclick="broadcastOnChain()" id="broadcast-btn" class="px-4 py-2 rounded-xl bg-emerald-600/30 hover:bg-emerald-600/50 border border-emerald-500/50 text-emerald-300 text-xs font-bold transition-all shadow-lg cursor-pointer">
            🚀 Broadcast On-Chain (Base L2)
          </button>
        </div>
      </div>

      <!-- Live Broadcast Result Container -->
      <div id="broadcast-output" class="hidden mt-4 p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs font-mono"></div>
    </div>

    <!-- 4 Vital Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
      <div class="card p-5 rounded-xl space-y-2">
        <div class="text-slate-400 text-xs font-medium">On-Chain USDC (Live)</div>
        <div class="text-2xl font-bold text-white tracking-tight" id="usdc-val">0.0000 <span class="text-xs font-normal text-slate-400">USDC</span></div>
        <div class="text-xs text-slate-400 font-mono">Contract: 0x036C...dCF7e</div>
      </div>

      <div class="card p-5 rounded-xl space-y-2">
        <div class="text-slate-400 text-xs font-medium">Base Sepolia Gas (Live)</div>
        <div class="text-2xl font-bold text-emerald-300 tracking-tight" id="gas-val">0.0946 <span class="text-xs font-normal text-slate-400">ETH</span></div>
        <div class="text-xs text-emerald-400">● Funded & Active on Base L2</div>
      </div>

      <div class="card p-5 rounded-xl space-y-2">
        <div class="text-slate-400 text-xs font-medium">24/7 Autonomous Daemon</div>
        <div class="text-2xl font-bold text-cyan-300 tracking-tight" id="daemon-state">IDLE</div>
        <div class="text-xs text-slate-400" id="daemon-summary">Auto-scan every 5 mins</div>
      </div>

      <div class="card p-5 rounded-xl space-y-2">
        <div class="text-slate-400 text-xs font-medium">Survival Runway</div>
        <div class="text-2xl font-bold text-amber-300 tracking-tight" id="runway-val">628.9 <span class="text-xs font-normal text-slate-400">Hours</span></div>
        <div class="text-xs text-slate-400" id="tasks-val">Multi-Language Sandbox Active</div>
      </div>
    </div>

    <!-- Live GitHub & Algora Bounty Stream with Closed-Loop Solver -->
    <div class="card rounded-2xl p-6 space-y-4 shadow-xl">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-lg font-bold text-white tracking-tight flex items-center gap-2">
            📡 Live Bounty Stream (Python • TypeScript • Solidity)
          </h2>
          <p class="text-xs text-slate-400 mt-0.5">
            Real-time GitHub/Algora bounty stream equipped with multi-language sandboxed verification and automatic remote dispatch.
          </p>
        </div>
        <button onclick="fetchBounties()" class="px-3 py-1.5 text-xs rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300">
          🔄 Refresh Feed
        </button>
      </div>

      <div id="bounty-list" class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
        <div class="text-xs text-slate-500 font-mono">Scanning live bounties...</div>
      </div>

      <div id="solver-result" class="hidden mt-4 p-4 rounded-xl border border-emerald-800/50 bg-emerald-950/20 text-xs font-mono space-y-3"></div>
    </div>

    <!-- Interactive Auditor Playground & Real Contracts -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
      <!-- Auditor (7 Cols) -->
      <div class="lg:col-span-7 card rounded-2xl p-6 space-y-4 shadow-xl">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-bold text-white tracking-tight flex items-center gap-2">
            🛡️ solc 0.8.20 Static Analysis & EAS Attestation
          </h2>
          <div class="flex items-center gap-2">
            <button onclick="loadPreset('vulnerable')" class="px-2.5 py-1 text-xs rounded bg-red-950/40 border border-red-800/50 text-red-300 hover:bg-red-900/40">Vulnerable Preset</button>
            <button onclick="loadPreset('secure')" class="px-2.5 py-1 text-xs rounded bg-emerald-950/40 border border-emerald-800/50 text-emerald-300 hover:bg-emerald-900/40">Secure Preset</button>
          </div>
        </div>

        <p class="text-xs text-slate-400">
          Runs genuine <code>solc 0.8.20</code> compilation and broadcasts on-chain <strong>EAS Attestation Certificates</strong> to Base Sepolia.
        </p>

        <textarea id="solidity-input" rows="8" class="w-full font-mono text-xs p-3.5 rounded-xl bg-[#07080D] border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"></textarea>

        <div class="flex items-center justify-between pt-2">
          <div class="text-xs text-slate-400 font-mono">
            Audit Fee: <span class="text-emerald-400 font-bold">0.62 USDC</span> | Engine: <span class="text-cyan-400">solc 0.8.20</span>
          </div>
          <button onclick="runAudit()" id="audit-btn" class="px-5 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 text-white text-xs font-bold transition-all shadow-lg cursor-pointer">
            Run Real Static Audit & Issue EAS
          </button>
        </div>

        <div id="audit-output" class="hidden mt-4 p-4 rounded-xl border space-y-3"></div>
      </div>

      <!-- Real Web3 Contract Specs (5 Cols) -->
      <div class="lg:col-span-5 card rounded-2xl p-6 space-y-4 shadow-xl flex flex-col justify-between">
        <div>
          <h2 class="text-lg font-bold text-white tracking-tight flex items-center gap-2 mb-2">
            🔗 Verified Base Sepolia Registry
          </h2>
          <p class="text-xs text-slate-400 mb-4">
            Live Base Sepolia (84532) contracts queried directly via Web3 RPC.
          </p>

          <div class="space-y-3">
            <div class="p-3 rounded-xl bg-[#07080D] border border-slate-800 space-y-1 text-xs">
              <div class="font-bold text-slate-200">Deployed Agent Policy Guard</div>
              <a href="https://sepolia.basescan.org/address/0x0aF732eEB4994CB4C9916b4Eb2903d89739fE8de" target="_blank" class="text-[11px] font-mono text-cyan-400 hover:underline break-all block">0x0aF732eEB4994CB4C9916b4Eb2903d89739fE8de</a>
              <div class="text-[10px] text-emerald-400 font-mono">● Deployed on Base Sepolia (0.05 ETH Daily Limit)</div>
            </div>
            <div class="p-3 rounded-xl bg-[#07080D] border border-slate-800 space-y-1 text-xs">
              <div class="font-bold text-slate-200">Registered EAS Schema (Live)</div>
              <a href="https://base-sepolia.easscan.org/schema/view/0xc5c3850ed0c63998ed4442e2bbdc00eeafd85cb051d93be3140ae70e82419710" target="_blank" class="text-[11px] font-mono text-cyan-400 hover:underline break-all block">0xc5c3850ed0c63998ed4442e2bbdc00eeafd85cb051d93be3140ae70e82419710</a>
              <div class="text-[10px] text-emerald-400 font-mono">● Registered on EAS SchemaRegistry (0x4200...20)</div>
            </div>
            <div class="p-3 rounded-xl bg-[#07080D] border border-slate-800 space-y-1 text-xs">
              <div class="font-bold text-slate-200">Official Base Sepolia USDC</div>
              <div class="text-[11px] font-mono text-slate-400 break-all">0x036CbD53842c5426634e7929541eC2318f3dCF7e</div>
              <div class="text-[10px] text-emerald-400 font-mono">ERC-20 + EIP-2612 Permit Supported (Decimals: 6)</div>
            </div>
          </div>
        </div>

        <div class="p-3.5 rounded-xl bg-cyan-950/20 border border-cyan-800/40 text-xs text-cyan-300">
          Certificate Standard: <span class="text-white font-mono">EAS On-Chain Attestation (Base L2)</span>
        </div>
      </div>
    </div>
  </main>

  <script>
    const VULN_CODE = `// SPDX-License-Identifier: MIT\\npragma solidity ^0.8.20;\\ncontract Vault {\\n    mapping(address => uint256) public balances;\\n    function withdraw() external {\\n        uint256 bal = balances[msg.sender];\\n        (bool s, ) = msg.sender.call{value: bal}("");\\n        require(s);\\n        balances[msg.sender] = 0;\\n    }\\n}`;
    const SECURE_CODE = `// SPDX-License-Identifier: MIT\\npragma solidity 0.8.20;\\ncontract SecureVault {\\n    mapping(address => uint256) public balances;\\n    function withdraw() external {\\n        uint256 bal = balances[msg.sender];\\n        balances[msg.sender] = 0;\\n        (bool s, ) = msg.sender.call{value: bal}("");\\n        require(s, "Transfer failed");\\n    }\\n}`;

    document.getElementById('solidity-input').value = VULN_CODE;

    function loadPreset(type) {
      document.getElementById('solidity-input').value = (type === 'vulnerable') ? VULN_CODE : SECURE_CODE;
      document.getElementById('audit-output').classList.add('hidden');
    }

    function copyAddress() {
      const addr = document.getElementById('agent-addr').innerText;
      navigator.clipboard.writeText(addr);
      alert('Copied Agent Address: ' + addr);
    }

    async function fetchVitals() {
      try {
        const res = await fetch('/v1/agent/vitals');
        const data = await res.json();
        document.getElementById('usdc-val').innerHTML = `${data.live_onchain_usdc.toFixed(4)} <span class="text-xs font-normal text-slate-400">USDC</span>`;
        document.getElementById('gas-val').innerHTML = `${data.live_onchain_eth.toFixed(4)} <span class="text-xs font-normal text-slate-400">ETH</span>`;
        document.getElementById('runway-val').innerHTML = `${data.runway_hours.toFixed(1)} <span class="text-xs font-normal text-slate-400">Hours</span>`;
        document.getElementById('agent-addr').innerText = data.agent_address;
        document.getElementById('tier-badge').innerText = data.urgency_tier;
        document.getElementById('basescan-link').href = data.basescan_url;
      } catch (e) {
        console.error(e);
      }
    }

    async function fetchDaemonStatus() {
      try {
        const res = await fetch('/v1/daemon/status');
        const data = await res.json();
        const stateEl = document.getElementById('daemon-state');
        const btn = document.getElementById('daemon-toggle-btn');
        
        if (data.is_running) {
          stateEl.innerText = 'ONLINE';
          stateEl.className = 'text-2xl font-bold text-emerald-400 tracking-tight';
          btn.innerText = '⏸ Pause 24/7 Daemon';
          btn.className = 'flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-amber-600/30 hover:bg-amber-600/50 border border-amber-500/40 text-amber-300 text-xs font-semibold transition-all cursor-pointer';
        } else {
          stateEl.innerText = 'IDLE';
          stateEl.className = 'text-2xl font-bold text-cyan-300 tracking-tight';
          btn.innerText = '▶ Start 24/7 Autonomous Daemon';
          btn.className = 'flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-emerald-600/30 hover:bg-emerald-600/50 border border-emerald-500/40 text-emerald-300 text-xs font-semibold transition-all cursor-pointer';
        }
        document.getElementById('daemon-summary').innerText = `Ticks: ${data.total_ticks_completed} | Solved: ${data.bounties_solved} (+$${data.total_revenue_claimed.toFixed(2)})`;
      } catch (e) {
        console.error(e);
      }
    }

    async function toggleDaemon() {
      try {
        const statusRes = await fetch('/v1/daemon/status');
        const data = await statusRes.json();
        const endpoint = data.is_running ? '/v1/daemon/stop' : '/v1/daemon/start';
        await fetch(endpoint, { method: 'POST' });
        await fetchDaemonStatus();
      } catch (e) {
        alert('Daemon toggle error: ' + e.message);
      }
    }

    async function triggerDaemonTick() {
      try {
        const res = await fetch('/v1/daemon/tick', { method: 'POST' });
        const data = await res.json();
        await fetchVitals();
        await fetchDaemonStatus();
        await fetchBounties();
        alert('Manual Tick Processed: ' + JSON.stringify(data.result));
      } catch (e) {
        alert('Tick error: ' + e.message);
      }
    }

    async function fetchBounties() {
      const listEl = document.getElementById('bounty-list');
      try {
        const res = await fetch('/v1/bounties/live');
        const data = await res.json();
        const bounties = data.bounties || [];
        window._scannedBounties = bounties;

        if (bounties.length === 0) {
          listEl.innerHTML = '<div class="text-xs text-slate-500">No active bounties found.</div>';
          return;
        }

        listEl.innerHTML = bounties.map((b, i) => `
          <div class="p-4 rounded-xl bg-[#07080D] border border-slate-800 space-y-2.5 flex flex-col justify-between">
            <div>
              <div class="flex items-center justify-between">
                <span class="px-2 py-0.5 rounded bg-indigo-950/60 border border-indigo-800/40 text-indigo-300 text-[10px] font-bold uppercase">${b.source}</span>
                <span class="text-emerald-400 font-mono font-bold text-sm">$${b.reward_usdc.toFixed(2)} USDC</span>
              </div>
              <a href="${b.url}" target="_blank" class="font-bold text-slate-100 hover:text-cyan-400 text-xs block mt-1.5">${b.title}</a>
              <div class="text-[11px] text-slate-500 font-mono mt-0.5">${b.repo_full_name} #${b.issue_number}</div>
            </div>

            <div class="pt-2 border-t border-slate-800/60 flex items-center justify-between">
              <span class="text-[10px] text-slate-400 font-mono">EV Score: <strong class="text-cyan-300">+${b.ev_score}</strong></span>
              <button onclick="autoSolveBountyByIndex(${i})" class="px-3 py-1 rounded-lg bg-emerald-600/30 hover:bg-emerald-600/50 border border-emerald-500/40 text-emerald-300 text-xs font-bold transition-all cursor-pointer">
                ⚡ Closed-Loop Solve
              </button>
            </div>
          </div>
        `).join('');
      } catch (e) {
        listEl.innerHTML = `<div class="text-red-400 text-xs">Error scanning bounties: ${e.message}</div>`;
      }
    }

    async function autoSolveBountyByIndex(index) {
      const b = (window._scannedBounties || [])[index];
      if (!b) return;

      const resBox = document.getElementById('solver-result');
      resBox.classList.remove('hidden');
      resBox.innerHTML = `<span class="text-cyan-400 animate-pulse">Running Closed-Loop Verification: Spawning isolated sandbox workspace & testing code for ${b.title}...</span>`;

      try {
        const res = await fetch('/v1/bounties/solve', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            bounty_id: `${b.repo_full_name}#${b.issue_number}`,
            title: b.title,
            description: `Fix issue for ${b.repo_full_name}#${b.issue_number} at ${b.url}`,
            reward_usdc: b.reward_usdc,
            task_type: b.task_type || 'SMART_CONTRACT_AUDIT',
            max_attempts: 3
          })
        });

        if (!res.ok) {
          const errText = await res.text();
          throw new Error(`Server returned HTTP ${res.status}: ${errText}`);
        }

        const data = await res.json();
        const pr = data.pr_payload;
        const dispatch = data.dispatch_info || {};

        let attemptsHtml = (data.attempts_history || []).map(a => `
          <div class="p-2 rounded bg-black/50 border border-slate-800 text-[11px]">
            <div class="flex items-center justify-between font-bold">
              <span class="${a.validation_passed ? 'text-emerald-400' : 'text-amber-400'}">Attempt #${a.attempt_number}: ${a.validation_passed ? 'PASSED (0 Errors)' : 'RETRYING'}</span>
              <span class="text-slate-400 font-mono">${a.tokens_used} tokens ($${a.cost_usdc.toFixed(6)})</span>
            </div>
            <div class="text-slate-400 text-[10px] mt-0.5">${a.compiler_or_test_output}</div>
          </div>
        `).join('');

        resBox.innerHTML = `
          <div class="flex items-center justify-between font-bold text-sm text-emerald-400">
            <span>🎉 ${data.summary}</span>
            <span class="text-xs text-slate-400 font-mono">Inference Cost: $${data.total_cost_usdc.toFixed(6)} USDC (${data.total_tokens} tokens)</span>
          </div>
          <div class="space-y-1.5">${attemptsHtml}</div>
          ${pr ? `
            <div class="pt-2 border-t border-slate-800 text-slate-300">
              <div class="flex items-center justify-between">
                <span>Target: <strong class="text-white">${pr.repo_owner}/${pr.repo_name}#${pr.issue_number}</strong></span>
                ${dispatch.pr_preview_url ? `<a href="${dispatch.pr_preview_url}" target="_blank" class="text-cyan-400 hover:underline text-xs font-bold font-mono">🐙 Open GitHub PR Draft ↗</a>` : ''}
              </div>
              <div class="text-slate-400 text-[11px] mt-0.5">Claiming Escrow Payout to Base L2: <code class="text-emerald-400">${pr.target_payout_address}</code></div>
              <div class="mt-2 p-2.5 rounded bg-black/60 border border-slate-800 text-[11px] text-slate-300 font-mono whitespace-pre-wrap">${pr.diff_patch}</div>
            </div>
          ` : ''}
        `;
        await fetchVitals();
        await fetchDaemonStatus();
      } catch (e) {
        resBox.innerHTML = `<div class="text-red-400 font-mono p-2">Solve failed: ${e.message}</div>`;
      }
    }

    async function broadcastOnChain() {
      const btn = document.getElementById('broadcast-btn');
      const out = document.getElementById('broadcast-output');
      btn.innerText = '⏳ Broadcasting on Base L2...';
      out.classList.remove('hidden');
      out.innerHTML = '<span class="text-cyan-400 animate-pulse">Connecting to Base Sepolia RPC and verifying live on-chain state...</span>';

      try {
        const res = await fetch('/v1/broadcast-onchain', { method: 'POST' });
        const json = await res.json();
        const r = json.result;
        
        if (r.status === 'CONFIRMED_ON_CHAIN') {
          out.innerHTML = `
            <div class="text-emerald-400 font-bold">🎉 On-Chain Transaction Confirmed on Base Sepolia!</div>
            <div class="text-slate-300 mt-1">Tx Hash: <a href="${r.basescan_url}" target="_blank" class="text-cyan-400 underline">${r.tx_hash}</a></div>
            <div class="text-slate-400 text-[11px]">Block Number: #${r.block_number} | Gas Used: ${r.gas_used}</div>
          `;
        } else {
          out.innerHTML = `
            <div class="text-amber-400 font-bold">⚠️ Testnet Gas Status</div>
            <div class="text-slate-300 mt-1">Current Balance: ${r.balance_eth.toFixed(6)} ETH</div>
          `;
        }
        await fetchVitals();
      } finally {
        btn.innerText = '🚀 Broadcast On-Chain (Base L2)';
      }
    }

    async function runAudit() {
      const btn = document.getElementById('audit-btn');
      const out = document.getElementById('audit-output');
      btn.innerText = 'Compiling & Issuing EAS Attestation...';
      const code = document.getElementById('solidity-input').value;

      try {
        const permitRes = await fetch('/v1/mock/create-permit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            payer_private_key: '0x' + Array.from(crypto.getRandomValues(new Uint8Array(32))).map(b => b.toString(16).padStart(2, '0')).join(''),
            amount_usdc: 0.625
          })
        });
        const permit = await permitRes.json();

        const auditRes = await fetch('/v1/audit/smart-contract', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            code: code,
            payer_address: '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f',
            payment_permit: permit,
            target_contract_name: 'Vault.sol'
          })
        });

        const data = await auditRes.json();
        const res = data.result;
        const eas = data.eas_attestation;
        const isVuln = res.status === 'VULNERABLE';

        out.classList.remove('hidden');
        out.className = `mt-4 p-4 rounded-xl border space-y-3 ${isVuln ? 'bg-red-950/20 border-red-800/50' : 'bg-emerald-950/20 border-emerald-800/50'}`;
        
        let findingsHtml = (res.findings || []).map(f => `
          <div class="p-2 rounded bg-black/40 border border-slate-800 text-xs">
            <div class="font-bold ${f.severity === 'CRITICAL' ? 'text-red-400' : 'text-amber-400'}">[${f.id}] ${f.title} (${f.severity})</div>
            <div class="text-slate-300 mt-0.5">${f.description || f.remediation}</div>
          </div>
        `).join('');

        out.innerHTML = `
          <div class="flex items-center justify-between font-bold text-sm">
            <span>Status: <span class="${isVuln ? 'text-red-400' : 'text-emerald-400'}">${res.status}</span></span>
            <span class="font-mono text-xs px-2 py-0.5 rounded bg-black/40">Security Score: ${res.security_score}/100</span>
          </div>
          <p class="text-xs text-slate-300 font-mono">${res.summary}</p>
          <div class="space-y-1.5 pt-1">${findingsHtml}</div>
          
          ${eas ? `
            <div class="pt-3 border-t border-slate-800/80 mt-2 space-y-1 text-xs font-mono">
              <div class="flex items-center justify-between text-cyan-300 font-bold">
                <span>📜 EAS Security Attestation (Base L2)</span>
                <span class="text-[10px] text-slate-400 font-normal">${eas.mode}</span>
              </div>
              <div class="text-[11px] text-slate-300 break-all">UID: <span class="text-emerald-400">${eas.uid}</span></div>
              <div class="text-[10px] text-slate-400 break-all">Attester: ${eas.attester}</div>
              ${eas.tx_hash ? `<div class="text-[10px] text-slate-400 break-all">Tx Hash: <a href="${eas.basescan_url}" target="_blank" class="text-cyan-400 underline">${eas.tx_hash}</a></div>` : ''}
              <div class="pt-1">
                <a href="${eas.easscan_url}" target="_blank" class="text-cyan-400 hover:underline text-[11px] inline-flex items-center gap-1 font-bold">
                  View on Base EAS Scan ↗
                </a>
              </div>
            </div>
          ` : ''}
        `;
        await fetchVitals();
      } catch (e) {
        out.classList.remove('hidden');
        out.innerHTML = `<div class="text-red-400 text-xs">Audit Error: ${e.message}</div>`;
      } finally {
        btn.innerText = 'Run Real Static Audit & Issue EAS';
      }
    }

    fetchVitals();
    fetchDaemonStatus();
    fetchBounties();
    setInterval(() => {
      fetchVitals();
      fetchDaemonStatus();
    }, 6000);
  </script>
</body>
</html>
"""
