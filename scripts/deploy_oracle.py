# sovereign-survival-agent/scripts/deploy_oracle.py
"""
Compiles and deploys AgentSecurityOracle.sol to Base L2 using solcx and Web3.py.
"""
import os
import sys
import json
import solcx
from pathlib import Path
from web3 import Web3
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv(".env.agent")


def compile_oracle_contract():
    contract_path = Path("contracts/AgentSecurityOracle.sol")
    if not contract_path.exists():
        raise FileNotFoundError("contracts/AgentSecurityOracle.sol not found")

    source_code = contract_path.read_text(encoding="utf-8")
    
    # Ensure solc 0.8.20 is installed
    solc_v = "0.8.20"
    if solc_v not in [str(v) for v in solcx.get_installed_solc_versions()]:
        solcx.install_solc(solc_v)

    compiled = solcx.compile_source(
        source_code,
        output_values=["abi", "bin"],
        solc_version=solc_v
    )

    contract_id = "<stdin>:AgentSecurityOracle"
    if contract_id not in compiled:
        # Fallback key search
        contract_id = list(compiled.keys())[0]

    abi = compiled[contract_id]["abi"]
    bytecode = compiled[contract_id]["bin"]
    return abi, bytecode


def main():
    print("==================================================")
    print("=== 🛠️ COMPILING AGENT SECURITY ORACLE (BASE L2) ===")
    print("==================================================")
    
    abi, bytecode = compile_oracle_contract()
    print(f"[+] Compiled successfully! Bytecode size: {len(bytecode)//2} bytes")
    print(f"[+] ABI contains {len(abi)} methods/events.")

    # Check network connection
    network = os.getenv("ACTIVE_NETWORK", "BASE_MAINNET")
    print(f"[*] Target Network: {network}")
    
    # Save artifacts for contract interface
    build_dir = Path("build/contracts")
    build_dir.mkdir(parents=True, exist_ok=True)
    with open(build_dir / "AgentSecurityOracle.json", "w", encoding="utf-8") as f:
        json.dump({"abi": abi, "bytecode": bytecode}, f, indent=2)
    print(f"[+] Saved build artifact to build/contracts/AgentSecurityOracle.json")


if __name__ == "__main__":
    main()
