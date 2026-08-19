# sovereign-survival-agent/core/telegram_bot_service.py
"""
Interactive Two-Way Telegram Remote Control:
Listens for user commands (/vitals, /scan, /solve, /tick, /status, /help)
allowing complete agent management directly from your phone.
"""
from __future__ import annotations
import os
import time
import threading
import requests
from typing import Dict, Any, List, Optional
from core.models import AgentState, Bounty, TaskType, ModelTier
from core.metabolism import MetabolismManager
from core.self_correcting_solver import SelfCorrectingSolver
from core.github_solver import GitHubSolverEngine
from daemon.autonomous_daemon import AutonomousDaemon
from channels.github_bounty_scanner import GitHubBountyScanner


class TelegramBotService:
    """
    Two-way interactive Telegram bot listener running as a background service.
    """

    def __init__(
        self,
        bot_token: Optional[str] = None,
        allowed_chat_id: Optional[str] = None,
        metabolism: Optional[MetabolismManager] = None,
        daemon: Optional[AutonomousDaemon] = None,
        scanner: Optional[GitHubBountyScanner] = None,
        solver: Optional[SelfCorrectingSolver] = None,
        github_solver: Optional[GitHubSolverEngine] = None
    ):
        self.token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.allowed_chat_id = allowed_chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.metabolism = metabolism
        self.daemon = daemon
        self.scanner = scanner
        self.solver = solver
        self.github_solver = github_solver
        
        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._last_update_id = 0

    def start(self):
        """Starts the long-polling listener thread."""
        if not self.token or self._is_running:
            return
        self._is_running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stops the listener thread."""
        self._is_running = False

    def send_message(self, text: str, chat_id: Optional[str] = None) -> bool:
        """Sends an HTML formatted message to Telegram."""
        cid = chat_id or self.allowed_chat_id
        if not self.token or not cid:
            return False
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            payload = {
                "chat_id": cid,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            res = requests.post(url, json=payload, timeout=8.0)
            return res.status_code == 200
        except Exception:
            return False

    def handle_command(self, cmd_text: str, chat_id: str):
        """Parses and executes Telegram commands."""
        text = cmd_text.strip()
        parts = text.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1].strip() if len(parts) > 1 else ""

        if command in ("/start", "/help"):
            msg = (
                "🤖 <b>Sovereign AI Agent Remote Control</b>\n\n"
                "Available Commands:\n"
                "• <b>/vitals</b> - View treasury, ETH gas, runway & on-chain state\n"
                "• <b>/scan</b> - Scan top live GitHub/Algora paid bounties\n"
                "• <b>/solve &lt;url&gt;</b> - Solve a specific GitHub issue\n"
                "• <b>/tick</b> - Force an immediate metabolic & solve cycle\n"
                "• <b>/daemon start</b> - Turn ON 24/7 background autopilot\n"
                "• <b>/daemon stop</b> - Pause 24/7 background autopilot\n"
                "• <b>/status</b> - View daemon and worker status"
            )
            self.send_message(msg, chat_id)

        elif command == "/vitals":
            if not self.metabolism:
                self.send_message("❌ Metabolism manager not attached.", chat_id)
                return
            state = self.metabolism.state
            msg = (
                f"🧬 <b>Agent Vitals (Base Sepolia L2)</b>\n\n"
                f"• <b>Status:</b> {'🟢 ALIVE' if state.is_alive else '💀 INSOLVENT'}\n"
                f"• <b>Tier:</b> {state.urgency_tier.value}\n"
                f"• <b>Treasury USDC:</b> ${state.treasury_usdc:.4f} USDC\n"
                f"• <b>Gas Balance:</b> {state.treasury_eth:.4f} ETH\n"
                f"• <b>Runway:</b> {state.runway_hours:.1f} Hours\n"
                f"• <b>Hourly Burn:</b> ${self.metabolism.get_hourly_burn_velocity():.4f}/hr\n"
                f"• <b>Total Claimed:</b> +${state.total_revenue_earned:.2f} USDC\n\n"
                f"🔗 <a href='https://sepolia.basescan.org/address/{state.agent_address}'>View on BaseScan ↗</a>"
            )
            self.send_message(msg, chat_id)

        elif command == "/scan":
            if not self.scanner:
                self.send_message("❌ Bounty scanner not attached.", chat_id)
                return
            self.send_message("🔍 Scanning live GitHub & Algora bounties...", chat_id)
            bounties = self.scanner.scan_all_bounties(min_reward_usdc=20.0, limit=4)
            if not bounties:
                self.send_message("No open bounties matching filter criteria.", chat_id)
                return
            
            lines = ["📡 <b>Top Live Paid Bounties:</b>\n"]
            for i, b in enumerate(bounties, 1):
                lines.append(
                    f"<b>{i}. ${b.reward_usdc:.0f} USDC</b> - <code>{b.repo_full_name}#{b.issue_number}</code>\n"
                    f"   <b>Title:</b> {b.title[:45]}...\n"
                    f"   <b>EV:</b> +{b.ev_score} | <a href='{b.url}'>View Issue ↗</a>\n"
                )
            lines.append("<i>Reply /solve &lt;url&gt; to solve any issue.</i>")
            self.send_message("\n".join(lines), chat_id)

        elif command == "/tick":
            if not self.daemon:
                self.send_message("❌ Daemon not attached.", chat_id)
                return
            self.send_message("⚡ Executing manual metabolic cycle & bounty sweep...", chat_id)
            res = self.daemon.run_single_tick()
            status_text = res.get("status", "UNKNOWN")
            if status_text == "SOLVED":
                self.send_message(
                    f"🎉 <b>Bounty Solved & Verified!</b>\n\n"
                    f"• Target: {res.get('target')}\n"
                    f"• Reward: +${res.get('reward_usdc', 0):.2f} USDC\n"
                    f"• Attempts: {res.get('attempts', 1)} (Sandbox 0 Errors)\n"
                    f"• PR Preview: <a href='{res.get('pr_preview')}'>Open GitHub PR ↗</a>",
                    chat_id
                )
            else:
                self.send_message(f"Tick completed. Result: <code>{status_text}</code>", chat_id)

        elif command == "/daemon":
            if not self.daemon:
                self.send_message("❌ Daemon not attached.", chat_id)
                return
            if args == "start":
                self.daemon.start()
                self.send_message("▶ <b>24/7 Autonomous Daemon Started!</b> Scanning every 5 mins.", chat_id)
            elif args == "stop":
                self.daemon.stop()
                self.send_message("⏸ <b>24/7 Autonomous Daemon Paused.</b>", chat_id)
            else:
                st = self.daemon.get_status()
                self.send_message(
                    f"⚙️ <b>Daemon Status:</b> {'🟢 RUNNING' if st.is_running else '⏸ PAUSED'}\n"
                    f"• Ticks: {st.total_ticks_completed}\n"
                    f"• Scanned: {st.bounties_scanned}\n"
                    f"• Solved: {st.bounties_solved}\n"
                    f"• Revenue: +${st.total_revenue_claimed:.2f} USDC",
                    chat_id
                )

        elif command == "/status":
            self.handle_command("/daemon", chat_id)

        elif command == "/solve":
            if not args:
                self.send_message("⚠️ Please provide a GitHub URL:\nExample: <code>/solve https://github.com/owner/repo/issues/12</code>", chat_id)
                return
            if not self.solver:
                self.send_message("❌ Solver engine not attached.", chat_id)
                return
            
            self.send_message(f"🛠️ Spawning isolated sandbox workspace & solving: {args}...", chat_id)
            
            # Construct bounty object
            bounty_obj = Bounty(
                bounty_id="telegram_manual_request",
                title=f"Fix issue: {args}",
                description=f"Telegram user requested solve for {args}",
                task_type=TaskType.CODE_BUG_FIX,
                reward_usdc=100.0,
                deadline_ticks=30,
                difficulty_score=0.5,
                issuer_address="0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
                escrow_address="0x_manual_telegram_escrow"
            )

            result = self.solver.solve_with_verification(bounty_obj, max_attempts=3, model_tier=ModelTier.CHEAP_FLASH)
            if result.success and result.pull_request:
                dispatch = self.github_solver.dispatch_pull_request(result.pull_request) if self.github_solver else {}
                preview_url = dispatch.get("pr_url") or dispatch.get("pr_preview_url", args)
                self.send_message(
                    f"🎉 <b>Successfully Solved & Verified in {result.total_attempts} attempt(s)!</b>\n\n"
                    f"• Target: {result.pull_request.repo_owner}/{result.pull_request.repo_name}#{result.pull_request.issue_number}\n"
                    f"• Inference Cost: ${result.total_cost_usdc:.6f} USDC ({result.total_tokens} tokens)\n"
                    f"• <a href='{preview_url}'>🐙 View Generated Pull Request ↗</a>",
                    chat_id
                )
            else:
                self.send_message(f"❌ Could not verify fix: {result.execution_summary}", chat_id)

        else:
            self.send_message("Unknown command. Type /help to view all commands.", chat_id)

    def _poll_loop(self):
        """Long-polling update loop for Telegram Bot API."""
        while self._is_running:
            try:
                url = f"https://api.telegram.org/bot{self.token}/getUpdates"
                params = {"offset": self._last_update_id + 1, "timeout": 20}
                res = requests.get(url, params=params, timeout=25.0)
                if res.status_code == 200:
                    data = res.json()
                    for update in data.get("result", []):
                        self._last_update_id = update.get("update_id", self._last_update_id)
                        message = update.get("message")
                        if message and "text" in message:
                            chat_id = str(message.get("chat", {}).get("id"))
                            text = message.get("text", "")
                            # If allowed_chat_id is set, only respond to authorized user
                            if not self.allowed_chat_id or chat_id == str(self.allowed_chat_id):
                                self.handle_command(text, chat_id)
            except Exception:
                time.sleep(3)
            time.sleep(1)
