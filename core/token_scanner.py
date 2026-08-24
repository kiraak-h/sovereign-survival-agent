import random
import time

class TokenScanner:
    '''
    Phase 7.1: Full Token Intelligence Report.
    
    In production: Aggregates data from:
    - honeypot.is API (buy/sell tax simulation)
    - Basescan API (contract verification, deployer age)
    - Uniswap V2/V3 subgraph (liquidity, volume)
    - ERC-20 transfer events (holder count, top holders %)
    '''
    
    def scan(self, token_address: str) -> dict:
        time.sleep(2) # Simulate multi-source API aggregation
        
        # Deterministic simulation: 0xdead/0xbad = scam
        is_scam = (
            token_address.lower().startswith("0xdead") or
            token_address.lower().startswith("0xbad")
        )
        
        if is_scam:
            return {
                'symbol': 'SCAM',
                'name': 'Unknown Token',
                'is_honeypot': True,
                'is_verified': False,
                'buy_tax': 99.0,
                'sell_tax': 100.0,
                'liquidity_eth': 0.1,
                'market_cap_usd': 500,
                'holder_count': 3,
                'top_10_holders_pct': 99.9,
                'deployer_age_days': 0,
                'deployer_tx_count': 2,
                'lp_locked': False,
                'lp_lock_days': 0,
                'verdict': 'DANGER',
                'risk_score': 99
            }
        
        # Legitimate token simulation
        buy_tax = round(random.uniform(0.0, 5.0), 1)
        sell_tax = round(random.uniform(0.0, 5.0), 1)
        lp_locked = random.random() > 0.3
        deployer_age = random.randint(30, 900)
        holder_count = random.randint(200, 50000)
        top_10_pct = round(random.uniform(15.0, 60.0), 1)
        liquidity = round(random.uniform(5.0, 500.0), 2)
        mcap = round(random.uniform(50000, 5000000), 0)
        
        # Risk scoring
        risk = 0
        if buy_tax > 5: risk += 20
        if sell_tax > 5: risk += 30
        if not lp_locked: risk += 25
        if top_10_pct > 50: risk += 15
        if deployer_age < 30: risk += 10
        
        if risk < 20:
            verdict = 'SAFE'
        elif risk < 50:
            verdict = 'MODERATE'
        else:
            verdict = 'RISKY'
            
        return {
            'symbol': 'TOKEN',
            'name': 'Base Token',
            'is_honeypot': False,
            'is_verified': random.random() > 0.4,
            'buy_tax': buy_tax,
            'sell_tax': sell_tax,
            'liquidity_eth': liquidity,
            'market_cap_usd': mcap,
            'holder_count': holder_count,
            'top_10_holders_pct': top_10_pct,
            'deployer_age_days': deployer_age,
            'deployer_tx_count': random.randint(10, 500),
            'lp_locked': lp_locked,
            'lp_lock_days': random.randint(30, 365) if lp_locked else 0,
            'verdict': verdict,
            'risk_score': risk
        }
