# sovereign-survival-agent/tests/test_daemon.py
"""
Test Suite for 24/7 Autonomous Daemon.
"""
import pytest
from core.models import AgentState
from core.metabolism import MetabolismManager
from core.policy_engine import SurvivalPolicyEngine
from core.llm_gateway import LLMGateway
from core.self_correcting_solver import SelfCorrectingSolver
from core.github_solver import GitHubSolverEngine
from core.notifier import AgentNotifier
from channels.github_bounty_scanner import GitHubBountyScanner
from daemon.autonomous_daemon import AutonomousDaemon


def test_autonomous_daemon_executes_single_tick():
    state = AgentState(
        agent_address="0x3C187eC3757e1C76aAC4D83f97608b3cA3191FcA",
        session_key_address="0x97F88CA501AF4A75C9F8fd8C56d230a43e407134",
        treasury_usdc=30.0
    )
    metabolism = MetabolismManager(state)
    policy = SurvivalPolicyEngine(state)
    scanner = GitHubBountyScanner()
    llm = LLMGateway(metabolism=metabolism)
    solver = SelfCorrectingSolver(agent_address=state.agent_address, llm_gateway=llm)
    github_solver = GitHubSolverEngine(agent_address=state.agent_address)
    notifier = AgentNotifier()

    daemon = AutonomousDaemon(
        metabolism=metabolism,
        policy=policy,
        scanner=scanner,
        solver=solver,
        github_solver=github_solver,
        notifier=notifier,
        interval_seconds=300
    )

    result = daemon.run_single_tick()
    assert result is not None
    assert "status" in result
    status = daemon.get_status()
    assert status.total_ticks_completed == 1
    assert status.bounties_scanned > 0
