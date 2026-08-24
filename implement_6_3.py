import sys
import re

with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_buy = '''    def _handle_buy(self, cmd_text: str, chat_id: str):
        parts = cmd_text.split()
        if len(parts) != 3:
            return self.send_message("Usage: /buy [token_address] [eth_amount]", chat_id)
            
        token = parts[1]
        try:
            amount = float(parts[2])
        except ValueError:
            return self.send_message("Invalid ETH amount.", chat_id)
            
        self.send_message(f"🔍 *Scanning* {token} *for honeypots...*", chat_id)
        
        import time
        time.sleep(1)
        self.send_message("✅ *AST Clear. Zero mints detected. Routing trade...*", chat_id)
        
        try:
            from core.sniper_wallet import get_or_create_wallet
            from core.dex_router import execute_snipe
            wallet = get_or_create_wallet(chat_id)
            result = execute_snipe(wallet['private_key'], token, amount)
            
            if result['status'] == 'SUCCESS':
                msg = (
                    f"🎯 *Snipe Executed!*\n\n"
                    f"Token: {token}\n"
                    f"Amount: {result['trade_eth']} ETH\n"
                    f"Fee (1%): {result['fee_eth']} ETH\n\n"
                    f"Tx Hash: [{result['simulated_tx_hash']}](https://basescan.org/tx/{result['simulated_tx_hash']})"
                )
                self.send_message(msg, chat_id)
            else:
                self.send_message(f"❌ Trade Failed: {result['message']}", chat_id)
        except Exception as e:
            self.send_message(f"❌ Error: {e}", chat_id)'''

new_buy = '''    def _handle_buy(self, cmd_text: str, chat_id: str):
        parts = cmd_text.split()
        if len(parts) != 3:
            return self.send_message("❌ Usage: /buy [token_address] [eth_amount]", chat_id)
            
        token = parts[1]
        try:
            amount = float(parts[2])
        except ValueError:
            return self.send_message("❌ Invalid ETH amount.", chat_id)
            
        self.send_message(f"🛡️ <i>Spinning up local EVM fork to simulate trade lifecycle...</i>", chat_id)
        
        try:
            from core.evm_simulator import HoneypotSimulator
            simulator = HoneypotSimulator()
            sim_result = simulator.simulate_trade_lifecycle(token, amount)
            
            if sim_result['is_honeypot']:
                msg = (
                    f"🚨 <b>HONEYPOT DETECTED - TRADE BLOCKED</b> 🚨\\n\\n"
                    f"<b>Token:</b> <code>{token}</code>\\n"
                    f"<b>Reason:</b> {sim_result['reason']}\\n"
                    f"<b>Simulated Tax:</b> Buy: {sim_result['buy_tax']}% | Sell: {sim_result['sell_tax']}%\\n\\n"
                    f"<i>The Sovereign Shield has intercepted the transaction to protect your capital.</i>"
                )
                return self.send_message(msg, chat_id)
                
            # If safe, report the dynamic gas profiling
            msg = (
                f"✅ <b>EVM Simulation Passed</b>\\n"
                f"Buy Tax: {sim_result['buy_tax']}% | Sell Tax: {sim_result['sell_tax']}%\\n"
                f"Estimated Gas: {sim_result['gas_used']} Gwei\\n\\n"
                f"⚡ <i>Executing safe transaction...</i>"
            )
            self.send_message(msg, chat_id)
            
            from core.sniper_wallet import get_or_create_wallet
            from core.dex_router import execute_snipe
            wallet = get_or_create_wallet(chat_id)
            result = execute_snipe(wallet['private_key'], token, amount)
            
            if result['status'] == 'SUCCESS':
                msg = (
                    f"🎯 <b>Snipe Executed!</b>\\n\\n"
                    f"Token: <code>{token}</code>\\n"
                    f"Amount: {result['trade_eth']} ETH\\n"
                    f"Fee (1%): {result['fee_eth']} ETH\\n\\n"
                    f"Tx Hash: <code>{result['simulated_tx_hash']}</code>"
                )
                self.send_message(msg, chat_id)
            else:
                self.send_message(f"❌ Trade Failed: {result['message']}", chat_id)
        except Exception as e:
            self.send_message(f"❌ Error during EVM simulation: {e}", chat_id)'''

content = content.replace(old_buy, new_buy)

with open('core/telegram_bot_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("EVM Shield implemented in /buy!")
