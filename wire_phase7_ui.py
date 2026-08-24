import sys

with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Wire menu_watchlist
content = content.replace(
    'elif data == "menu_scanner":',
    '''elif data == "menu_watchlist":
            self.handle_command("/watchlist", chat_id)
        elif data == "menu_scanner":'''
)

# 2. Wire menu_dca
content = content.replace(
    'elif data == "menu_import":',
    '''elif data == "menu_dca":
            self.send_message("<b>🕒 DCA Orders</b>\\n\\nSet a recurring auto-buy:\\n<code>/dca [TOKEN] [ETH] [MINUTES]</code>\\n<i>Example: /dca 0x123... 0.05 60</i>\\n\\nCancel with: <code>/dcaoff [TOKEN]</code>", chat_id)
        elif data == "menu_import":'''
)

# 3. Wire menu_rewards
content = content.replace(
    'elif data == "menu_dca":',
    '''elif data == "menu_rewards":
            self.handle_command("/rewards", chat_id)
        elif data == "menu_dca":'''
)

# 4. Wire commands
content = content.replace(
    'elif cmd_text.startswith("/antrug"):',
    '''elif cmd_text.startswith("/scan"):
            self._handle_scan(cmd_text, chat_id)
        elif cmd_text.startswith("/dca"):
            self._handle_dca(cmd_text, chat_id)
        elif cmd_text.startswith("/dcaoff"):
            self._handle_dcaoff(cmd_text, chat_id)
        elif cmd_text.startswith("/watch"):
            self._handle_watch(cmd_text, chat_id)
        elif cmd_text == "/watchlist":
            self._handle_watchlist(chat_id)
        elif cmd_text == "/history":
            self._handle_history(chat_id)
        elif cmd_text == "/rewards":
            self._handle_rewards(chat_id)
        elif cmd_text.startswith("/antrug"):'''
)

# 5. Add all new methods
new_methods = '''
    def _handle_scan(self, cmd_text: str, chat_id: str):
        parts = cmd_text.split()
        if len(parts) != 2:
            return self.send_message("❌ Usage: /scan [TOKEN_ADDRESS]", chat_id)
        token = parts[1]
        self.send_message(f"🔍 <i>Running full intelligence scan on {token[:10]}...\\nAggregating honeypot, liquidity, holder, and deployer data...</i>", chat_id)
        try:
            from core.token_scanner import TokenScanner
            scanner = TokenScanner()
            r = scanner.scan(token)
            verdict_emoji = {"SAFE": "🟢", "MODERATE": "🟡", "RISKY": "🔴", "DANGER": "💀"}.get(r['verdict'], "⚪")
            hp = "🚨 YES — HONEYPOT" if r['is_honeypot'] else "✅ No"
            verified = "✅ Verified" if r['is_verified'] else "❌ Unverified"
            lp = f"🔒 Locked ({r['lp_lock_days']}d)" if r['lp_locked'] else "🔓 UNLOCKED"
            msg = (
                f"🔍 <b>Token Intelligence Report</b>\\n"
                f"<code>{token}</code>\\n\\n"
                f"{verdict_emoji} <b>Verdict: {r['verdict']}</b> (Risk Score: {r['risk_score']}/100)\\n\\n"
                f"<b>Honeypot:</b> {hp}\\n"
                f"<b>Contract:</b> {verified}\\n"
                f"<b>Buy Tax:</b> {r['buy_tax']}% | <b>Sell Tax:</b> {r['sell_tax']}%\\n"
                f"<b>Liquidity:</b> {r['liquidity_eth']} ETH\\n"
                f"<b>Market Cap:</b> \\n"
                f"<b>Holders:</b> {r['holder_count']:,}\\n"
                f"<b>Top 10 Hold:</b> {r['top_10_holders_pct']}%\\n"
                f"<b>LP Status:</b> {lp}\\n"
                f"<b>Deployer Age:</b> {r['deployer_age_days']} days | {r['deployer_tx_count']} txs"
            )
            keyboard = {"inline_keyboard": [[
                {"text": "🟢 Buy This", "callback_data": f"quickbuy_{token}"},
                {"text": "⭐ Watch It", "callback_data": f"quickwatch_{token}"}
            ]]}
            self.send_message(msg, chat_id, reply_markup=keyboard)
        except Exception as e:
            self.send_message(f"❌ Scan error: {e}", chat_id)

    def _handle_dca(self, cmd_text: str, chat_id: str):
        parts = cmd_text.split()
        if len(parts) != 4:
            return self.send_message("❌ Usage: /dca [TOKEN] [ETH_AMOUNT] [INTERVAL_MINUTES]", chat_id)
        token, eth_str, interval_str = parts[1], parts[2], parts[3]
        try:
            eth = float(eth_str)
            interval = int(interval_str)
        except ValueError:
            return self.send_message("❌ Invalid amount or interval.", chat_id)
        from core.dca_engine import create_dca_order
        create_dca_order(chat_id, token, eth, interval)
        self.send_message(
            f"✅ <b>DCA Order Created!</b>\\n\\n"
            f"Token: <code>{token}</code>\\n"
            f"Buy: {eth} ETH every {interval} minutes\\n\\n"
            f"<i>First buy executes in {interval} minutes. EVM Shield active on every buy.\\nUse /dcaoff to cancel.</i>",
            chat_id
        )

    def _handle_dcaoff(self, cmd_text: str, chat_id: str):
        parts = cmd_text.split()
        if len(parts) != 2:
            return self.send_message("❌ Usage: /dcaoff [TOKEN]", chat_id)
        from core.dca_engine import cancel_dca_order
        cancel_dca_order(chat_id, parts[1])
        self.send_message(f"🔴 DCA order for <code>{parts[1]}</code> cancelled.", chat_id)

    def _handle_watch(self, cmd_text: str, chat_id: str):
        parts = cmd_text.split()
        if len(parts) < 3:
            return self.send_message("❌ Usage: /watch [TOKEN] [TARGET_PRICE] [above/below]\\n<i>Default direction: above</i>", chat_id)
        token = parts[1]
        try:
            price = float(parts[2])
        except ValueError:
            return self.send_message("❌ Invalid price.", chat_id)
        direction = parts[3].upper() if len(parts) >= 4 else "ABOVE"
        from core.watchlist_engine import add_to_watchlist
        add_to_watchlist(chat_id, token, price, direction)
        self.send_message(
            f"⭐ <b>Watchlist Alert Set!</b>\\n\\n"
            f"Token: <code>{token}</code>\\n"
            f"Alert when: price goes {direction} \\n\\n"
            f"<i>I will ping you the moment this triggers.</i>",
            chat_id
        )

    def _handle_watchlist(self, chat_id: str):
        from core.watchlist_engine import get_active_watchlist
        items = get_active_watchlist(chat_id)
        if not items:
            return self.send_message("⭐ <b>Watchlist</b>\\n\\nNo active alerts. Set one with:\\n<code>/watch [TOKEN] [PRICE]</code>", chat_id)
        msg = "⭐ <b>Your Watchlist</b>\\n\\n"
        for item in items:
            msg += f"• <code>{item['token'][:10]}...</code> — Alert {item['direction']} \\n"
        self.send_message(msg, chat_id)

    def _handle_history(self, chat_id: str):
        from core.watchlist_engine import get_tx_history
        txs = get_tx_history(chat_id)
        if not txs:
            return self.send_message("📋 <b>Transaction History</b>\\n\\nNo trades recorded yet.", chat_id)
        msg = "📋 <b>Last Trades</b>\\n\\n"
        for tx in txs:
            import datetime
            dt = datetime.datetime.fromtimestamp(tx['ts']).strftime('%m/%d %H:%M')
            pnl_str = f"+{tx['pnl']}%" if tx['pnl'] >= 0 else f"{tx['pnl']}%"
            emoji = "🟢" if tx['pnl'] >= 0 else "🔴"
            msg += f"{emoji} <b>{tx['action']}</b> {tx['eth']} ETH → <code>{tx['token'][:8]}...</code> | {pnl_str} | {dt}\\n"
        self.send_message(msg, chat_id)

    def _handle_rewards(self, chat_id: str):
        from core.sniper_wallet import get_referral_stats
        stats = get_referral_stats(chat_id)
        bot_username = "SovereignSniperBot"
        link = f"https://t.me/{bot_username}?start=ref_{chat_id}"
        msg = (
            f"💰 <b>Sovereign Referral Dashboard</b>\\n\\n"
            f"🔗 <b>Your Invite Link:</b>\\n<code>{link}</code>\\n\\n"
            f"👥 <b>Total Referrals:</b> {stats['count']}\\n"
            f"💎 <b>Total Earned:</b> {stats['rewards']:.5f} ETH\\n"
            f"📈 <b>Reward Rate:</b> 20% of all referral fees, forever\\n\\n"
            f"<i>Share your link. Every trade they make earns you 20% of our 1% fee automatically.</i>"
        )
        self.send_message(msg, chat_id)
'''

content += new_methods

with open('core/telegram_bot_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Phase 7 UI wired")
