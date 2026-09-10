import os
import re

filepath = 'core/telegram_bot_service.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix menu_rewards to point to menu_referrals
content = content.replace(
    'elif data == "menu_rewards":\n            self.handle_command("/rewards", chat_id)',
    'elif data == "menu_rewards":\n            self.handle_command("/referrals", chat_id)'
)

# Add MEV tip button to Settings menu
old_settings = '''                    "inline_keyboard": [
                        [{"text": "🛡️ Anti-Rug ON", "callback_data": "cmd_antrug_on"}, {"text": "🛡️ Anti-Rug OFF", "callback_data": "cmd_antrug_off"}],
                        [{"text": "⚡ Sniper ON", "callback_data": "cmd_snipe_on"}, {"text": "⚡ Sniper OFF", "callback_data": "cmd_snipe_off"}],
                        [{"text": "🕵️‍♂️ Trenches ON", "callback_data": "cmd_trenches_on"}, {"text": "🕵️‍♂️ Trenches OFF", "callback_data": "cmd_trenches_off"}],
                        [{"text": "🔙 Back", "callback_data": "menu_back"}]
                    ]'''
new_settings = '''                    "inline_keyboard": [
                        [{"text": "🛡️ Anti-Rug ON", "callback_data": "cmd_antrug_on"}, {"text": "🛡️ Anti-Rug OFF", "callback_data": "cmd_antrug_off"}],
                        [{"text": "⚡ Sniper ON", "callback_data": "cmd_snipe_on"}, {"text": "⚡ Sniper OFF", "callback_data": "cmd_snipe_off"}],
                        [{"text": "🕵️‍♂️ Trenches ON", "callback_data": "cmd_trenches_on"}, {"text": "🕵️‍♂️ Trenches OFF", "callback_data": "cmd_trenches_off"}],
                        [{"text": "🏎️ Config MEV Tip", "callback_data": "menu_mev"}],
                        [{"text": "🔙 Back", "callback_data": "menu_back"}]
                    ]'''
content = content.replace(old_settings, new_settings)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated settings keyboard and rewards route.")
