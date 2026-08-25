import sys

with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Update /help command to include ALL commands in organized sections
old_help = '''        elif cmd_text == "/help":
            msg = (
                "<b><u>How do I use Sovereign Sniper?</u></b>
"
                "Check out our <a href='https://youtube.com'>YouTube playlist</a> where we explain it all and join our support chat for additional resources @SovereignSniper.

"
                "<b><u>Where can I find my referral code?</u></b>
"
                "Open the /start menu and click 💰 Rewards.

"
                "<b><u>What are the fees for using Sovereign?</u></b>
"
                "Successful transactions through Sovereign incur a fee of 1.0%, if you were referred by another user (who gets 20% of that). We don't charge a subscription fee or pay-wall any features.

"
                "<b><u>Security Tips: How can I protect my account from scammers?</u></b>
"
                "- Safeguard does <b>NOT</b> require you to login with a phone number or QR code!
"
                "- NEVER search for bots in telegram. Use only official links.
"
                "- Admins and Mods NEVER dm first or send links, stay safe!

"
                "<b><u>Trading Tips: Common Failure Reasons</u></b>
"
                "- Slippage Exceeded: Up your slippage or sell in smaller increments.
"
                "- Insufficient balance for buy amount + gas: Add ETH or reduce your tx amount.
"
                "- Timed out: Can occur with heavy network loads, consider increasing your gas tip.

"
                "<b><u>My PNL seems wrong, why is that?</u></b>
"
                "The net profit of a trade takes into consideration the trade's transaction fees. Confirm your gas tip settings and ensure your settings align with your trading size.

"
                "<b><u>Additional questions or need support?</u></b>
"
                "Join our Telegram group @SovereignSniper and one of our admins can assist you."
            )
            self.send_message(msg, chat_id)'''

new_help = '''        elif cmd_text == "/help":
            msg = (
                "<b>🛡️ Sovereign Sniper — Command Reference</b>\\n\\n"
                "<b>━━━ 👛 WALLET ━━━</b>\\n"
                "/start — Open main menu\\n"
                "/wallet — View address &amp; balance\\n"
                "/import [PK] — Import existing wallet (auto-deletes for OPSEC)\\n"
                "/withdraw [ADDR] [ETH] — Send ETH to any address\\n\\n"
                "<b>━━━ 📈 TRADING ━━━</b>\\n"
                "/buy [TOKEN] [ETH] — Buy a token (EVM Shield active)\\n"
                "/positions — Portfolio with 1-click sell\\n"
                "/scan [TOKEN] — Full intelligence report\\n"
                "/takeprofit [TOKEN] [PCT] — Set take-profit limit\\n\\n"
                "<b>━━━ 🤖 AUTOMATION ━━━</b>\\n"
                "/dca [TOKEN] [ETH] [MINS] — Recurring auto-buy\\n"
                "/dcaoff [TOKEN] — Cancel DCA order\\n"
                "/snipe on [ETH] [MIN_LIQ] — Block-0 pair sniper\\n"
                "/snipe off — Disable sniper\\n"
                "/copy [WALLET] [MAX_ETH] — Copy trade a wallet\\n"
                "/antrug on/off — Rugpull protection shield\\n"
                "/trenches on [ETH] [MCAP] — Micro-cap degen mode\\n\\n"
                "<b>━━━ 🔔 MONITORING ━━━</b>\\n"
                "/watch [TOKEN] [PRICE] [above/below] — Price alert\\n"
                "/watchlist — View active alerts\\n"
                "/history — Last 10 trades\\n\\n"
                "<b>━━━ 💰 SOCIAL ━━━</b>\\n"
                "/rewards — Referral dashboard\\n"
                "/refer — Get invite link\\n"
                "/pnl [TOKEN] [PCT] — Generate PnL flex card\\n\\n"
                "<b>━━━ ⚙️ FEES ━━━</b>\\n"
                "1% per trade. 20% of that goes to whoever referred you.\\n\\n"
                "<i>Support: @SovereignSniper</i>"
            )
            self.send_message(msg, chat_id)'''

content = content.replace(old_help, new_help)

with open('core/telegram_bot_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Help updated!")
