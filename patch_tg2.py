import os
import re

filepath = 'core/telegram_bot_service.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. P&L Visualizer for 1-click sell
def replace_method(content, method_name, new_method):
    pattern = r"    def " + method_name + r"\(self,.*?\):.*?(?=    def |\Z)"
    return re.sub(pattern, new_method + '\n', content, flags=re.DOTALL)

new_sell = '''    def _handle_1click_sell(self, chat_id: str, token: str, pct: int):
        try:
            from core.sniper_wallet import get_wallet_by_chat_id, get_entry_price, get_mev_tip
            from core.dex_router import execute_partial_sell
            from core.watchlist_engine import get_real_price
            from core.pnl_generator import generate_pnl_image
            
            wallet = get_wallet_by_chat_id(chat_id)
            if not wallet:
                return
                
            self.send_message(f"⏳ <i>Executing {pct}% Sell for {token}...</i>", chat_id)
            mev_tip = get_mev_tip(chat_id)
            result = execute_partial_sell(wallet['private_key'], token, pct, mev_tip_eth=mev_tip)
            
            if result['status'] == 'SUCCESS':
                entry_price = get_entry_price(chat_id, token)
                current_price = get_real_price(token)
                
                caption = f"✅ <b>Sell Executed!</b>\\n\\nDumped {pct}% of <b>{token}</b>.\\nTx: <code>{result['tx_hash']}</code>"
                
                if entry_price > 0 and current_price > 0:
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100
                    try:
                        buf = generate_pnl_image(token, pnl_pct)
                        self.send_photo(buf, caption, chat_id)
                        return
                    except Exception as e:
                        pass
                
                self.send_message(caption, chat_id)
            else:
                self.send_message(f"❌ Sell Failed: {result['message']}", chat_id)
        except Exception as e:
            self.send_message(f"❌ Error: {e}", chat_id)'''

new_copy = '''    def _handle_copy(self, cmd_text: str, chat_id: str):
        parts = cmd_text.split()
        from core.sniper_wallet import get_copy_targets, add_copy_target, toggle_copy_target, remove_copy_target
        
        if len(parts) == 1:
            targets = get_copy_targets(chat_id)
            if not targets:
                return self.send_message("🦇 <b>Vampire Copy Trading</b>\\n\\nYou have no active targets.\\n\\n<b>Add a target:</b>\\n<code>/copy [ADDRESS] [MAX_SPEND_ETH]</code>", chat_id)
                
            msg = "🦇 <b>Your Vampire Targets:</b>\\n\\n"
            keyboard = {"inline_keyboard": []}
            for idx, t in enumerate(targets):
                addr = t['target_address']
                status = "🟢 ACTIVE" if t['is_active'] else "🔴 PAUSED"
                msg += f"{idx+1}. <code>{addr}</code>\\n   Spend: {t['max_spend_eth']} ETH | {status}\\n\\n"
                
                action = "pause" if t['is_active'] else "resume"
                keyboard["inline_keyboard"].append([
                    {"text": f"Toggle {addr[:6]}", "callback_data": f"copy_toggle_{addr}"},
                    {"text": f"Delete {addr[:6]}", "callback_data": f"copy_del_{addr}"}
                ])
                
            keyboard["inline_keyboard"].append([{"text": "🔙 Back", "callback_data": "menu_back"}])
            return self.send_message(msg, chat_id, reply_markup=keyboard)
            
        if len(parts) != 3:
            return self.send_message("❌ Usage: /copy [TARGET_ADDRESS] [MAX_SPEND_ETH]", chat_id)
            
        target = parts[1]
        try:
            max_spend = float(parts[2])
        except ValueError:
            return self.send_message("❌ Invalid ETH amount.", chat_id)
            
        add_copy_target(chat_id, target, max_spend)
        from server import _copy_engine
        _copy_engine.load_targets_from_db()
        
        self.send_message(f"🦇 <b>Vampire Copy Trading Activated!</b>\\n\\nTarget: <code>{target}</code>\\nMax Spend: {max_spend} ETH per trade\\n\\n<i>Monitoring mempool for target transactions...</i>", chat_id)'''

content = replace_method(content, "_handle_1click_sell", new_sell)
content = replace_method(content, "_handle_copy", new_copy)

# Also add _handle_referrals and _handle_mev
new_funcs = '''
    def _handle_referrals(self, chat_id: str):
        from core.sniper_wallet import get_referral_stats
        stats = get_referral_stats(chat_id)
        msg = (
            f"🤝 <b>Referral Dashboard</b>\\n\\n"
            f"Invite friends and earn 20% of their trading fees forever!\\n\\n"
            f"👥 <b>Total Invited:</b> {stats['count']}\\n"
            f"💰 <b>Total Earned:</b> {stats['rewards']} ETH\\n\\n"
            f"<b>Your Link:</b>\\n"
            f"<code>https://t.me/SovereignSniperBot?start=ref_{chat_id}</code>"
        )
        keyboard = {"inline_keyboard": [
            [{"text": "🎁 Claim Rewards", "callback_data": "claim_rewards"}],
            [{"text": "🔙 Back", "callback_data": "menu_back"}]
        ]}
        self.send_message(msg, chat_id, reply_markup=keyboard)

    def _handle_mev(self, cmd_text: str, chat_id: str):
        parts = cmd_text.split()
        if len(parts) != 2:
            from core.sniper_wallet import get_mev_tip
            current = get_mev_tip(chat_id)
            return self.send_message(f"🏎️ <b>MEV Bribe / Tip Config</b>\\n\\nCurrent Tip: <code>{current} ETH</code>\\n\\nHigher tips guarantee faster transactions.\\n<b>Usage:</b> <code>/mev [ETH_AMOUNT]</code>\\n<i>Example: /mev 0.01</i>", chat_id)
        try:
            tip = float(parts[1])
            from core.sniper_wallet import set_mev_tip
            set_mev_tip(chat_id, tip)
            self.send_message(f"✅ <b>MEV Bribe Updated!</b>\\n\\nEvery transaction will now include a {tip} ETH tip to the block builder.", chat_id)
        except ValueError:
            self.send_message("❌ Invalid amount.", chat_id)
'''

content = content.replace("def _handle_dca(self", new_funcs.strip() + "\n\n    def _handle_dca(self")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Regex replacement completed.")
