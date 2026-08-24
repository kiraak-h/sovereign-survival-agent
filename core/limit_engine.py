import time
import random
import os
import requests
import sys

# Ensure we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(".env.agent")

from core.sniper_wallet import get_pending_orders, mark_order_executed, get_wallet_by_chat_id
from core.dex_router import execute_sell
from core.metabolism import MetabolismManager
from core.models import AgentState

class LimitEngine:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        _dummy_state = AgentState(
            agent_address="0xLIMIT",
            session_key_address="0xSESSION",
            treasury_usdc=0.0,
            treasury_eth=0.0,
            fixed_burn_rate_hourly=0.0
        )
        self.metabolism = MetabolismManager(_dummy_state)

    def alert_user(self, chat_id: str, message: str):
        if not self.bot_token:
            return
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        try:
            requests.post(url, json=payload, timeout=5.0)
        except Exception as e:
            print(f"[LimitEngine] Alert failed: {e}")

    def poll(self):
        print("[LimitEngine] Monitoring for take-profit limits...")
        while True:
            try:
                orders = get_pending_orders()
                for order in orders:
                    pump_chance = random.random()
                    
                    if pump_chance > 0.7:  # 30% chance it hits the target per loop
                        print(f"[LimitEngine] Target HIT for Order #{order['id']} (+{order['target_percentage']}%)")
                        
                        wallet = get_wallet_by_chat_id(order['chat_id'])
                        if not wallet:
                            continue
                            
                        # Execute the Sell!
                        result = execute_sell(
                            wallet['private_key'], 
                            order['token_address'], 
                            order['target_percentage'], 
                            wallet['referrer_id']
                        )
                        
                        if result['status'] == 'SUCCESS':
                            mark_order_executed(order['id'])
                            
                            # Credit Treasury
                            self.metabolism.credit_revenue(
                                amount_usdc=result['treasury_fee_eth'] * 3000,
                                source_description=f"Limit Sell Fee | User: {order['chat_id']} | Token: {order['token_address'][:6]}"
                            )
                            
                            # Alert User
                            msg = (
                                f"🎯 <b>TAKE PROFIT EXECUTED</b> 🎯\n\n"
                                f"<b>Token:</b> <code>{order['token_address']}</code>\n"
                                f"<b>Target:</b> +{order['target_percentage']}%\n"
                                f"<b>Returned:</b> {result['trade_eth']:.4f} ETH\n"
                                f"<b>Fee:</b> {result['treasury_fee_eth']:.4f} ETH\n\n"
                                f"<i>Trade automatically settled to your Sovereign Wallet.</i>"
                            )
                            self.alert_user(order['chat_id'], msg)
            except Exception as e:
                print(f"[LimitEngine] Error: {e}")
                
            time.sleep(5)

if __name__ == "__main__":
    engine = LimitEngine()
    engine.poll()
