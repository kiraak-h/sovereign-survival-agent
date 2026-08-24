import sys

with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_msg = '''            if result['status'] == 'SUCCESS':
                msg = (
                    f"🎯 <b>Snipe Executed!</b>\\n\\n"
                    f"Token: <code>{token}</code>\\n"
                    f"Amount: {result['trade_eth']} ETH\\n"
                    f"Fee (1%): {result['fee_eth']} ETH\\n\\n"
                    f"Tx Hash: <code>{result['simulated_tx_hash']}</code>"
                )
                self.send_message(msg, chat_id)'''

new_msg = '''            if result['status'] == 'SUCCESS':
                msg = (
                    f"🎯 <b>Snipe Executed!</b>\\n\\n"
                    f"Token: <code>{token}</code>\\n"
                    f"Amount: {result['trade_eth']} ETH\\n"
                    f"Fee (1%): {result['fee_eth']} ETH\\n\\n"
                    f"👻 <b>MEV Protection:</b> Active\\n"
                    f"🧱 <b>Builder:</b> {result['builder']}\\n"
                    f"💰 <b>Bribe Paid:</b> {result['mev_bribe_eth']} ETH\\n\\n"
                    f"Tx Hash: <code>{result['simulated_tx_hash']}</code>"
                )
                self.send_message(msg, chat_id)'''

content = content.replace(old_msg, new_msg)

with open('core/telegram_bot_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("telegram_bot_service updated for MEV UI")
