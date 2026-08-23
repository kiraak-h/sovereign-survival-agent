import re

with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

status_func = """
    def _handle_status(self, chat_id: str):
        import sqlite3
        total_web2_usdc = 0.0
        total_web3_usdc = 0.0
        pending_count = 0
        
        try:
            with sqlite3.connect("treasury_ledger.db") as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT SUM(credits_usdc) FROM api_keys")
                row = cursor.fetchone()
                if row[0]: total_web2_usdc = row[0]
                
                cursor.execute("SELECT status, COUNT(*), SUM(amount_usdc) FROM unclaimed_permits GROUP BY status")
                for row in cursor.fetchall():
                    if row['status'] == 'SETTLED':
                        total_web3_usdc += (row[2] or 0.0)
                    elif row['status'] == 'PENDING':
                        pending_count += row[1]
                        
            msg = (
                f"🤖 *Sovereign Agent Status*\\n\\n"
                f"💰 *Total Revenue:* ${total_web2_usdc + total_web3_usdc:.2f} USDC\\n"
                f"├ Web2 API Keys: ${total_web2_usdc:.2f}\\n"
                f"└ Web3 M2M: ${total_web3_usdc:.2f}\\n\\n"
                f"🧹 *Pending Sweeps:* {pending_count} un-cashed EIP-2612 permits\\n"
                f"🟢 *Daemon:* UNSTOPPABLE 24/7"
            )
            self.send_message(chat_id, msg)
        except Exception as e:
            self.send_message(chat_id, f"Error fetching status: {e}")
"""

handle_command_func = """
    def handle_command(self, cmd_text: str, chat_id: str):
        if cmd_text == "/start" or cmd_text == "/help":
            msg = (
                "🛡️ *Sovereign Admin Bot*\\n\\n"
                "/status - View live revenue and sweeping metrics\\n"
                "/sweep - Force the on-chain settlement sweeper to run\\n\\n"
                "You can also paste a Solidity contract directly into this chat for an instant AST audit."
            )
            self.send_message(chat_id, msg)
        elif cmd_text == "/status":
            self._handle_status(chat_id)
        elif cmd_text == "/sweep":
            self._execute_sweep(chat_id)
        else:
            self.send_message(chat_id, "Unknown command. Try /help")
"""

sweep_func = """
    def _execute_sweep(self, chat_id: str):
        self.send_message(chat_id, "🧹 *Initiating On-Chain Sweep...*")
        try:
            from scripts.sweep_permits import sweep_pending_permits
            import io
            import sys
            
            old_stdout = sys.stdout
            sys.stdout = my_stdout = io.StringIO()
            sweep_pending_permits()
            sys.stdout = old_stdout
            
            output = my_stdout.getvalue()
            if not output.strip():
                output = "No pending permits found."
                
            self.send_message(chat_id, f"✅ *Sweep Complete*\\n```text\\n{output[:4000]}\\n```")
        except Exception as e:
            self.send_message(chat_id, f"❌ *Sweep Failed*\\n{e}")
"""

content = re.sub(r'\s*def _handle_swarm_status\(self, chat_id: str\):.*?(?=\s*def _execute_delegate)', '\n' + status_func, content, flags=re.DOTALL)
content = re.sub(r'\s*def handle_command\(self, cmd_text: str, chat_id: str\):.*?(?=\s*def _handle_status|\s*def _handle_swarm_status)', '\n' + handle_command_func, content, flags=re.DOTALL)
content = re.sub(r'\s*def _execute_delegate\(self, target_url: str, chat_id: str\):.*?(?=\s*def _handle_direct_solidity_audit)', '\n' + sweep_func, content, flags=re.DOTALL)

with open('core/telegram_bot_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")
