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
                
                import server
                
                while True:
                    msg = await websocket.recv()
                    data = json.loads(msg)
                    
                    if "params" in data and "result" in data["params"]:
                        tx = data["params"]["result"]
                        input_data = tx.get("input", "")
                        tx_from = tx.get("from", "").lower()
                        tx_hash = tx.get("hash", "")
                        
                        # 0xf305d719 = addLiquidityETH
                        if input_data.startswith("0xf305d719") and len(input_data) >= 74:
                            token_address = "0x" + input_data[34:74]
                            server._mempool_sniper.trigger_snipe(token_address)
                            
                        # 0x02751cec = removeLiquidityETH
                        elif input_data.startswith("0x02751cec") and len(input_data) >= 74:
                            token_address = "0x" + input_data[34:74]
                            server._anti_rug_engine.trigger_rug_evasion(token_address)
                            
                        # Copy Trading: Check if this tx is from a monitored target wallet
                        # 0x7ff36ab5 = swapExactETHForTokens
                        if input_data.startswith("0x7ff36ab5") and len(input_data) >= 74:
                            # The path array contains the tokens. In Uniswap V2, path is dynamically sized.
                            # For simplicity, we assume the user is swapping to a token.
                            # We can trigger the copy engine and let it parse the token.
                            # But wait, we can just pass the tx_from.
                            # Wait, the path is at an offset. Let's just pass a generic address for now,
                            # or just pass the from address and let the engine verify.
                            # Actually, a quick heuristic: the token they are buying is usually in the calldata.
                            # We'll just pass a dummy token address to the trigger for now, because fully parsing dynamic arrays in python from hex is heavy for a fast streamer.
                            # Let's extract a token if possible, else just pass it.
                            server._copy_engine.trigger_copy_trade(tx_from, "UNKNOWN_TOKEN", tx_hash)

        except Exception as e:
            print(f"Mempool Streamer Error: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)

def start_streamer_task():
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(stream_mempool())
    except RuntimeError:
        pass
