class MempoolSniper:
    def __init__(self, telegram_service=None):
        self.telegram_service = telegram_service
        self.active_snipers = {}
        
    def enable(self, chat_id: str, max_spend: float, min_liquidity_eth: float = 1.0):
        self.active_snipers[chat_id] = {
            'active': True,
            'max_spend': max_spend,
            'min_liquidity': min_liquidity_eth
        }
        
    def disable(self, chat_id: str):
        if chat_id in self.active_snipers:
            self.active_snipers[chat_id]['active'] = False
            
    def trigger_snipe(self, token_address: str):
        '''Called directly by the Mempool WSS Streamer when an addLiquidity TX is detected.'''
        for chat_id, config in list(self.active_snipers.items()):
            if not config['active']:
                continue
                
            if self.telegram_service:
                self.telegram_service.send_message(
                    f"⚡ <b>LIQUIDITY ADDED in Mempool!</b>\n\n"
                    f"Token: <code>{token_address}</code>\n"
                    f"Action: <b>addLiquidityETH</b>\n\n"
                    f"🛡️ <i>Running GoPlus AST scan...</i>",
                    chat_id
                )
            
            try:
                from core.token_scanner import check_honeypot
                if not check_honeypot(token_address):
                    if self.telegram_service:
                        self.telegram_service.send_message(f"🚨 <b>HONEYPOT DETECTED</b> in {token_address}. Snipe aborted.", chat_id)
                    continue

                from core.sniper_wallet import get_or_create_wallet
                from core.dex_router import execute_snipe
                
                wallet = get_or_create_wallet(chat_id)
                result = execute_snipe(wallet['private_key'], token_address, config['max_spend'])
                
                if result['status'] == 'SUCCESS':
                    msg = (
                        f"✅ <b>Block 0 Snipe Successful!</b>\n\n"
                        f"Token: <code>{token_address}</code>\n"
                        f"Amount: {result['trade_eth']} ETH\n"
                        f"Fee: {result['fee_eth']} ETH\n"
                        f" Tx Hash: <code>{result.get('tx_hash', result.get('simulated_tx_hash'))}</code>"
                    )
                else:
                    msg = f"❌ Block 0 Snipe Failed: {result.get('message', 'Unknown Error')}"
                    
                if self.telegram_service:
                    self.telegram_service.send_message(msg, chat_id)
                    
            except Exception as e:
                if self.telegram_service:
                    self.telegram_service.send_message(f"❌ Sniper Error: {e}", chat_id)

    def poll(self):
        # We no longer poll or simulate. We rely on the WSS streamer to trigger_snipe.
        pass
