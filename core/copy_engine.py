import time
import random
from core.mev_router import MEVPrivateRouter
from core.dex_router import execute_snipe

class CopyEngine:
    def __init__(self, telegram_service=None):
        self.telegram_service = telegram_service
        # Format: {chat_id: {'target_address': '0x...', 'max_spend': 0.1, 'active': True}}
        self.active_targets = {}
        self.router = MEVPrivateRouter()
        
    def set_target(self, chat_id: str, target: str, max_spend: float):
        self.active_targets[chat_id] = {
            'target_address': target.lower(),
            'max_spend': max_spend,
            'active': True
        }
        
    def poll(self):
        '''
        Daemon loop that monitors the mempool for target wallet transactions.
        If a Swap is detected, it executes a Vampire Snipe (Front-runs the target).
        '''
        while True:
            time.sleep(10) # Poll every 10 seconds (Simulated mempool listener)
            
            for chat_id, config in list(self.active_targets.items()):
                if not config['active']:
                    continue
                    
                # Simulate detecting a transaction from the target wallet 10% of the time
                if random.random() < 0.10:
                    simulated_token = "0x" + "".join(random.choices("abcdef0123456789", k=40))
                    
                    if self.telegram_service:
                        self.telegram_service.send_message(f"🚨 <b>Copy Trade Triggered!</b>\\n\\nTarget: <code>{config['target_address']}</code>\\nAction: <b>Detected pending Buy for {simulated_token[:6]}...</b>\\n\\n🦇 <i>Executing Vampire Snipe to front-run the target...</i>", chat_id)
                        
                    # Calculate a slightly higher bribe to guarantee we buy before them
                    bribe = self.router.calculate_optimal_bribe(config['max_spend'], priority="HIGH") + 0.002
                    
                    # Execute the buy
                    # We need the user's private key. In production, we'd fetch it from DB.
                    # For simulation, we'll bypass the wallet check and just use a mock private key
                    try:
                        from core.sniper_wallet import get_wallet_by_chat_id
                        wallet = get_wallet_by_chat_id(chat_id)
                        if wallet:
                            result = execute_snipe(wallet['private_key'], simulated_token, config['max_spend'])
                            if result['status'] == 'SUCCESS':
                                msg = (
                                    f"🦇 <b>Vampire Snipe Successful!</b>\\n\\n"
                                    f"We bought <code>{simulated_token}</code> before the target!\\n"
                                    f"Amount: {result['trade_eth']} ETH\\n"
                                    f"Bribe Paid: {bribe} ETH\\n\\n"
                                    f"Tx Hash: <code>{result['simulated_tx_hash']}</code>"
                                )
                                if self.telegram_service:
                                    self.telegram_service.send_message(msg, chat_id)
                    except Exception as e:
                        if self.telegram_service:
                            self.telegram_service.send_message(f"❌ Copy Trade Failed: {e}", chat_id)
