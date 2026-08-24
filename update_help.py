import sys
import re

with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add handle_callback_query method right before handle_command
callback_method = '''
    def handle_callback_query(self, callback_query: Dict[str, Any]):
        cq_id = callback_query.get("id")
        data = callback_query.get("data")
        message = callback_query.get("message", {})
        chat_id = str(message.get("chat", {}).get("id"))
        
        # Acknowledge the callback immediately
        requests.post(f"https://api.telegram.org/bot{self.token}/answerCallbackQuery", json={"callback_query_id": cq_id})
        
        if data == "menu_help":
            self.handle_command("/help", chat_id)
        elif data == "menu_back":
            self.handle_command("/start", chat_id)
        elif data == "menu_refresh":
            self.handle_command("/start", chat_id)
        else:
            self.send_message(f"<i>Feature '{data}' coming soon in Phase 6...</i>", chat_id)

    def handle_command'''
    
if "def handle_callback_query" not in content:
    content = content.replace("    def handle_command", callback_method)

# 2. Update the /start keyboard to include Import Wallet and Trenches
pattern_start = r"(keyboard = \{\n\s*\"inline_keyboard\": \[).*?(\]\n\s*\})"
new_keyboard = '''\\1
                [{"text": "🟢 Buy", "callback_data": "menu_buy"}, {"text": "🔴 Sell", "callback_data": "menu_sell"}],
                [{"text": "📊 Positions", "callback_data": "menu_positions"}, {"text": "🎯 Limit Orders", "callback_data": "menu_limits"}, {"text": "🕒 DCA Orders", "callback_data": "menu_dca"}],
                [{"text": "👥 Copy Trade", "callback_data": "menu_copy"}, {"text": "⚡ Sniper", "callback_data": "menu_snipe"}],
                [{"text": "🔍 Scanner", "callback_data": "menu_scanner"}, {"text": "💰 Rewards", "callback_data": "menu_rewards"}, {"text": "⭐ Watchlist", "callback_data": "menu_watchlist"}],
                [{"text": "📤 Withdraw", "callback_data": "menu_withdraw"}, {"text": "📥 Import Wallet", "callback_data": "menu_import"}, {"text": "⚙️ Settings", "callback_data": "menu_settings"}],
                [{"text": "🕳️ Trenches", "callback_data": "menu_trenches"}, {"text": "❓ Help", "callback_data": "menu_help"}, {"text": "🔄 Refresh", "callback_data": "menu_refresh"}]
            \\2'''
content = re.sub(pattern_start, new_keyboard, content, flags=re.DOTALL)

# 3. Update the /help command to match the screenshot perfectly
pattern_help = r"(elif cmd_text == \"/help\":\n\s*msg = \(\n).*?(\n\s*\)\n\s*self\.send_message\(msg, chat_id\))"

new_help = '''\\1                "<b><u>How do I use Sovereign Sniper?</u></b>\\n"
                "Check out our <a href='https://youtube.com'>YouTube playlist</a> where we explain it all and join our support chat for additional resources @SovereignSniper.\\n\\n"
                "<b><u>Where can I find my referral code?</u></b>\\n"
                "Open the /start menu and click 💰 Rewards.\\n\\n"
                "<b><u>What are the fees for using Sovereign?</u></b>\\n"
                "Successful transactions through Sovereign incur a fee of 1.0%, if you were referred by another user (who gets 20% of that). We don't charge a subscription fee or pay-wall any features.\\n\\n"
                "<b><u>Security Tips: How can I protect my account from scammers?</u></b>\\n"
                "- Safeguard does <b>NOT</b> require you to login with a phone number or QR code!\\n"
                "- NEVER search for bots in telegram. Use only official links.\\n"
                "- Admins and Mods NEVER dm first or send links, stay safe!\\n\\n"
                "<b><u>Trading Tips: Common Failure Reasons</u></b>\\n"
                "- Slippage Exceeded: Up your slippage or sell in smaller increments.\\n"
                "- Insufficient balance for buy amount + gas: Add ETH or reduce your tx amount.\\n"
                "- Timed out: Can occur with heavy network loads, consider increasing your gas tip.\\n\\n"
                "<b><u>My PNL seems wrong, why is that?</u></b>\\n"
                "The net profit of a trade takes into consideration the trade's transaction fees. Confirm your gas tip settings and ensure your settings align with your trading size.\\n\\n"
                "<b><u>Additional questions or need support?</u></b>\\n"
                "Join our Telegram group @SovereignSniper and one of our admins can assist you."\\2'''

# Add the back button markup to the help send_message call
new_help = new_help.replace("self.send_message(msg, chat_id)", "self.send_message(msg, chat_id, reply_markup={'inline_keyboard': [[{'text': '← Back', 'callback_data': 'menu_back'}]]})")

content = re.sub(pattern_help, new_help, content, flags=re.DOTALL)

with open('core/telegram_bot_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated successfully!")
