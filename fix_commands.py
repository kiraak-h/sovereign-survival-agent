import sys

with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix duplicate /scan routing - the first one is exact match, second is startswith
# The exact match catches /scan with no args, startswith catches /scan TOKEN_ADDRESS
# We need to collapse them properly - keep only the startswith version
content = content.replace(
    '''        elif cmd_text == "/scan":
            self._handle_scan(cmd_text, chat_id)
        elif cmd_text == "/status":''',
    '''        elif cmd_text == "/status":'''
)

# 2. Fix /dca vs /dcaoff ordering - dcaoff must come FIRST or /dca will catch /dcaoff
content = content.replace(
    '''        elif cmd_text.startswith("/dca"):
            self._handle_dca(cmd_text, chat_id)
        elif cmd_text.startswith("/dcaoff"):
            self._handle_dcaoff(cmd_text, chat_id)''',
    '''        elif cmd_text.startswith("/dcaoff"):
            self._handle_dcaoff(cmd_text, chat_id)
        elif cmd_text.startswith("/dca"):
            self._handle_dca(cmd_text, chat_id)'''
)

# 3. Update _register_bot_commands with the complete command list
old_commands = '''            commands = [
                  {"command": "wallet", "description": "Generate or view your trading wallet"},
                  {"command": "buy", "description": "Securely snipe a token (/buy address amount)"},
                  {"command": "pnl", "description": "Generate a profit flex card (/pnl token %)"},
                  {"command": "refer", "description": "Get your referral link and view earnings"},
                  {"command": "status", "description": "View live agent revenue metrics"},
                  {"command": "sweep", "description": "Force on-chain settlement"},
                  {"command": "help", "description": "Show help and command guide"}
              ]'''

new_commands = '''            commands = [
                  # --- Core ---
                  {"command": "start",      "description": "Open main menu with live wallet balance"},
                  {"command": "help",       "description": "Full FAQ and command guide"},
                  # --- Wallet ---
                  {"command": "wallet",     "description": "View your wallet address & balance"},
                  {"command": "import",     "description": "Securely import an existing wallet (/import PK)"},
                  {"command": "withdraw",   "description": "Send ETH out (/withdraw ADDRESS AMOUNT)"},
                  # --- Trading ---
                  {"command": "buy",        "description": "Buy a token (/buy ADDRESS ETH_AMOUNT)"},
                  {"command": "positions",  "description": "View portfolio with 1-click sell buttons"},
                  {"command": "scan",       "description": "Full token intelligence report (/scan ADDRESS)"},
                  {"command": "takeprofit", "description": "Set take-profit limit (/takeprofit TOKEN PCT)"},
                  # --- Automation ---
                  {"command": "dca",        "description": "Auto-buy on schedule (/dca TOKEN ETH MINUTES)"},
                  {"command": "dcaoff",     "description": "Cancel a DCA order (/dcaoff TOKEN)"},
                  {"command": "snipe",      "description": "Mempool sniper on/off (/snipe on ETH MIN_LIQ)"},
                  {"command": "copy",       "description": "Copy trade a wallet (/copy ADDRESS MAX_ETH)"},
                  {"command": "antrug",     "description": "Anti-rugpull shield on/off (/antrug on)"},
                  {"command": "trenches",   "description": "Ultra-degen micro-cap sniper (/trenches on ETH MCAP)"},
                  # --- Monitoring ---
                  {"command": "watch",      "description": "Set price alert (/watch TOKEN PRICE above/below)"},
                  {"command": "watchlist",  "description": "View all active price alerts"},
                  {"command": "history",    "description": "View your last 10 trades"},
                  # --- Social ---
                  {"command": "rewards",    "description": "Referral dashboard and earnings"},
                  {"command": "pnl",        "description": "Generate PnL flex card (/pnl TOKEN PCT)"},
                  {"command": "refer",      "description": "Get your referral invite link"},
                  # --- Admin ---
                  {"command": "status",     "description": "View live agent revenue metrics"},
                  {"command": "sweep",      "description": "Force on-chain treasury settlement"},
              ]'''

content = content.replace(old_commands, new_commands)

with open('core/telegram_bot_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Commands updated!")
