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
                subscribe_msg = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "eth_subscribe",
                    "params": ["alchemy_pendingTransactions"]
                }
                await websocket.send(json.dumps(subscribe_msg))
                response = await websocket.recv()
                print(f"Mempool Streamer: Subscribed: {response}")
                
                # We need to import the engines safely without circular imports
                import server
                
                while True:
                    msg = await websocket.recv()
                    data = json.loads(msg)
                    
                    if "params" in data and "result" in data["params"]:
                        tx = data["params"]["result"]
                        input_data = tx.get("input", "")
                        
                        # 0xf305d719 = addLiquidityETH
                        if input_data.startswith("0xf305d719") and len(input_data) >= 74:
                            token_address = "0x" + input_data[34:74]
                            print(f"[⚡ SNIPER] Liquidity Added! Token: {token_address} TX: {tx.get('hash')}")
                            # Trigger Sniper Engine
                            server._mempool_sniper.trigger_snipe(token_address)
                            
                        # 0x02751cec = removeLiquidityETH
                        elif input_data.startswith("0x02751cec") and len(input_data) >= 74:
                            token_address = "0x" + input_data[34:74]
                            print(f"[🛡️ ANTI-RUG] Dev Removing Liquidity! Token: {token_address} TX: {tx.get('hash')}")
                            # Trigger Anti-Rug Engine
                            server._anti_rug_engine.trigger_rug_evasion(token_address)
                            
        except Exception as e:
            print(f"Mempool Streamer Error: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)

def start_streamer_task():
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(stream_mempool())
    except RuntimeError:
        pass
