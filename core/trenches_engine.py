import time
import json
import urllib.request
import ssl

class TrenchesEngine:
    def __init__(self, telegram_service=None):
        self.active = {}
        self.telegram_service = telegram_service
        self._ctx = ssl.create_default_context()
        self._ctx.check_hostname = False
        self._ctx.verify_mode = ssl.CERT_NONE
        self._seen_tokens = set()

    def enable(self, chat_id: str, max_spend: float):
        self.active[chat_id] = {'max_spend': max_spend}

    def disable(self, chat_id: str):
        self.active.pop(chat_id, None)

    def _fetch_new_pairs(self) -> dict | None:
        try:
            url = "https://api.dexscreener.com/latest/dex/tokens/0x4200000000000000000000000000000000000006" # WETH Base
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5, context=self._ctx) as r:
                data = json.loads(r.read())
                
            pairs = data.get('pairs', [])
            for p in pairs:
                if p.get('chainId') == 'base':
                    token = p.get('baseToken', {}).get('address')
                    if token and token not in self._seen_tokens:
                        self._seen_tokens.add(token)
                        mcap = float(p.get('fdv', 0))
                        liq = float(p.get('liquidity', {}).get('usd', 0))
                        
                        # Only return microcaps
                        if 1000 <= mcap <= 100000:
                            return {'token': token, 'mcap': mcap, 'liquidity': liq}
            return None
        except Exception:
            return None

    def poll(self):
        while True:
            time.sleep(15) # Poll DexScreener every 15 seconds
            if not self.active:
                continue
            
            launch = self._fetch_new_pairs()
            if not launch:
                continue
                
            # We found a real token, now execute real trades!
            for chat_id, config in self.active.items():
                if self.telegram_service:
                    self.telegram_service.send_message(
                        f"☢️ <b>TRENCHES: MICROCAP SPOTTED</b>\n\n"
                        f"Token: <code>{launch['token']}</code>\n"
                        f"MCap: \n"
                        f"Liquidity: \n\n"
                        f"⚡ <i>Running GoPlus AST scan...</i>",
                        chat_id
                    )
                
                from core.token_scanner import check_honeypot
                if not check_honeypot(launch['token']):
                    if self.telegram_service:
                        self.telegram_service.send_message(f"🚨 <b>HONEYPOT DETECTED</b> in {launch['token']}. Snipe aborted.", chat_id)
                    continue
                    
                from core.sniper_wallet import get_or_create_wallet
                from core.dex_router import execute_snipe
                
                wallet = get_or_create_wallet(chat_id)
                r = execute_snipe(wallet['private_key'], launch['token'], config['max_spend'])
                
                if r['status'] == 'SUCCESS':
                    if self.telegram_service:
                        self.telegram_service.send_message(
                            f"✅ <b>Trenches Snipe Executed!</b>\n"
                            f"<code>{launch['token']}</code>\n"
                            f"{r['trade_eth']} ETH | Tx: <code>{r.get('tx_hash', r.get('simulated_tx_hash'))}</code>",
                            chat_id
                        )
                else:
                    if self.telegram_service:
                        self.telegram_service.send_message(f"❌ Snipe Failed: {r['message']}", chat_id)
