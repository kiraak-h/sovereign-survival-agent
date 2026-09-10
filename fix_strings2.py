import os
import re

filepath = 'core/telegram_bot_service.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# I will just write a python script that replaces literal \n inside double quotes with \\n, or just rewrite the blocks.
# Let's replace the whole blocks that are broken.

bad_caption = '''caption = f"✅ <b>Sell Executed!</b>\n\nDumped {pct}% of <b>{token}</b>.\nTx: <code>{result['tx_hash']}</code>"'''
good_caption = 'caption = f"✅ <b>Sell Executed!</b>\\\\n\\\\nDumped {pct}% of <b>{token}</b>.\\\\nTx: <code>{result[\'tx_hash\']}</code>"'
content = content.replace(bad_caption, good_caption)

bad_copy1 = '''return self.send_message("🦇 <b>Vampire Copy Trading</b>\n\nYou have no active targets.\n\n<b>Add a target:</b>\n<code>/copy [ADDRESS] [MAX_SPEND_ETH]</code>", chat_id)'''
good_copy1 = 'return self.send_message("🦇 <b>Vampire Copy Trading</b>\\\\n\\\\nYou have no active targets.\\\\n\\\\n<b>Add a target:</b>\\\\n<code>/copy [ADDRESS] [MAX_SPEND_ETH]</code>", chat_id)'
content = content.replace(bad_copy1, good_copy1)

bad_copy2 = '''msg = "🦇 <b>Your Vampire Targets:</b>\n\n"'''
good_copy2 = 'msg = "🦇 <b>Your Vampire Targets:</b>\\\\n\\\\n"'
content = content.replace(bad_copy2, good_copy2)

bad_copy3 = '''msg += f"{idx+1}. <code>{addr}</code>\n   Spend: {t['max_spend_eth']} ETH | {status}\n\n"'''
good_copy3 = 'msg += f"{idx+1}. <code>{addr}</code>\\\\n   Spend: {t[\'max_spend_eth\']} ETH | {status}\\\\n\\\\n"'
content = content.replace(bad_copy3, good_copy3)

bad_copy4 = '''self.send_message(f"🦇 <b>Vampire Copy Trading Activated!</b>\n\nTarget: <code>{target}</code>\nMax Spend: {max_spend} ETH per trade\n\n<i>Monitoring mempool for target transactions...</i>", chat_id)'''
good_copy4 = 'self.send_message(f"🦇 <b>Vampire Copy Trading Activated!</b>\\\\n\\\\nTarget: <code>{target}</code>\\\\nMax Spend: {max_spend} ETH per trade\\\\n\\\\n<i>Monitoring mempool for target transactions...</i>", chat_id)'
content = content.replace(bad_copy4, good_copy4)

bad_ref1 = '''msg = (
            f"🤝 <b>Referral Dashboard</b>\n\n"
            f"Invite friends and earn 20% of their trading fees forever!\n\n"
            f"👥 <b>Total Invited:</b> {stats['count']}\n"
            f"💰 <b>Total Earned:</b> {stats['rewards']} ETH\n\n"
            f"<b>Your Link:</b>\n"
            f"<code>https://t.me/SovereignSniperBot?start=ref_{chat_id}</code>"
        )'''
good_ref1 = '''msg = (
            f"🤝 <b>Referral Dashboard</b>\\n\\n"
            f"Invite friends and earn 20% of their trading fees forever!\\n\\n"
            f"👥 <b>Total Invited:</b> {stats['count']}\\n"
            f"💰 <b>Total Earned:</b> {stats['rewards']} ETH\\n\\n"
            f"<b>Your Link:</b>\\n"
            f"<code>https://t.me/SovereignSniperBot?start=ref_{chat_id}</code>"
        )'''
content = content.replace(bad_ref1, good_ref1)

bad_mev1 = '''return self.send_message(f"🏎️ <b>MEV Bribe / Tip Config</b>\n\nCurrent Tip: <code>{current} ETH</code>\n\nHigher tips guarantee faster transactions.\n<b>Usage:</b> <code>/mev [ETH_AMOUNT]</code>\n<i>Example: /mev 0.01</i>", chat_id)'''
good_mev1 = 'return self.send_message(f"🏎️ <b>MEV Bribe / Tip Config</b>\\\\n\\\\nCurrent Tip: <code>{current} ETH</code>\\\\n\\\\nHigher tips guarantee faster transactions.\\\\n<b>Usage:</b> <code>/mev [ETH_AMOUNT]</code>\\\\n<i>Example: /mev 0.01</i>", chat_id)'
content = content.replace(bad_mev1, good_mev1)

bad_mev2 = '''self.send_message(f"✅ <b>MEV Bribe Updated!</b>\n\nEvery transaction will now include a {tip} ETH tip to the block builder.", chat_id)'''
good_mev2 = 'self.send_message(f"✅ <b>MEV Bribe Updated!</b>\\\\n\\\\nEvery transaction will now include a {tip} ETH tip to the block builder.", chat_id)'
content = content.replace(bad_mev2, good_mev2)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
