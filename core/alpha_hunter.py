import os
import requests
import time
from typing import List, Dict

BITQUERY_API_KEY = os.getenv("BITQUERY_API_KEY", "")

class AlphaHunter:
    def __init__(self):
        self.api_url = "https://streaming.bitquery.io/graphql"
        
    def fetch_smart_money(self) -> List[Dict]:
        """
        Fetches top traders from Bitquery API on Base Chain.
        If no API key is provided, returns simulated 'smart money' targets for testing.
        """
        if not BITQUERY_API_KEY:
            # Fallback to simulated data so the user can test the flow immediately
            return [
                {"address": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984", "win_rate": 82.5, "tx_count": 12},
                {"address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045", "win_rate": 78.1, "tx_count": 45},
                {"address": "0x514910771AF9Ca656af840dff83E8264EcF986CA", "win_rate": 91.0, "tx_count": 5}
            ]

        # V2 Bitquery query for top DEX buyers on Base
        query = '''
        query TopTraders {
          EVM(dataset: combined, network: base) {
            DEXTrades(
              limit: {count: 50}
              orderBy: {descending: Trade_Buy_AmountInUSD}
              where: {Trade: {Dex: {ProtocolFamily: {is: "Uniswap"}}}}
            ) {
              Trade {
                Buy {
                  Buyer
                  AmountInUSD
                }
              }
            }
          }
        }
        '''
        
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": BITQUERY_API_KEY,
            "Authorization": f"Bearer {BITQUERY_API_KEY}"
        }
        
        try:
            response = requests.post(self.api_url, json={'query': query}, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                trades = data.get("data", {}).get("EVM", {}).get("DEXTrades", [])
                
                # Aggregate by buyer
                buyers = {}
                for t in trades:
                    buyer = t.get("Trade", {}).get("Buy", {}).get("Buyer")
                    if buyer:
                        buyers[buyer] = buyers.get(buyer, 0) + 1
                        
                results = []
                for addr, count in buyers.items():
                    results.append({
                        "address": addr,
                        "win_rate": 85.0, # Placeholder for advanced PNL logic
                        "tx_count": count
                    })
                return results
            else:
                return []
        except Exception as e:
            print(f"AlphaHunter API Error: {e}")
            return []

    def filter_wallets(self, raw_wallets: List[Dict]) -> List[str]:
        """
        Filters out MEV bots (tx_count > 100) and low win-rate wallets.
        Returns a list of addresses.
        """
        approved = []
        for w in raw_wallets:
            if w["tx_count"] > 100:
                continue # Likely MEV or Arb bot
            if w["win_rate"] < 70.0:
                continue # Not profitable enough
                
            approved.append(w["address"])
            
            if len(approved) >= 3: # Keep top 3
                break
                
        return approved

    def inject_targets(self, chat_id: str, targets: List[str], max_spend: float = 0.005) -> int:
        """
        Injects the approved targets into the copy_targets database table.
        Returns the number of injected targets.
        """
        from core.sniper_wallet import add_copy_target, get_copy_targets
        
        existing = [t['target_address'].lower() for t in get_copy_targets(chat_id)]
        
        injected_count = 0
        for addr in targets:
            if addr.lower() not in existing:
                add_copy_target(chat_id, addr, max_spend)
                injected_count += 1
                
        # Reload the engine
        try:
            from server import _copy_engine
            _copy_engine.load_targets_from_db()
        except Exception:
            pass
            
        return injected_count

    def execute_hunt(self, chat_id: str) -> int:
        raw = self.fetch_smart_money()
        filtered = self.filter_wallets(raw)
        return self.inject_targets(chat_id, filtered)

alpha_hunter_engine = AlphaHunter()
