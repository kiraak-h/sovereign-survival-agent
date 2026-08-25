import os
import json
import asyncio
import websockets
from dotenv import load_dotenv

load_dotenv()

ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")

async def stream_mempool():
    if not ALCHEMY_API_KEY:
        print("Mempool Streamer: ALCHEMY_API_KEY missing, skipping WS connection.")
        return

    uri = f"wss://base-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
    
    while True:
        try:
            print("Mempool Streamer: Connecting to Alchemy WSS...")
            async with websockets.connect(uri) as websocket:
                # Subscribe to full pending transactions
                subscribe_msg = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "eth_subscribe",
                    "params": ["alchemy_pendingTransactions"]
                }
                await websocket.send(json.dumps(subscribe_msg))
                
                response = await websocket.recv()
                print(f"Mempool Streamer: Subscribed: {response}")
                
                # Start consuming the stream
                while True:
                    msg = await websocket.recv()
                    data = json.loads(msg)
                    
                    if "params" in data and "result" in data["params"]:
                        tx = data["params"]["result"]
                        
                        # Process the transaction here
                        # We look for Uniswap V2 Router interactions (0x4752ba5DBc23f44D87826276BF6Fd6b1C372aD24 for Base)
                        # or specifically addLiquidity / removeLiquidity signatures
                        
                        input_data = tx.get("input", "")
                        
                        # MethodID for addLiquidityETH is 0xf305d719
                        # MethodID for removeLiquidityETH is 0x02751cec
                        # MethodID for setTax (varies, e.g., 0x2235bb70 or similar)
                        
                        if input_data.startswith("0xf305d719"):
                            # This is a liquidity add! Trigger Sniper
                            print(f"[⚡ SNIPER] Liquidity Added in Mempool! TX: {tx.get('hash')}")
                            # In real production, we would extract the token address and trigger _mempool_sniper.py
                            
                        elif input_data.startswith("0x02751cec"):
                            # This is a liquidity remove! Trigger Anti-Rug
                            print(f"[🛡️ ANTI-RUG] Dev Removing Liquidity! TX: {tx.get('hash')}")
                            # In real production, we would trigger _anti_rug_engine.py
                            
        except Exception as e:
            print(f"Mempool Streamer Error: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)

def start_streamer_task():
    # If there is a running loop, create task
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(stream_mempool())
    except RuntimeError:
        pass
