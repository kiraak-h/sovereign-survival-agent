# sovereign-survival-agent/start.py
"""
Production Entrypoint for Render / Docker Cloud Deployments:
Handles dynamic port binding, pre-flight environment verification,
and robust startup error logging.
"""
import os
import sys
import traceback

# Ensure working directory is in python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import uvicorn

def main():
    print("=" * 60)
    print("=== STARTING SOVEREIGN SURVIVAL AGENT (PRODUCTION) ===")
    print("=" * 60)

    port = int(os.environ.get("PORT", os.environ.get("RENDER_PORT", 8000)))
    host = "0.0.0.0"

    print(f"[*] Binding to host: {host}, port: {port}")
    print(f"[*] Python Version: {sys.version}")
    print(f"[*] Environment Check:")
    print(f"    - AGENT_PRIVATE_KEY: {'[+] Configured' if os.environ.get('AGENT_PRIVATE_KEY') else '[-] Fallback generated'}")
    print(f"    - TELEGRAM_BOT_TOKEN: {'[+] Configured' if os.environ.get('TELEGRAM_BOT_TOKEN') else '[-] Not set'}")
    print(f"    - GITHUB_TOKEN: {'[+] Configured' if os.environ.get('GITHUB_TOKEN') else '[-] Not set'}")
    print(f"    - GEMINI_API_KEY: {'[+] Configured' if os.environ.get('GEMINI_API_KEY') else '[-] Not set'}")

    # 1. Pre-flight solc check
    try:
        import solcx
        installed = [str(v) for v in solcx.get_installed_solc_versions()]
        if "0.8.20" not in installed:
            print("[*] Pre-installing solc 0.8.20 via solcx...")
            solcx.install_solc("0.8.20")
        solcx.set_solc_version("0.8.20")
        print("[+] solc 0.8.20 ready.")
    except Exception as e:
        print(f"[!] solcx notice: {e}")

    # 2. Verify server module imports cleanly
    try:
        from server import app
        print("[+] FastAPI application loaded successfully.")
    except Exception as e:
        print(f"\n[FATAL IMPORT ERROR]: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

    # 3. Start Uvicorn Server
    print(f"[+] Starting Uvicorn server on http://{host}:{port} ...")
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    main()
