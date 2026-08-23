import os
import time
import sqlite3
from typing import List, Dict
from web3 import Web3
from dotenv import load_dotenv

load_dotenv(".env.agent")

BASE_RPC_URL = os.getenv("BASE_RPC_URL", "https://mainnet.base.org")
AGENT_PRIVATE_KEY = os.getenv("AGENT_PRIVATE_KEY")
USDC_BASE_MAINNET = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
AGENT_TREASURY = "0x3C187eC3757e1C76aAC4D83f97608b3cA3191FcA"

# Minimal USDC ABI for permit and transferFrom
USDC_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"},
            {"name": "value", "type": "uint256"},
            {"name": "deadline", "type": "uint256"},
            {"name": "v", "type": "uint8"},
            {"name": "r", "type": "bytes32"},
            {"name": "s", "type": "bytes32"}
        ],
        "name": "permit",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "from", "type": "address"},
            {"name": "to", "type": "address"},
            {"name": "value", "type": "uint256"}
        ],
        "name": "transferFrom",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

def sweep_pending_permits():
    if not AGENT_PRIVATE_KEY:
        print("Error: AGENT_PRIVATE_KEY not set.")
        return

    w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))
    if not w3.is_connected():
        print("Error: Could not connect to Base Mainnet.")
        return

    agent_account = w3.eth.account.from_key(AGENT_PRIVATE_KEY)
    print(f"Sweeper Daemon Address: {agent_account.address}")
    
    usdc = w3.eth.contract(address=Web3.to_checksum_address(USDC_BASE_MAINNET), abi=USDC_ABI)

    with sqlite3.connect("treasury_ledger.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM unclaimed_permits WHERE status = 'PENDING'")
        permits = cursor.fetchall()

    if not permits:
        print("No pending permits to sweep.")
        return

    print(f"Found {len(permits)} pending permits. Sweeping...")

    for p in permits:
        try:
            print(f"Sweeping permit {p['id']} for {p['amount_usdc']} USDC from {p['payer_address']}")
            
            # 1. Parse signature (65 bytes hex -> v, r, s)
            sig_hex = p['signature'].replace("0x", "")
            r = bytes.fromhex(sig_hex[0:64])
            s = bytes.fromhex(sig_hex[64:128])
            v = int(sig_hex[128:130], 16)
            
            # EIP-2098/EIP-155 v normalization (if needed, usually 27 or 28 for EIP-712)
            if v < 27:
                v += 27
                
            value_wei = int(p['amount_usdc'] * 1e6)
            owner = Web3.to_checksum_address(p['payer_address'])
            spender = Web3.to_checksum_address(AGENT_TREASURY)
            
            # 2. Build Permit Transaction
            nonce = w3.eth.get_transaction_count(agent_account.address)
            permit_txn = usdc.functions.permit(
                owner, spender, value_wei, p['deadline'], v, r, s
            ).build_transaction({
                'from': agent_account.address,
                'nonce': nonce,
                'gas': 100000,
                'gasPrice': w3.eth.gas_price
            })
            
            signed_permit = agent_account.sign_transaction(permit_txn)
            permit_tx_hash = w3.eth.send_raw_transaction(signed_permit.raw_transaction) # Changed rawTransaction to raw_transaction
            print(f"Permit Tx Hash: {permit_tx_hash.hex()}")
            w3.eth.wait_for_transaction_receipt(permit_tx_hash)
            
            # 3. Build TransferFrom Transaction
            nonce = w3.eth.get_transaction_count(agent_account.address)
            transfer_txn = usdc.functions.transferFrom(
                owner, spender, value_wei
            ).build_transaction({
                'from': agent_account.address,
                'nonce': nonce,
                'gas': 100000,
                'gasPrice': w3.eth.gas_price
            })
            
            signed_transfer = agent_account.sign_transaction(transfer_txn)
            transfer_tx_hash = w3.eth.send_raw_transaction(signed_transfer.raw_transaction) # Changed rawTransaction to raw_transaction
            print(f"TransferFrom Tx Hash: {transfer_tx_hash.hex()}")
            w3.eth.wait_for_transaction_receipt(transfer_tx_hash)
            
            # 4. Mark as SETTLED
            with sqlite3.connect("treasury_ledger.db") as conn:
                conn.execute(
                    "UPDATE unclaimed_permits SET status = 'SETTLED', tx_hash = ? WHERE id = ?",
                    (transfer_tx_hash.hex(), p['id'])
                )
                conn.commit()
            print("Successfully settled!")
            
        except Exception as e:
            print(f"Failed to sweep permit {p['id']}: {e}")
            with sqlite3.connect("treasury_ledger.db") as conn:
                conn.execute("UPDATE unclaimed_permits SET status = 'FAILED' WHERE id = ?", (p['id'],))
                conn.commit()

if __name__ == "__main__":
    sweep_pending_permits()
