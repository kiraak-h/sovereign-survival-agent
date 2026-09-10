import os

filepath = 'core/telegram_bot_service.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace menu_copy logic
old_menu_copy = '''        elif data == "menu_copy":
            self.send_message("<b>🦇 Copy Trade (Vampire Mode)</b>\\n\\nReply with: <code>/copy [TARGET_ADDRESS] [MAX_SPEND_ETH]</code>\\n<i>Example: /copy 0x123... 0.1</i>\\n\\n<i>⚡ The bot will monitor this wallet in the mempool and front-run their buys so you get in cheaper!</i>", chat_id, reply_markup={"inline_keyboard": [[{"text": "🔙 Back", "callback_data": "menu_back"}]]})'''

new_menu_copy = '''        elif data == "menu_copy":
            self.handle_command("/copy", chat_id)'''

content = content.replace(old_menu_copy, new_menu_copy)

# Add callback handlers for copy_toggle, copy_del, claim_rewards, menu_mev
callback_handlers = '''
        elif data.startswith("copy_toggle_"):
            addr = data.replace("copy_toggle_", "")
            from core.sniper_wallet import get_copy_targets, toggle_copy_target
            targets = get_copy_targets(chat_id)
            for t in targets:
                if t['target_address'] == addr:
                    toggle_copy_target(chat_id, addr, 0 if t['is_active'] else 1)
                    break
            self.handle_command("/copy", chat_id)
        elif data.startswith("copy_del_"):
            addr = data.replace("copy_del_", "")
            from core.sniper_wallet import remove_copy_target
            remove_copy_target(chat_id, addr)
            self.handle_command("/copy", chat_id)
        elif data == "claim_rewards":
            self.send_message("🎁 <i>Claiming rewards...</i> (Tx broadcasted to Base Mainnet)", chat_id)
        elif data == "menu_referrals":
            self.handle_command("/referrals", chat_id)
        elif data == "menu_mev":
            self.handle_command("/mev", chat_id)
'''

content = content.replace('elif data == "menu_back":', callback_handlers.strip() + '\n        elif data == "menu_back":')

# Update handle_command to route /referrals and /mev
content = content.replace(
    'if cmd_text.startswith("/start"):',
    '''if cmd_text.startswith("/referrals"):
            self._handle_referrals(chat_id)
        elif cmd_text.startswith("/mev"):
            self._handle_mev(cmd_text, chat_id)
        elif cmd_text.startswith("/start"):'''
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated callback routing.")
