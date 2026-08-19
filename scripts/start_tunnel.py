# sovereign-survival-agent/scripts/start_tunnel.py
"""
1-Click Public HTTPS Cloudflare Tunnel Launcher:
Exposes local port 8000 to the public web using Cloudflare / untun,
saving the public endpoint to deployments/public_url.json for external clients.
"""
from __future__ import annotations
import os
import re
import sys
import json
import time
import subprocess
from pathlib import Path


def start_tunnel(port: int = 8000) -> str:
    """Launches an instant public HTTPS tunnel for the agent API."""
    print("=" * 60)
    print(f"=== LAUNCHING PUBLIC CLOUDFLARE HTTPS TUNNEL (Port {port}) ===")
    print("=" * 60)

    # 1. First try npx untun
    public_url = None
    cmd = ["npx", "--yes", "untun@latest", "tunnel", f"http://localhost:{port}"]

    try:
        print("[*] Spawning tunnel process via npx untun...")
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=True
        )

        # Read output lines looking for https://...
        start_t = time.time()
        while time.time() - start_t < 15:
            line = proc.stdout.readline()
            if not line:
                continue
            print("    ", line.strip())
            match = re.search(r"(https://[\w-]+\.[\w.-]+)", line)
            if match and "github" not in match.group(1) and "npm" not in match.group(1):
                public_url = match.group(1)
                break
    except Exception as e:
        print(f"[!] Tunnel startup notice: {e}")

    if not public_url:
        public_url = f"http://localhost:{port}"

    # Save to deployments manifest
    manifest_path = Path("deployments/public_url.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({
            "public_url": public_url,
            "port": port,
            "is_public": public_url.startswith("https://"),
            "audit_endpoint": f"{public_url}/v1/audit/smart-contract",
            "console_url": f"{public_url}/console",
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }, f, indent=2)

    print(f"\n[+] Public Tunnel Configuration Saved:")
    print(f"    Public Endpoint: {public_url}")
    print(f"    Public Console:  {public_url}/console")
    print(f"    Paid Audit API:  {public_url}/v1/audit/smart-contract")
    return public_url


if __name__ == "__main__":
    start_tunnel()
