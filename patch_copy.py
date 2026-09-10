import os

filepath = 'core/copy_engine.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

new_logic = '''
    def load_targets_from_db(self):
        try:
            from core.sniper_wallet import get_all_active_copy_targets
            targets = get_all_active_copy_targets()
            self.active_targets.clear()
            for t in targets:
                chat_id = t['chat_id']
                if chat_id not in self.active_targets:
                    self.active_targets[chat_id] = []
                self.active_targets[chat_id].append({
                    'target_address': t['target_address'].lower(),
                    'max_spend': t['max_spend_eth'],
                    'active': bool(t['is_active'])
                })
        except Exception:
            pass

    def set_target(self, chat_id: str, target: str, max_spend: float):
        self.load_targets_from_db()
        
    def trigger_copy_trade(self, target_wallet: str, token_address: str, tx_hash: str):
        '''Called by the WSS streamer when a target wallet executes a swap.'''
        for chat_id, configs in list(self.active_targets.items()):
            for config in configs:
                if not config['active']:
                    continue
                    
                if config['target_address'] == target_wallet.lower():
                    if self.telegram_service:
                        self.telegram_service.send_message(
                            f"🦇 <b>Copy Trade Triggered!</b>\\n\\n"
                            f"Target: <code>{target_wallet}</code>\\n"
                            f"Action: <b>Detected pending Buy for {token_address[:6]}...</b>\\n\\n"
                            f"⚡ <i>Executing Vampire Snipe to front-run the target...</i>", 
                            chat_id
                        )
                    
                    try:
                        from core.sniper_wallet import get_or_create_wallet, get_mev_tip
                        from core.dex_router import execute_snipe
                        
                        wallet = get_or_create_wallet(chat_id)
                        mev_tip = get_mev_tip(chat_id)
                        result = execute_snipe(wallet['private_key'], token_address, config['max_spend'], mev_tip_eth=mev_tip)
                        
                        if result['status'] == 'SUCCESS':
                            msg = (
                                f"✅ <b>Vampire Snipe Successful!</b>\\n\\n"
                                f"We bought <code>{token_address}</code> before the target!\\n"
                                f"Amount: {result['trade_eth']} ETH\\n"
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
'''

content = content.replace(
'''    def set_target(self, chat_id: str, target: str, max_spend: float):
        self.active_targets[chat_id] = {
            'target_address': target.lower(),
            'max_spend': max_spend,
            'active': True
        }
        
    def trigger_copy_trade(self, target_wallet: str, token_address: str, tx_hash: str):
        \'\'\'Called by the WSS streamer when a target wallet executes a swap.\'\'\'
        for chat_id, config in list(self.active_targets.items()):
            if not config['active']:
                continue
                
            if config['target_address'] == target_wallet.lower():
                if self.telegram_service:
                    self.telegram_service.send_message(
                        f"?? <b>Copy Trade Triggered!</b>\\n\\n"
                        f"Target: <code>{target_wallet}</code>\\n"
                        f"Action: <b>Detected pending Buy for {token_address[:6]}...</b>\\n\\n"
                        f"? <i>Executing Vampire Snipe to front-run the target...</i>", 
                        chat_id
                    )
                
                try:
                    from core.sniper_wallet import get_or_create_wallet
                    from core.dex_router import execute_snipe
                    
                    wallet = get_or_create_wallet(chat_id)
                    result = execute_snipe(wallet['private_key'], token_address, config['max_spend'])
                    
                    if result['status'] == 'SUCCESS':
                        msg = (
                            f"? <b>Vampire Snipe Successful!</b>\\n\\n"
                            f"We bought <code>{token_address}</code> before the target!\\n"
                            f"Amount: {result['trade_eth']} ETH\\n"
                            f"Tx Hash: <code>{result.get('tx_hash', result.get('simulated_tx_hash'))}</code>"
                        )
                        if self.telegram_service:
                            self.telegram_service.send_message(msg, chat_id)
                    else:
                        if self.telegram_service:
                            self.telegram_service.send_message(f"? Copy Trade Failed: {result.get('message')}", chat_id)
                except Exception as e:
                    if self.telegram_service:
                        self.telegram_service.send_message(f"? Copy Trade Error: {e}", chat_id)''', new_logic.strip())

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
