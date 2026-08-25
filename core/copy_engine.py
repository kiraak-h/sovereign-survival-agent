class CopyEngine:
    def __init__(self, telegram_service=None):
        self.telegram_service = telegram_service
        self.active_targets = {}
        
    def set_target(self, chat_id: str, target: str, max_spend: float):
        self.active_targets[chat_id] = {
            'target_address': target.lower(),
            'max_spend': max_spend,
            'active': True
        }
        
    def trigger_copy_trade(self, target_wallet: str, token_address: str, tx_hash: str):
        '''Called by the WSS streamer when a target wallet executes a swap.'''
        for chat_id, config in list(self.active_targets.items()):
            if not config['active']:
                continue
                
            if config['target_address'] == target_wallet.lower():
                if self.telegram_service:
                    self.telegram_service.send_message(
                        f"🦇 <b>Copy Trade Triggered!</b>\n\n"
                        f"Target: <code>{target_wallet}</code>\n"
                        f"Action: <b>Detected pending Buy for {token_address[:6]}...</b>\n\n"
                        f"⚡ <i>Executing Vampire Snipe to front-run the target...</i>", 
                        chat_id
                    )
                
                try:
                    from core.sniper_wallet import get_or_create_wallet
                    from core.dex_router import execute_snipe
                    
                    wallet = get_or_create_wallet(chat_id)
                    result = execute_snipe(wallet['private_key'], token_address, config['max_spend'])
                    
                    if result['status'] == 'SUCCESS':
                        msg = (
                            f"✅ <b>Vampire Snipe Successful!</b>\n\n"
                            f"We bought <code>{token_address}</code> before the target!\n"
                            f"Amount: {result['trade_eth']} ETH\n"
                            f"Tx Hash: <code>{result.get('tx_hash', result.get('simulated_tx_hash'))}</code>"
                        )
                        if self.telegram_service:
                            self.telegram_service.send_message(msg, chat_id)
                    else:
                        if self.telegram_service:
                            self.telegram_service.send_message(f"❌ Copy Trade Failed: {result.get('message')}", chat_id)
                except Exception as e:
                    if self.telegram_service:
                        self.telegram_service.send_message(f"❌ Copy Trade Error: {e}", chat_id)

    def poll(self):
        # We no longer poll or simulate. We rely on the WSS streamer to trigger_copy_trade.
        pass
