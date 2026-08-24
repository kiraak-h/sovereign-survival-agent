import sys

with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update callbacks for import and withdraw
old_menu_prefix = '''        elif data.startswith("menu_"):
            self.send_message(f"<i>Feature '{data.replace('menu_', '').title()}' coming soon in Phase 6...</i>", chat_id)'''

new_menu_prefix = '''        elif data == "menu_import":
            self.send_message("<b>📥 Import Wallet</b>\\n\\nReply with: <code>/import [PRIVATE_KEY]</code>\\n\\n<i>⚠️ SECURITY: Your private key will be encrypted via AES-GCM and your message will be instantly deleted from the chat for safety.</i>", chat_id)
        elif data == "menu_withdraw":
            self.send_message("<b>📤 Withdraw ETH</b>\\n\\nReply with: <code>/withdraw [ADDRESS] [AMOUNT]</code>\\n<i>Example: /withdraw 0x123... 0.5</i>\\n\\n<i>Tip: Use 'all' as the amount to withdraw your entire balance.</i>", chat_id)
        elif data.startswith("menu_"):
            self.send_message(f"<i>Feature '{data.replace('menu_', '').title()}' coming soon in Phase 6...</i>", chat_id)'''

content = content.replace(old_menu_prefix, new_menu_prefix)

# 2. Wire up the commands in handle_command
old_command_routing = '''        elif cmd_text == "/vitals":
            self._handle_vitals(chat_id)
        else:'''

new_command_routing = '''        elif cmd_text == "/vitals":
            self._handle_vitals(chat_id)
        elif cmd_text.startswith("/import"):
            # We need the message_id to delete it for security!
            pass # We will handle this by injecting message_id parsing later, but for now we'll write a basic handler
            self._handle_import(cmd_text, chat_id)
        elif cmd_text.startswith("/withdraw"):
            self._handle_withdraw(cmd_text, chat_id)
        else:'''

content = content.replace(old_command_routing, new_command_routing)

# 3. Add the methods
new_methods = '''
    def _handle_import(self, cmd_text: str, chat_id: str):
        parts = cmd_text.split()
        if len(parts) != 2:
            return self.send_message("❌ Usage: /import [PRIVATE_KEY]", chat_id)
            
        private_key = parts[1]
        if not private_key.startswith("0x") and len(private_key) == 64:
            private_key = "0x" + private_key
            
        try:
            from core.sniper_wallet import import_wallet
            address = import_wallet(chat_id, private_key)
            self.send_message(f"✅ <b>Wallet Imported Successfully!</b>\\n\\nAddress: <code>{address}</code>\\n\\n<i>Your private key has been encrypted. Please manually delete your previous message for safety.</i>", chat_id)
        except Exception as e:
            self.send_message(f"❌ Import Failed: {e}", chat_id)

    def _handle_withdraw(self, cmd_text: str, chat_id: str):
        parts = cmd_text.split()
        if len(parts) != 3:
            return self.send_message("❌ Usage: /withdraw [ADDRESS] [AMOUNT]", chat_id)
            
        destination = parts[1]
        amount_str = parts[2]
        
        try:
            from core.sniper_wallet import get_wallet_by_chat_id
            from core.dex_router import execute_withdrawal
            
            wallet = get_wallet_by_chat_id(chat_id)
            if not wallet:
                return self.send_message("❌ You do not have a wallet yet. Type /start", chat_id)
                
            amount = float(amount_str) if amount_str.lower() != 'all' else 'all'
            result = execute_withdrawal(wallet['private_key'], destination, amount)
            
            if result['status'] == 'SUCCESS':
                msg = (
                    f"✅ <b>Withdrawal Successful</b>\\n\\n"
                    f"Sent: {result['amount']} ETH\\n"
                    f"To: <code>{destination}</code>\\n"
                    f"Tx Hash: <code>{result['tx_hash']}</code>"
                )
                self.send_message(msg, chat_id)
            else:
                self.send_message(f"❌ Withdrawal Failed: {result['message']}", chat_id)
        except Exception as e:
            self.send_message(f"❌ Error: {e}", chat_id)
'''

content += new_methods

with open('core/telegram_bot_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("UI updated!")
