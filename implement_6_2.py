import sys
import re

with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update menu_positions routing
content = content.replace(
    'elif data.startswith("menu_"):',
    '''elif data == "menu_positions":
            self.handle_command("/positions", chat_id)
        elif data.startswith("sell_"):
            parts = data.split("_")
            pct = int(parts[1])
            token = parts[2]
            self._handle_1click_sell(chat_id, token, pct)
        elif data.startswith("menu_"):'''
)

# 2. Update command routing for /positions
content = content.replace(
    'elif cmd_text.startswith("/import"):',
    '''elif cmd_text == "/positions":
            self._handle_positions(chat_id)
        elif cmd_text.startswith("/import"):'''
)

# 3. Add the methods
new_methods = '''
    def _handle_positions(self, chat_id: str):
        try:
            from core.sniper_wallet import get_wallet_by_chat_id
            from core.dex_router import get_portfolio_positions
            
            wallet = get_wallet_by_chat_id(chat_id)
            if not wallet:
                return self.send_message("❌ You do not have a wallet yet. Type /start", chat_id)
                
            self.send_message("🔍 <i>Scanning Base network for your assets... (Filtering dust <.00)</i>", chat_id)
            
            positions = get_portfolio_positions(wallet['address'])
            if not positions:
                return self.send_message("📊 <b>Positions</b>\\n\\nYour wallet is currently empty.", chat_id)
                
            for pos in positions:
                emoji = "🟩" if pos['pnl_pct'] >= 0 else "🟥"
                msg = (
                    f"<b>{pos['symbol']}</b>\\n"
                    f"<code>{pos['address']}</code>\\n"
                    f"<b>Value:</b>  | <b>PnL:</b> {emoji} {pos['pnl_pct']}%"
                )
                
                keyboard = {
                    "inline_keyboard": [
                        [
                            {"text": "Sell 25%", "callback_data": f"sell_25_{pos['symbol']}"},
                            {"text": "Sell 50%", "callback_data": f"sell_50_{pos['symbol']}"},
                            {"text": "Sell 100%", "callback_data": f"sell_100_{pos['symbol']}"}
                        ]
                    ]
                }
                self.send_message(msg, chat_id, reply_markup=keyboard)
                
        except Exception as e:
            self.send_message(f"❌ Error fetching positions: {e}", chat_id)

    def _handle_1click_sell(self, chat_id: str, token: str, pct: int):
        try:
            from core.sniper_wallet import get_wallet_by_chat_id
            from core.dex_router import execute_partial_sell
            
            wallet = get_wallet_by_chat_id(chat_id)
            if not wallet:
                return
                
            self.send_message(f"⚡ <i>Executing {pct}% Sell for {token}...</i>", chat_id)
            result = execute_partial_sell(wallet['private_key'], token, pct)
            
            if result['status'] == 'SUCCESS':
                self.send_message(f"✅ <b>Sell Executed!</b>\\n\\nDumped {pct}% of <b>{token}</b>.\\nTx: <code>{result['tx_hash']}</code>", chat_id)
            else:
                self.send_message(f"❌ Sell Failed: {result['message']}", chat_id)
        except Exception as e:
            self.send_message(f"❌ Error: {e}", chat_id)
'''

content += new_methods

with open('core/telegram_bot_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("UI updated!")
