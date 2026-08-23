# sovereign-survival-agent/scripts/run_verified_bounty_sweep.py
"""
Executes a live bounty sweep using the hardened GitHubBountyScanner and DiffSafetyGuard.
"""
import sys
from dotenv import load_dotenv
from channels.github_bounty_scanner import GitHubBountyScanner
from core.github_solver import GitHubSolverEngine
from core.diff_safety_guard import DiffSafetyGuard
from core.models import Bounty, TaskType

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv(".env.agent")


def main():
    print("==========================================================")
    print("=== 🔍 RUNNING HARDENED LIVE BOUNTY SWEEP & VERIFIER ===")
    print("==========================================================")

    scanner = GitHubBountyScanner()
    print("[*] Sweeping GitHub, Algora, and Bountycaster feeds...")
    scanned_items = scanner.scan_all_bounties(min_reward_usdc=15.0, limit=10)

    print(f"[+] Found {len(scanned_items)} verified bounty candidate(s):\n")
    for idx, b in enumerate(scanned_items, 1):
        print(f"{idx}. [{b.source}] {b.repo_full_name}#{b.issue_number}")
        print(f"   Title: {b.title}")
        print(f"   Verified Reward: ${b.reward_usdc:.2f} USDC | EV: {b.ev_score} | Task: {b.task_type.value}")
        print(f"   URL: {b.url}")
        print("-" * 55)

    if not scanned_items:
        print("[i] No funded bounties (>=$15.00) with active escrow found on this tick.")
        print("[i] Scanner rejected empty/closed bounties cleanly. Background daemon will monitor continuously.")


if __name__ == "__main__":
    main()
