class AntiRugEngine:
    def __init__(self, telegram_service=None):
        self.active_guards = {}
        self.telegram_service = telegram_service

    def enable(self, chat_id: str):
        self.active_guards[chat_id] = {'active': True}

    def disable(self, chat_id: str):
        self.active_guards.pop(chat_id, None)

    def trigger_rug_evasion(self, token_address: str):
        '''Called directly by the Mempool WSS Streamer when a removeLiquidity TX is detected.'''
        for chat_id, config in list(self.active_guards.items()):
            if not config['active']:
                continue
                
            if self.telegram_service:
                self.telegram_service.send_message(
                    f"🛡️ <b>RUGPULL DETECTED in Mempool!</b>\n\n"
                    f"Token: <code>{token_address}</code>\n"
                    f"Malicious Action: <b>removeLiquidityETH</b>\n\n"
                    f"⚡ <i>Executing emergency 100% sell...</i>",
                    chat_id
                )
            self._execute_emergency_sell(chat_id, token_address)

    def _execute_emergency_sell(self, chat_id: str, token: str) -> dict:
        '''Executes a REAL 100% sell of the token to exit before the rug TX is confirmed.'''
        try:
            from core.sniper_wallet import get_or_create_wallet
            from core.dex_router import execute_partial_sell
            
            wallet = get_or_create_wallet(chat_id)
            if not wallet:
                return {'status': 'ERROR'}
                
            # Sell 100% of the bag
            result = execute_partial_sell(wallet['private_key'], token, 100)
            
            if result['status'] == 'SUCCESS':
                if self.telegram_service:
                    self.telegram_service.send_message(
                        f"✅ <b>EMERGENCY SELL SUCCESSFUL!</b>\n\n"
                        f"Dumped 100% of <code>{token}</code>.\n"
                        f"Tx: <code>{result.get('tx_hash')}</code>",
                        chat_id
                    )
            else:
                if self.telegram_service:
                    self.telegram_service.send_message(f"❌ Emergency Sell Failed: {result.get('message')}", chat_id)
            return result
        except Exception as e:
            return {'status': 'ERROR', 'message': str(e)}

    def poll(self):
        # We no longer poll or simulate. We rely on the WSS streamer to trigger_rug_evasion.
        pass
