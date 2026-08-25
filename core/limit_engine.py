import time
import os
import json
from core.sniper_wallet import get_pending_orders, mark_order_executed, get_wallet_by_chat_id
from core.watchlist_engine import get_real_price
from core.dex_router import execute_sell
from core.notifier import SovereignNotifier
from core.metabolism import MetabolismManager

class LimitEngine:
    """
    Scans pending limit orders and executes sells when targets are reached.
    Upgraded to support both Take-Profit (positive targets) and Stop-Loss (negative targets).
    """
    def __init__(self):
        self.notifier = SovereignNotifier()
        self.metabolism = MetabolismManager()
        
    def alert_user(self, chat_id, text):
        if self.notifier:
            self.notifier.send_telegram_message(text, chat_id)

    def poll(self):
        print("[LimitEngine] Monitoring for take-profit and stop-loss limits...")
        while True:
            try:
                orders = get_pending_orders()
                for order in orders:
                    current_price = get_real_price(order['token_address'])
                    entry_price = order.get('entry_price', 0.0)
                    
                    if current_price == 0.0 or entry_price == 0.0:
                        continue
                        
                    price_increase = (current_price - entry_price) / entry_price * 100
                    target = order['target_percentage']
                    
                    # Logic for TP vs SL
                    hit_tp = target > 0 and price_increase >= target
                    hit_sl = target < 0 and price_increase <= target
                    
                    if hit_tp or hit_sl:
                        event_type = "TAKE PROFIT" if hit_tp else "STOP LOSS"
                        emoji = "🟢" if hit_tp else "🔴"
                        print(f"[LimitEngine] {event_type} HIT for Order #{order['id']} ({price_increase:.2f}%)")
                        
                        wallet = get_wallet_by_chat_id(order['chat_id'])
                        if not wallet:
                            continue
                            
                        result = execute_sell(
                            wallet['private_key'], 
                            order['token_address'], 
                            100
                        )
                        
                        if result['status'] == 'SUCCESS':
                            mark_order_executed(order['id'])
                            
                            # Credit Treasury
                            fee_eth = result.get('fee_eth', 0.0)
                            self.metabolism.credit_revenue(
                                amount_usdc=fee_eth * 3000,
                                source_description=f"{event_type} Fee | User: {order['chat_id']} | Token: {order['token_address'][:6]}"
                            )
                            
                            msg = (
                                f"{emoji} <b>{event_type} EXECUTED</b> {emoji}\n\n"
                                f"<b>Token:</b> <code>{order['token_address']}</code>\n"
                                f"<b>Target:</b> {target}%\n"
                                f"<b>Actual Trigger:</b> {price_increase:.2f}%\n"
                                f"<b>Returned:</b> {result['trade_eth']:.4f} ETH\n"
                                f"<b>Fee:</b> {fee_eth:.4f} ETH\n\n"
                                f"<i>Trade automatically settled to your Sovereign Wallet.</i>"
                            )
                            self.alert_user(order['chat_id'], msg)
            except Exception as e:
                print(f"[LimitEngine] Error: {e}")
                
            time.sleep(15) # Poll every 15s for tighter stops

if __name__ == "__main__":
    engine = LimitEngine()
    engine.poll()
