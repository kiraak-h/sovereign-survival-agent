        elif data.startswith("tsnipe_"):
            token_addr = data.replace("tsnipe_", "")
            self.send_message(f"⚡ <b>1-CLICK SNIPE INITIATED</b>\n\nToken: <code>{token_addr}</code>\nAmount: 0.02 ETH\n\n<i>Executing via Private MEV Router...</i>", chat_id)
            
            try:
                from core.sniper_wallet import get_or_create_wallet, create_limit_order
                from core.dex_router import execute_snipe
                
                wallet = get_or_create_wallet(chat_id)
                result = execute_snipe(wallet['private_key'], token_addr, 0.02)
                
                if result['status'] == 'SUCCESS':
                    # Automatically set +100% TP and -30% SL for maximum safety!
                    try:
                        create_limit_order(chat_id, token_addr, 100.0)
                        create_limit_order(chat_id, token_addr, -30.0)
                        limit_msg = "\n\n🛡️ <b>Auto-Protection Enabled:</b>\n✅ Take-Profit set at +100%\n⛔ Stop-Loss set at -30%"
                    except Exception as e:
                        limit_msg = f"\n\n⚠️ Could not set auto-limits: {e}"

                    msg = (
                        f"✅ <b>Snipe Successful!</b>\n\n"
                        f"Amount: {result['trade_eth']:.4f} ETH\n"
                        f"Fee: {result.get('fee_eth', 0.0):.5f} ETH\n\n"
                        f"Tx Hash: [{result.get('tx_hash', 'Unknown')}](https://basescan.org/tx/{result.get('tx_hash', '')})"
                        f"{limit_msg}"
                    )
                    self.send_message(msg, chat_id)
                else:
                    self.send_message(f"❌ Snipe Failed: {result.get('message', 'Unknown Error')}", chat_id)
            except Exception as e:
                self.send_message(f"❌ Execution Error: {e}", chat_id)
