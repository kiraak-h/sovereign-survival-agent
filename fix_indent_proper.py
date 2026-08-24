import sys
import re

with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = r"(if cmd_text\.startswith\(\"/start\"\):)(.*?)(elif cmd_text\.startswith\(\"/takeprofit\"\):)"

new_start = '''\\1
            referrer_id = None
            if " ref_" in cmd_text:
                referrer_id = cmd_text.split(" ref_")[-1]
            try:
                from core.sniper_wallet import get_or_create_wallet
                wallet = get_or_create_wallet(chat_id, referrer_id)
                address = wallet["address"]
            except Exception:
                address = "0xERROR"
                
            msg = (
                f"<b>Sovereign Sniper · Base L2</b> 🛡️\\n"
                f"<code>{address}</code> <i>(Tap to copy)</i>\\n"
                f"<b>Balance:</b> 0.000 ETH (.00)\\n"
                f"—\\n"
                f"Click on the Refresh button to update your current balance.\\n\\n"
                f"<b>Referral Link</b> | <a href='https://twitter.com/TheSovSniper'>X</a> | Terminal\\n"
                f"<code>https://t.me/SovereignSniperBot?start=ref_{chat_id}</code>"
            )
            
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🟢 Buy", "callback_data": "menu_buy"}, {"text": "🔴 Sell", "callback_data": "menu_sell"}],
                    [{"text": "📊 Positions", "callback_data": "menu_positions"}, {"text": "🎯 Limit Orders", "callback_data": "menu_limits"}, {"text": "🕒 DCA Orders", "callback_data": "menu_dca"}],
                    [{"text": "👥 Copy Trade", "callback_data": "menu_copy"}, {"text": "⚡ Sniper", "callback_data": "menu_snipe"}],
                    [{"text": "🔍 Scanner", "callback_data": "menu_scanner"}, {"text": "💰 Rewards", "callback_data": "menu_rewards"}, {"text": "⭐ Watchlist", "callback_data": "menu_watchlist"}],
                    [{"text": "📤 Withdraw", "callback_data": "menu_withdraw"}, {"text": "📥 Import Wallet", "callback_data": "menu_import"}, {"text": "⚙️ Settings", "callback_data": "menu_settings"}],
                    [{"text": "🕳️ Trenches", "callback_data": "menu_trenches"}, {"text": "❓ Help", "callback_data": "menu_help"}, {"text": "🔄 Refresh", "callback_data": "menu_refresh"}]
                ]
            }
            self.send_message(msg, chat_id, reply_markup=keyboard)
            
        \\3'''

content = re.sub(pattern, new_start, content, flags=re.DOTALL)

with open('core/telegram_bot_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Indentation properly rewritten!")
