# Sovereign Survival Agent - Universal Memory

## Context
The project evolved from a B2B Autonomous Developer Agent (Phase 1-3) into a vertically integrated B2C Telegram Trading Empire (Phase 4). The agent monetizes its proprietary AST Smart Contract Security Oracle by packaging it into a consumer-facing Telegram Sniper Bot, charging a 1% fee on safe trades. We are now entering Phase 5 (The Trojan Killer), expanding the bot's features to dominate the consumer market.

## Architectural Decisions
1. **Role-Based Access Control (RBAC):** Instead of running two bots, the single @SovereignSniperBot dynamically renders Admin commands (/status, /sweep) only if the chat_id matches the .env.agent TELEGRAM_CHAT_ID.
2. **Wallet Generation:** Non-custodial base L2 wallets. Symmetrically encrypted via cryptography.fernet. 
3. **The Referral Engine:** 20% of the 1% trading fee is routed back to the referrer off-chain.

## Burn Book (Failed Approaches)
1. **Volatile Encryption Keys:** Relying purely on os.environ.get('SNIPER_MASTER_KEY', generate_key()) was a critical failure. Render restarts wiped the ephemeral key, permanently locking the sniper_wallets.db records. **Fix:** The key is now persistently saved to sniper_master.key as a fallback.
2. **HTML Parsing mode in Telegram:** Hardcoding parse_mode="HTML" caused silent 400 Bad Request drops when sending markdown containing < or > characters (e.g., <token>). **Fix:** Escaped angle brackets and corrected send_message signature arguments.
3. **PowerShell Here-Strings for Python:** PowerShell aggressive interpolation corrupts python syntax when piping strings. **Fix:** Exclusively use pure python scripts or eplace_file_content for syntax injection.

## Active Scratchpad (Next Immediate Steps)
* **Status:** Finished Phase 5, Step 1 (Referral Engine).
* **Next Session Goal:** Execute Phase 5, Step 2 (PnL "Flex" Cards). 
* **Requirements for Tomorrow:** We will need to build an image generation/rendering pipeline (perhaps HTML-to-Image or Pillow) so the bot can generate dynamic branded profit cards when the user types /pnl [token].
