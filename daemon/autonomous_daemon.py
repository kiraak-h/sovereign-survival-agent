# sovereign-survival-agent/daemon/autonomous_daemon.py
"""
24/7 Autonomous Background Worker Daemon:
Continuously monitors metabolic burn, scans GitHub & Algora for high-EV paid bounties,
executes closed-loop verification repairs in sandboxes, dispatches PRs, and triggers mobile alerts.
"""
from __future__ import annotations
import time
import threading
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from core.models import AgentState, Bounty, TaskType, ModelTier
from core.metabolism import MetabolismManager
from core.policy_engine import SurvivalPolicyEngine
from core.self_correcting_solver import SelfCorrectingSolver, ClosedLoopResult
from core.github_solver import GitHubSolverEngine
from core.notifier import AgentNotifier
from channels.github_bounty_scanner import GitHubBountyScanner, ScannedBounty
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from channels.automated_contract_auditor import AutomatedContractAuditor


class DaemonStatus(BaseModel):
    is_running: bool
    interval_seconds: int
    total_ticks_completed: int
    bounties_scanned: int
    bounties_solved: int
    contracts_audited: int = 0
    total_revenue_claimed: float
    last_tick_time: Optional[str] = None
    last_activity_summary: str = "Daemon Initialized"


class AutonomousDaemon:
    """
    Autonomous background worker that manages 24/7 bounty hunting, smart contract auditing, and metabolism.
    """

    def __init__(
        self,
        metabolism: MetabolismManager,
        policy: SurvivalPolicyEngine,
        scanner: GitHubBountyScanner,
        solver: SelfCorrectingSolver,
        github_solver: GitHubSolverEngine,
        notifier: AgentNotifier,
        auditor: Optional[Any] = None,
        interval_seconds: int = 300
    ):
        self.metabolism = metabolism
        self.policy = policy
        self.scanner = scanner
        self.solver = solver
        self.github_solver = github_solver
        self.notifier = notifier
        self.auditor = auditor
        self.interval_seconds = interval_seconds
        
        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._solved_bounty_ids = set()
        
        self.total_ticks = 0
        self.bounties_scanned_count = 0
        self.bounties_solved_count = 0
        self.contracts_audited_count = 0
        self.total_revenue_claimed = 0.0
        self.last_activity = "Idle"
        self.last_tick_iso: Optional[str] = None


    def start(self):
        """Starts the background worker thread."""
        if self._is_running:
            return
        self._is_running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self.last_activity = "24/7 Autonomous Daemon Started"
        self.notifier.dispatch_alert("⚡ Autonomous Daemon Online", "Agent is now actively scanning for paid bounties 24/7.")

    def stop(self):
        """Stops the background worker thread."""
        self._is_running = False
        self.last_activity = "Autonomous Daemon Paused"

    def run_single_tick(self) -> Dict[str, Any]:
        """Executes a single metabolic cycle and bounty sweep."""
        self.total_ticks += 1
        self.last_tick_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # 1. Deduct hourly hosting rent
        self.metabolism.tick_metabolic_cost()

        # 2. Check if agent is alive
        if not self.metabolism.state.is_alive:
            self.last_activity = f"Agent Insolvent: {self.metabolism.state.death_cause}"
            return {"status": "INSOLVENT", "message": self.last_activity}

        # 3. Scan live bounties
        bounties = self.scanner.scan_all_bounties(min_reward_usdc=30.0, limit=8)
        self.bounties_scanned_count += len(bounties)

        # 3b. Automated 24/7 Smart Contract Audit Sweep
        if self.auditor:
            try:
                self.auditor.run_automated_audit_tick()
                self.contracts_audited_count = len(self.auditor.audited_contracts)
            except Exception:
                pass

        # 4. Filter for high EV un-solved bounties
        solvable_candidates = [
            b for b in bounties
            if f"{b.repo_full_name}#{b.issue_number}" not in self._solved_bounty_ids
            and b.ev_score > 0
        ]


        if not solvable_candidates:
            self.last_activity = f"Tick #{self.total_ticks}: Scanned {len(bounties)} bounties, 0 pending targets."
            return {"status": "IDLE", "bounties_found": len(bounties)}

        # 5. Pick highest EV target
        target = solvable_candidates[0]
        target_id = f"{target.repo_full_name}#{target.issue_number}"
        self._solved_bounty_ids.add(target_id)

        bounty_obj = Bounty(
            bounty_id=target_id,
            title=target.title,
            description=f"Fix issue for {target_id} at {target.url}",
            task_type=target.task_type,
            reward_usdc=target.reward_usdc,
            deadline_ticks=30,
            difficulty_score=target.difficulty_score,
            issuer_address="0x0000000000000000000000000000000000000000",
            escrow_address="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
        )


        # 6. Execute Closed-Loop Verification
        result = self.solver.solve_with_verification(
            bounty=bounty_obj,
            max_attempts=3,
            model_tier=ModelTier.CHEAP_FLASH
        )

        if result.success and result.pull_request:
            self.bounties_solved_count += 1
            self.total_revenue_claimed += target.reward_usdc
            
            # Credit revenue to treasury
            self.metabolism.credit_revenue(
                amount_usdc=target.reward_usdc,
                source_description=f"Auto-Daemon Claim: {target.title[:35]} (+$ {target.reward_usdc:.2f} USDC)"
            )

            # Dispatch PR (or create draft preview)
            dispatch = self.github_solver.dispatch_pull_request(result.pull_request)
            preview_url = dispatch.get("pr_url") or dispatch.get("pr_preview_url", target.url)

            # Notify on mobile
            self.notifier.notify_bounty_solved(
                bounty_title=target.title,
                reward_usdc=target.reward_usdc,
                repo_name=target.repo_full_name,
                issue_number=target.issue_number,
                pr_preview_url=preview_url,
                attempts=result.total_attempts,
                cost_usdc=result.total_cost_usdc
            )

            self.last_activity = f"Tick #{self.total_ticks}: Solved {target_id} (+$ {target.reward_usdc:.2f} USDC)"
            return {
                "status": "SOLVED",
                "target": target_id,
                "reward_usdc": target.reward_usdc,
                "attempts": result.total_attempts,
                "pr_preview": preview_url
            }

        self.last_activity = f"Tick #{self.total_ticks}: Attempted {target_id} - {result.execution_summary}"
        return {"status": "FAILED_ATTEMPT", "target": target_id}

    def get_status(self) -> DaemonStatus:
        """Returns the live status of the daemon."""
        return DaemonStatus(
            is_running=self._is_running,
            interval_seconds=self.interval_seconds,
            total_ticks_completed=self.total_ticks,
            bounties_scanned=self.bounties_scanned_count,
            bounties_solved=self.bounties_solved_count,
            contracts_audited=self.contracts_audited_count,
            total_revenue_claimed=round(self.total_revenue_claimed, 2),
            last_tick_time=self.last_tick_iso,
            last_activity_summary=self.last_activity
        )


    def _run_loop(self):
        """Continuous background worker loop."""
        while self._is_running:
            try:
                self.run_single_tick()
            except Exception as e:
                self.last_activity = f"Daemon Error: {str(e)}"
            
            # Sleep in 1-second intervals to allow fast graceful shutdown
            for _ in range(self.interval_seconds):
                if not self._is_running:
                    break
                time.sleep(1)
