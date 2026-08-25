import threading
import time
import random

class MempoolSniper:
    def __init__(self, telegram_service=None):
        self.telegram_service = telegram_service
        # Format: {chat_id: {'active': True, 'max_spend': 0.05, 'min_liquidity': 1.0}}
        self.active_snipers = {}
        self._is_running = False
        
    def enable(self, chat_id: str, max_spend: float, min_liquidity_eth: float = 1.0):
        self.active_snipers[chat_id] = {
            'active': True,
            'max_spend': max_spend,
            'min_liquidity': min_liquidity_eth
        }
        
    def disable(self, chat_id: str):
        if chat_id in self.active_snipers:
            self.active_snipers[chat_id]['active'] = False
            
    def _simulate_new_pair_detection(self) -> dict | None:
        '''
        In production: Subscribes to wss:// Base node, listens for
        addLiquidityETH() calls on Uniswap V2/V3 Router.
        
        Returns the new pair data if a new LP is detected, None otherwise.
        Fires roughly every 45s-120s to simulate real on-chain activity.
        '''
        if random.random() < 0.03: # ~3% chance per poll cycle to detect a new pair
            token_address = "0x" + "".join(random.choices("abcdef0123456789", k=40))
            liquidity_eth = round(random.uniform(0.5, 20.0), 2)
            return {
                'token_address': token_address,
                'liquidity_eth': liquidity_eth,
                'pair_address': "0x" + "".join(random.choices("abcdef0123456789", k=40))
            }
        return None
        
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
                    f"🔫 <i>Firing Block-0 Snipe...</i>",
                    chat_id
                )
            self._execute_snipe(chat_id, token_address, config['max_spend'])
    def poll(self):
        '''Background daemon that watches the mempool for new liquidity pairs.'''
        self._is_running = True
        while self._is_running:
            time.sleep(5) # Poll every 5 seconds
            
            if not self.active_snipers:
                continue
                
            new_pair = self._simulate_new_pair_detection()
            if not new_pair:
                continue
                
            for chat_id, config in list(self.active_snipers.items()):
                if not config['active']:
                    continue
                    
                # Minimum liquidity filter - ignore micro rugs
                if new_pair['liquidity_eth'] < config['min_liquidity']:
                    if self.telegram_service:
                        self.telegram_service.send_message(
                            f"⚠️ <b>New Pair Detected - Skipped</b>\\n"
                            f"Token: <code>{new_pair['token_address'][:10]}...</code>\\n"
                            f"Liquidity: {new_pair['liquidity_eth']} ETH (below your {config['min_liquidity']} ETH minimum)",
                            chat_id
                        )
                    continue
                
                # Alert immediately before execution
                if self.telegram_service:
                    self.telegram_service.send_message(
                        f"🚀 <b>NEW PAIR DETECTED - SNIPING!</b>\\n\\n"
                        f"Token: <code>{new_pair['token_address']}</code>\\n"
                        f"Pair: <code>{new_pair['pair_address']}</code>\\n"
                        f"Liquidity: {new_pair['liquidity_eth']} ETH\\n\\n"
                        f"⚡ <i>Executing Block 0 snipe via Private MEV Router...</i>",
                        chat_id
                    )
                    
                try:
                    from core.sniper_wallet import get_wallet_by_chat_id
                    from core.evm_simulator import HoneypotSimulator
                    from core.dex_router import execute_snipe
                    
                    wallet = get_wallet_by_chat_id(chat_id)
                    if not wallet:
                        continue
                    
                    # Run honeypot check before sniping
                    sim = HoneypotSimulator()
                    sim_result = sim.simulate_trade_lifecycle(new_pair['token_address'], config['max_spend'])
                    
                    if sim_result['is_honeypot']:
                        if self.telegram_service:
                            self.telegram_service.send_message(
                                f"🚨 <b>SNIPE ABORTED - HONEYPOT!</b>\\n\\n"
                                f"Token: <code>{new_pair['token_address'][:10]}...</code>\\n"
                                f"<i>EVM Shield blocked the trade before any ETH was spent.</i>",
                                chat_id
                            )
                        continue
                    
                    result = execute_snipe(wallet['private_key'], new_pair['token_address'], config['max_spend'])
                    
                    if result['status'] == 'SUCCESS':
                        msg = (
                            f"🎯 <b>Block 0 Snipe Successful!</b>\\n\\n"
                            f"Token: <code>{new_pair['token_address']}</code>\\n"
                            f"Amount: {result['trade_eth']} ETH\\n"
                            f"Fee: {result['fee_eth']} ETH\\n"
                            f"👻 MEV: {result['builder']}\\n\\n"
                            f"Tx: <code>{result['simulated_tx_hash']}</code>"
                        )
                    else:
                        msg = f"❌ Block 0 Snipe Failed: {result['message']}"
                        
                    if self.telegram_service:
                        self.telegram_service.send_message(msg, chat_id)
                        
                except Exception as e:
                    if self.telegram_service:
                        self.telegram_service.send_message(f"❌ Sniper Error: {e}", chat_id)
