# agent/runner.py
"""
Sovereign Survival Agent Daemon:
Main heartbeat runner executing continuous metabolic cycles, processing incoming HTTP-402
service requests, solving on-chain bounties, managing Base L2 wallet guardrails, and rendering live vitals.
"""
from __future__ import annotations
import time
import argparse
from typing import Optional
from rich.console import Console
from core.models import AgentState, UrgencyTier
from core.metabolism import MetabolismManager
from core.policy_engine import SurvivalPolicyEngine
from core.wallet import SovereignWallet
from channels.service_oracle import ServiceOracle
from channels.bounty_hunter import BountyHunter
from dashboard import AgentDashboard


class SovereignSurvivalDaemon:
    """
    Main orchestrator for the sovereign decentralized agent.
    """

    def __init__(
        self,
        seed_treasury_usdc: float = 12.0,
        fixed_hourly_rent: float = 0.05,
        console: Optional[Console] = None
    ):
        self.console = console or Console(force_terminal=True, legacy_windows=False)
        self.state = AgentState(
            agent_address="",
            session_key_address="",
            treasury_usdc=seed_treasury_usdc,
            treasury_eth=0.005,
            fixed_burn_rate_hourly=fixed_hourly_rent
        )
        self.metabolism = MetabolismManager(self.state)
        self.wallet = SovereignWallet(self.state)
        self.policy = SurvivalPolicyEngine(self.state)
        self.service_oracle = ServiceOracle(self.metabolism, self.policy, self.wallet)
        self.bounty_hunter = BountyHunter(self.metabolism, self.policy, self.wallet)
        self.market = MarketSimulator(self.wallet)
        self.dashboard = AgentDashboard(self.console)

    def execute_cycle(self, cycle_num: int, verbose: bool = True) -> bool:
        """
        Executes a single survival heartbeat tick:
        1. Deduct fixed metabolic hosting rent.
        2. Ingest & process incoming HTTP-402 paid query.
        3. Scan and execute available on-chain bounties.
        4. Check anti-drain policy & vitals.
        Returns: True if agent is alive, False if dead/insolvent.
        """
        if not self.state.is_alive:
            if verbose:
                self.console.print(f"[bold red][HALT] Cycle #{cycle_num}: Agent is INSOLVENT. Cannot proceed.[/]")
            return False

        if verbose:
            self.console.print(f"\n[bold cyan]>>> SURVIVAL CYCLE #{cycle_num} (Treasury: ${self.state.treasury_usdc:.4f} USDC | Urgency: {self.state.urgency_tier.value}) <<<[/]")

        # 1. Metabolic Rent Burn (simulating time passing)
        self.metabolism.tick_metabolic_cost()

        # 2. Process an incoming paid HTTP-402 Service Request
        # 10% chance to test adversary injection defense
        is_attack = (cycle_num % 7 == 0)
        service_req = self.market.generate_service_request(inject_adversary=is_attack)
        resp = self.service_oracle.process_service_request(service_req)

        if resp.success:
            if verbose:
                self.console.print(
                    f"  [green][+] HTTP-402 Service[/]: Audited contract from {service_req.client_address[:8]}... "
                    f"(Earned: +${resp.fee_charged_usdc:.2f}, Score: {resp.result.get('security_score')}/100, "
                    f"Model: {resp.model_used.value})"
                )
        else:
            if verbose:
                self.console.print(f"  [yellow][!] Service Request Rejected[/]: {resp.result.get('error')}")

        # 3. Check for On-Chain Bounties
        bounties = self.market.generate_bounties(count=2)
        for b in bounties:
            success, submission, note = self.bounty_hunter.evaluate_and_execute_bounty(b)
            if verbose:
                if success:
                    self.console.print(f"  [bold green][BOUNTY SOLVED][/]: {note}")
                elif "SKIPPED" in note:
                    self.console.print(f"  [dim yellow]  [-] {note}[/]")
                else:
                    self.console.print(f"  [red]  [x] {note}[/]")

        # 4. Burn a tiny amount of L2 gas for on-chain state sync
        self.metabolism.consume_gas(gas_used_eth=0.000002, tx_label="cycle_sync")

        return self.state.is_alive

    def run_simulation(self, total_cycles: int = 10, delay_seconds: float = 0.5) -> None:
        """Runs N consecutive survival cycles and prints the final ledger."""
        self.console.print(f"[bold magenta]>>> Launching Sovereign Autonomous Agent on Base L2 ({total_cycles} cycles)...[/]\n")

        for i in range(1, total_cycles + 1):
            alive = self.execute_cycle(i, verbose=True)
            if not alive:
                self.console.print(f"\n[bold red][DEAD] Agent starved on cycle #{i}! Cause: {self.state.death_cause}[/]")
                break
            time.sleep(delay_seconds)

        self.console.print("\n" + "=" * 80)
        self.dashboard.print_snapshot(self.state, self.metabolism.ledger)


def main():
    parser = argparse.ArgumentParser(description="Sovereign Earn-to-Survive Autonomous Agent")
    parser.add_argument("--cycles", type=int, default=8, help="Number of survival cycles to simulate")
    parser.add_argument("--treasury", type=float, default=10.0, help="Initial seed treasury USDC")
    parser.add_argument("--delay", type=float, default=0.3, help="Delay in seconds between cycles")
    args = parser.parse_args()

    daemon = SovereignSurvivalDaemon(seed_treasury_usdc=args.treasury)
    daemon.run_simulation(total_cycles=args.cycles, delay_seconds=args.delay)


if __name__ == "__main__":
    main()

