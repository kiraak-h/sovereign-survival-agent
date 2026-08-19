# agent/simulation/multi_agent_arena.py
"""
Multi-Agent Survival Arena (Homo Economicus Tournament):
Simulates a competitive Base L2 decentralized economy where multiple AI agents with
different survival strategies (Frugal, Reckless, Local-Only, Sovereign-Adaptive)
compete for scarce bounties and market share under fixed metabolic burn.
"""
from __future__ import annotations
import random
from typing import List, Dict
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from eth_account import Account
from core.models import (
    AgentState,
    UrgencyTier,
    ModelTier,
    Bounty,
    TaskType
)
from core.metabolism import MetabolismManager
from core.policy_engine import SurvivalPolicyEngine
from core.wallet import SovereignWallet
from channels.bounty_hunter import BountyHunter
from simulation.market_simulator import BOUNTY_TEMPLATES


class ArenaAgent:
    """An individual agent archetype in the survival tournament."""

    def __init__(self, name: str, strategy: str, initial_treasury: float = 8.0, hourly_rent: float = 0.05):
        self.name = name
        self.strategy = strategy  # "SOVEREIGN_ADAPTIVE", "RECKLESS_FRONTIER", "LOCAL_ONLY", "CONSERVATIVE"
        self.state = AgentState(
            agent_address="",
            session_key_address="",
            treasury_usdc=initial_treasury,
            treasury_eth=0.005,
            fixed_burn_rate_hourly=hourly_rent
        )
        self.metabolism = MetabolismManager(self.state)
        self.wallet = SovereignWallet(self.state)
        self.policy = SurvivalPolicyEngine(self.state)
        self.hunter = BountyHunter(self.metabolism, self.policy, self.wallet)
        self.rounds_survived = 0

    def decide_and_bid(self, bounty: Bounty) -> bool:
        """Determines whether the agent bids on and executes a bounty based on strategy."""
        if not self.state.is_alive:
            return False

        if self.strategy == "RECKLESS_FRONTIER":
            # Always attempts every bounty using expensive REASONING_PRO model
            estimated_tokens = int(800 + bounty.difficulty_score * 3000)
            cost = self.metabolism.consume_compute(
                model=ModelTier.REASONING_PRO,
                input_tokens=int(estimated_tokens * 0.65),
                output_tokens=int(estimated_tokens * 0.35),
                task_label=f"Reckless: {bounty.title}"
            )
            # 95% success rate but huge token cost
            if random.random() <= 0.95:
                self.metabolism.credit_revenue(bounty.reward_usdc, f"Reckless payout {bounty.title}")
                return True
            else:
                self.metabolism.record_task_failure(bounty.reward_usdc * 0.1, "Reckless failure")
                return False

        elif self.strategy == "LOCAL_ONLY":
            # Only uses FREE_LOCAL (zero token cost) but low success rate on hard tasks
            cost = self.metabolism.consume_compute(
                model=ModelTier.FREE_LOCAL,
                input_tokens=500,
                output_tokens=200,
                task_label=f"Local: {bounty.title}"
            )
            # Low success rate on complex tasks
            p_success = max(0.20, 0.70 - (bounty.difficulty_score * 0.5))
            if random.random() <= p_success:
                self.metabolism.credit_revenue(bounty.reward_usdc, f"Local payout {bounty.title}")
                return True
            else:
                self.metabolism.record_task_failure(bounty.reward_usdc * 0.1, "Local failure")
                return False

        elif self.strategy == "CONSERVATIVE":
            # Only takes extremely easy, high-margin bounties
            if bounty.difficulty_score > 0.40 or bounty.reward_usdc < 2.00:
                return False
            success, _, _ = self.hunter.evaluate_and_execute_bounty(bounty)
            return success

        else:  # "SOVEREIGN_ADAPTIVE" (Our complete dynamic system)
            success, _, _ = self.hunter.evaluate_and_execute_bounty(bounty)
            return success


class SurvivalArena:
    """Simulates multi-agent competition for scarce market capital."""

    def __init__(self, console: Console | None = None):
        self.console = console or Console(force_terminal=True, legacy_windows=False)
        self.agents: List[ArenaAgent] = [
            ArenaAgent("Agent Alpha (Sovereign Adaptive)", "SOVEREIGN_ADAPTIVE", initial_treasury=8.0),
            ArenaAgent("Agent Beta (Reckless Frontier)", "RECKLESS_FRONTIER", initial_treasury=8.0),
            ArenaAgent("Agent Gamma (Local-Only Heuristics)", "LOCAL_ONLY", initial_treasury=8.0),
            ArenaAgent("Agent Delta (Ultra Conservative)", "CONSERVATIVE", initial_treasury=8.0),
        ]

    def run_tournament(self, total_rounds: int = 15):
        """Runs N rounds of market competition."""
        self.console.print(Panel.fit(
            f"[bold magenta]=== MULTI-AGENT SURVIVAL ARENA (Base L2 Economy) ===[/]\n"
            f"Testing 4 AI Agent archetypes competing over {total_rounds} market cycles with metabolic burn.",
            border_style="magenta"
        ))

        client_account = Account.create()

        for round_num in range(1, total_rounds + 1):
            # 1. Deduct fixed metabolic rent for all agents
            for agent in self.agents:
                if agent.state.is_alive:
                    agent.metabolism.tick_metabolic_cost()
                    agent.rounds_survived += 1

            # 2. Generate 3 competitive bounties
            selected_templates = random.sample(BOUNTY_TEMPLATES, 3)
            bounties = [
                Bounty(
                    bounty_id=f"b_{round_num}_{i}",
                    title=t[0],
                    description=t[0],
                    task_type=t[1],
                    reward_usdc=round(t[3] * random.uniform(0.9, 1.2), 2),
                    deadline_ticks=10,
                    difficulty_score=t[2],
                    issuer_address=client_account.address,
                    escrow_address="0xescrow"
                )
                for i, t in enumerate(selected_templates)
            ]

            # 3. Agents bid and compete
            for bounty in bounties:
                for agent in self.agents:
                    if agent.state.is_alive:
                        agent.decide_and_bid(bounty)

        self.print_leaderboard()

    def print_leaderboard(self):
        """Prints the final survival tournament scoreboard."""
        table = Table(
            title="=== MULTI-AGENT SURVIVAL LEADERBOARD ===",
            title_style="bold yellow",
            expand=True,
            header_style="bold cyan"
        )
        table.add_column("Agent Name", style="bold white", width=30)
        table.add_column("Status", width=14)
        table.add_column("Treasury", justify="right", width=14)
        table.add_column("Net Profit", justify="right", width=14)
        table.add_column("Tokens Used", justify="right", width=14)
        table.add_column("Tasks (W/L)", justify="center", width=14)
        table.add_column("Rounds", justify="center", width=10)

        # Sort by alive first, then highest treasury
        sorted_agents = sorted(
            self.agents,
            key=lambda a: (a.state.is_alive, a.state.treasury_usdc),
            reverse=True
        )

        for a in sorted_agents:
            status_str = "[green]ALIVE[/]" if a.state.is_alive else f"[red]DEAD ({a.state.death_cause[:12]}...)[/]"
            net_profit = a.state.total_revenue_earned - a.state.total_burn_cost
            profit_str = f"+${net_profit:.2f}" if net_profit >= 0 else f"-${abs(net_profit):.2f}"
            profit_style = "green" if net_profit >= 0 else "red"

            table.add_row(
                a.name,
                status_str,
                f"${a.state.treasury_usdc:.2f}",
                f"[{profit_style}]{profit_str}[/]",
                f"{a.state.total_compute_tokens_used:,}",
                f"{a.state.tasks_completed} / {a.state.tasks_failed}",
                str(a.rounds_survived)
            )

        self.console.print("\n")
        self.console.print(table)


def main():
    arena = SurvivalArena()
    arena.run_tournament(total_rounds=15)


if __name__ == "__main__":
    main()
