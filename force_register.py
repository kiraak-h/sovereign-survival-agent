import os
import requests
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("TELEGRAM_BOT_TOKEN")

if token:
    url = f"https://api.telegram.org/bot{token}/setMyCommands"
    commands = [
        {"command": "start",      "description": "Open main menu / Dashboard"},
        {"command": "wallet",     "description": "View address & balance"},
        {"command": "import",     "description": "Import private key securely"},
        {"command": "withdraw",   "description": "Withdraw ETH"},
        {"command": "buy",        "description": "Buy a token (/buy ADDRESS ETH)"},
        {"command": "positions",  "description": "View portfolio and 1-click sell"},
        {"command": "scan",       "description": "Full token intelligence report"},
        {"command": "takeprofit", "description": "Set take-profit limit (/takeprofit TOKEN PCT)"},
        {"command": "dca",        "description": "Auto-buy on schedule (/dca TOKEN ETH MINS)"},
        {"command": "dcaoff",     "description": "Cancel a DCA order (/dcaoff TOKEN)"},
        {"command": "snipe",      "description": "Mempool sniper on/off"},
        {"command": "copy",       "description": "Copy trade a wallet (/copy ADDRESS MAX_ETH)"},
        {"command": "antrug",     "description": "Anti-rugpull shield on/off"},
        {"command": "trenches",   "description": "Ultra-degen micro-cap sniper on/off"},
        {"command": "watch",      "description": "Set price alert (/watch TOKEN PRICE above/below)"},
        {"command": "watchlist",  "description": "View all active price alerts"},
        {"command": "history",    "description": "View your last 10 trades"},
        {"command": "rewards",    "description": "Referral dashboard and earnings"},
        {"command": "pnl",        "description": "Generate PnL flex card"},
        {"command": "refer",      "description": "Get your referral invite link"},
        {"command": "help",       "description": "Show help and command guide"}
    ]
    res = requests.post(url, json={"commands": commands}, timeout=8.0)
    print("Force updated Telegram commands:", res.json())
else:
    print("No token found")
