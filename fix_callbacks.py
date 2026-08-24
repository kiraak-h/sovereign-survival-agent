import sys
import re

with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove the duplicate handle_callback_query I injected earlier
pattern_remove = r"    def handle_callback_query.*?def handle_command"
content = re.sub(pattern_remove, "    def handle_command", content, flags=re.DOTALL)

# 2. Update _handle_callback_query to handle menu clicks
pattern_update = r"(if data\.startswith\(\"solve_idx_\"\):)"
new_routing = '''if data == "menu_help":
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
        
content = content.replace('if data.startswith("solve_idx_"):', new_routing)

with open('core/telegram_bot_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Routing updated successfully!")
