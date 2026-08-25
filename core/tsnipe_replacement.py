        elif data.startswith("tsnipe_"):
            token_addr = data.replace("tsnipe_", "")
            self.send_message(f"⚡ <b>1-CLICK SNIPE INITIATED</b>\n\nToken: <code>{token_addr}</code>\nAmount: 0.05 ETH\n\n<i>Executing via Private MEV Router...</i>", chat_id)
            
            try:
                from core.sniper_wallet import get_or_create_wallet
                from core.dex_router import execute_snipe
                
                wallet = get_or_create_wallet(chat_id)
                result = execute_snipe(wallet['private_key'], token_addr, 0.05)
                
                if result['status'] == 'SUCCESS':
                    msg = (
                        f"✅ <b>Snipe Successful!</b>\n\n"
                        f"Amount: {result['trade_eth']:.4f} ETH\n"
                        f"Fee: {result.get('fee_eth', 0.0):.5f} ETH\n\n"
                        f"Tx Hash: [{result.get('tx_hash', 'Unknown')}](https://basescan.org/tx/{result.get('tx_hash', '')})"
                    )
                    self.send_message(msg, chat_id)
                else:
                    self.send_message(f"❌ Snipe Failed: {result.get('message', 'Unknown Error')}", chat_id)
            except Exception as e:
                self.send_message(f"❌ Execution Error: {e}", chat_id)
