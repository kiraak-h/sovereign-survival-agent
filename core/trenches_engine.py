# Trenches Mode: Ultra-degen micro-cap auto-sniper
import time
import random

class TrenchesEngine:
    '''
    Phase 7.6: Trenches Mode.
    Hunts ultra-micro-cap launches (under  mcap) and auto-snipes them.
    High risk, high reward. Designed for degens who want 100x or nothing.
    Filters: mcap < , liquidity > 0.5 ETH, honeypot check mandatory.
    '''
    def __init__(self, telegram_service=None):
        self.telegram_service = telegram_service
        self.active = {}  # {chat_id: {'max_spend': 0.02, 'mcap_limit': 50000}}

    def enable(self, chat_id: str, max_spend: float, mcap_limit: float = 50000):
        self.active[chat_id] = {'max_spend': max_spend, 'mcap_limit': mcap_limit}

    def disable(self, chat_id: str):
        self.active.pop(chat_id, None)

    def _simulate_micro_launch(self) -> dict | None:
        if random.random() < 0.04:
            token = "0x" + "".join(random.choices("abcdef0123456789", k=40))
            mcap = round(random.uniform(1000, 80000), 0)
            liquidity = round(random.uniform(0.3, 3.0), 2)
            return {'token': token, 'mcap': mcap, 'liquidity': liquidity}
        return None

    def poll(self):
        while True:
            time.sleep(5)
            if not self.active:
                continue
            launch = self._simulate_micro_launch()
            if not launch:
                continue
            for chat_id, config in list(self.active.items()):
                if launch['mcap'] > config['mcap_limit']:
                    continue
                if launch['liquidity'] < 0.5:
                    continue
                # Mandatory honeypot check even in trenches mode
                from core.evm_simulator import HoneypotSimulator
                sim = HoneypotSimulator()
                result = sim.simulate_trade_lifecycle(launch['token'], config['max_spend'])
                if result['is_honeypot']:
                    continue
                if self.telegram_service:
                    self.telegram_service.send_message(
                        f"🕳️ <b>TRENCHES: Micro-Cap Detected!</b>\\n\\n"
                        f"Token: <code>{launch['token']}</code>\\n"
                        f"Market Cap: \\n"
                        f"Liquidity: {launch['liquidity']} ETH\\n"
                        f"EVM Shield: ✅ Passed\\n\\n"
                        f"⚡ <i>Sniping {config['max_spend']} ETH...</i>",
                        chat_id
                    )
                try:
                    from core.sniper_wallet import get_wallet_by_chat_id
                    from core.dex_router import execute_snipe
                    wallet = get_wallet_by_chat_id(chat_id)
                    if wallet:
                        r = execute_snipe(wallet['private_key'], launch['token'], config['max_spend'])
                        if r['status'] == 'SUCCESS' and self.telegram_service:
                            self.telegram_service.send_message(
                                f"🎰 <b>Trenches Snipe Executed!</b>\\n"
                                f"<code>{launch['token']}</code>\\n"
                                f"{r['trade_eth']} ETH | Tx: <code>{r['simulated_tx_hash']}</code>",
                                chat_id
                            )
                except Exception as e:
                    if self.telegram_service:
                        self.telegram_service.send_message(f"❌ Trenches error: {e}", chat_id)
