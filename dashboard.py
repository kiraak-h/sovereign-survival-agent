# agent/dashboard.py
"""
Interactive Rich Terminal Dashboard:
Visualizes the sovereign agent's live vitals, treasury balance, metabolic burn velocity,
runway countdown, active jobs, and auditable on-chain transaction ledger.
"""
import sys
from typing import List
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.progress import ProgressBar
from rich.text import Text
from rich.layout import Layout
from core.models import AgentState, UrgencyTier, LedgerEntry


class AgentDashboard:
    """
    Renders a terminal UI showing the agent's real-time metabolic and economic vitals.
    """

    def __init__(self, console: Console | None = None):
        self.console = console or Console(force_terminal=True, legacy_windows=False)

    def render_vitals_panel(self, state: AgentState) -> Panel:
        """Constructs the core vital statistics panel."""
        # Color-coded status badge
        tier_colors = {
            UrgencyTier.THRIVING: ("green", "[THRIVING] (> 72h Runway)"),
            UrgencyTier.STABLE: ("cyan", "[STABLE] (24h - 72h Runway)"),
            UrgencyTier.AUSTERE: ("yellow", "[AUSTERE] (6h - 24h Runway)"),
            UrgencyTier.CRITICAL: ("red", "[CRITICAL / STARVATION] (< 6h Runway)"),
            UrgencyTier.INSOLVENT: ("bold white on red", "[INSOLVENT / BANKRUPT] (0h Runway)")
        }
        color, label = tier_colors.get(state.urgency_tier, ("white", state.urgency_tier.value))

        net_profit = state.total_revenue_earned - state.total_burn_cost
        profit_color = "green" if net_profit >= 0 else "red"

        vitals_table = Table.grid(padding=(0, 2))
        vitals_table.add_column("Key", style="bold white", justify="left")
        vitals_table.add_column("Val", style="bold", justify="left")
        vitals_table.add_column("Key2", style="bold white", justify="left")
        vitals_table.add_column("Val2", style="bold", justify="left")

        vitals_table.add_row(
            "Treasury (USDC):",
            f"[bold green]${state.treasury_usdc:.4f} USDC[/]",
            "Gas Reserve (ETH):",
            f"[bold magenta]{state.treasury_eth:.6f} ETH[/]"
        )
        vitals_table.add_row(
            "Metabolic Status:",
            f"[{color}]{label}[/]",
            "Reputation Score:",
            f"[bold yellow]{state.reputation_score:.1f} / 100.0[/]"
        )
        vitals_table.add_row(
            "Estimated Runway:",
            f"[bold {color}]{state.runway_hours:.1f} hours[/]",
            "Tasks Completed:",
            f"[bold green]{state.tasks_completed}[/] ([red]{state.tasks_failed} failed[/])"
        )
        vitals_table.add_row(
            "Total Revenue:",
            f"[bold green]+${state.total_revenue_earned:.4f}[/]",
            "Total Burn Cost:",
            f"[bold red]-${state.total_burn_cost:.4f}[/]"
        )
        vitals_table.add_row(
            "Cumulative Profit:",
            f"[bold {profit_color}]{'+' if net_profit >= 0 else ''}${net_profit:.4f}[/]",
            "Compute Tokens Used:",
            f"[bold cyan]{state.total_compute_tokens_used:,} tokens[/]"
        )

        return Panel(
            vitals_table,
            title="[bold white]=== SOVEREIGN AGENT METABOLIC VITALS (Base L2) ===[/]",
            border_style=color,
            padding=(1, 2)
        )

    def render_ledger_table(self, ledger: List[LedgerEntry], limit: int = 6) -> Table:
        """Constructs an auditable transaction ledger table."""
        table = Table(
            title="Recent Financial & Metabolic Ledger (Auditable)",
            title_style="bold white",
            expand=True,
            header_style="bold cyan"
        )
        table.add_column("Time", style="dim", width=10)
        table.add_column("Type", width=16)
        table.add_column("Amount", justify="right", width=12)
        table.add_column("Balance", justify="right", width=12)
        table.add_column("Description", style="white")

        recent_entries = ledger[-limit:] if ledger else []
        for entry in reversed(recent_entries):
            type_colors = {
                "REVENUE": "green",
                "COMPUTE_BURN": "yellow",
                "FIXED_RENT_BURN": "magenta",
                "GAS_BURN": "red"
            }
            c = type_colors.get(entry.tx_type.value, "white")
            amount_str = f"+${entry.amount_usdc:.4f}" if entry.amount_usdc > 0 else f"-${abs(entry.amount_usdc):.4f}"
            amount_style = "green" if entry.amount_usdc > 0 else "red"

            table.add_row(
                entry.timestamp.strftime("%H:%M:%S"),
                f"[{c}]{entry.tx_type.value}[/]",
                f"[{amount_style}]{amount_str}[/]",
                f"${entry.balance_after:.4f}",
                entry.description
            )

        return table

    def print_snapshot(self, state: AgentState, ledger: List[LedgerEntry]) -> None:
        """Prints a complete formatted console snapshot."""
        vitals_panel = self.render_vitals_panel(state)
        ledger_table = self.render_ledger_table(ledger)
        group = Group(vitals_panel, ledger_table)
        self.console.print(group)
