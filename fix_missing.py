import sys

with open('old_bot.py', 'r', encoding='utf-8') as f:
    old_lines = f.readlines()

for i, line in enumerate(old_lines):
    if line.startswith('    def _handle_direct_solidity_audit'):
        start_idx = i
        break

missing_block = "".join(old_lines[start_idx:])

# Inject the menu handlers into _handle_callback_query
old_callback_start = '        if data.startswith("solve_idx_"):'
new_callback_start = '''        if data == "menu_help":
            self.handle_command("/help", chat_id)
        elif data == "menu_back":
            self.handle_command("/start", chat_id)
        elif data == "menu_refresh":
            self.handle_command("/start", chat_id)
        elif data == "menu_limits":
            self.send_message("<b>🎯 Limit Orders</b>\\n\\nReply with: <code>/takeprofit [TOKEN] [PERCENTAGE]</code>\\n<i>Example: /takeprofit PEPE 50</i>", chat_id)
        elif data.startswith("menu_"):
            self.send_message(f"<i>Feature '{data.replace('menu_', '').title()}' coming soon in Phase 6...</i>", chat_id)
        elif data.startswith("solve_idx_"):'''

missing_block = missing_block.replace(old_callback_start, new_callback_start)

with open('core/telegram_bot_service.py', 'a', encoding='utf-8') as f:
    f.write("\n" + missing_block)
