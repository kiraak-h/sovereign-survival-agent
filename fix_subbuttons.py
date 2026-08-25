import sys

with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix menu_settings to use inline buttons
old_settings = '''        elif data == "menu_settings":
            self.send_message(
                "<b>⚙️ Settings &amp; Control Panel</b>\\n\\n"
                "🛡️ <b>Anti-Rugpull Shield</b>\\n"
                "  <code>/antrug on</code>  |  <code>/antrug off</code>\\n\\n"
                "⚡ <b>Mempool Sniper</b>\\n"
                "  <code>/snipe on [ETH] [MIN_LIQ]</code>  |  <code>/snipe off</code>\\n\\n"
                "👥 <b>Copy Trading</b>\\n"
                "  <code>/copy [ADDRESS] [MAX_ETH]</code>\\n\\n"
                "🕳️ <b>Trenches Mode</b>\\n"
                "  <code>/trenches on [ETH] [MCAP]</code>  |  <code>/trenches off</code>\\n\\n"
                "🕒 <b>DCA Orders</b>\\n"
                "  <code>/dca [TOKEN] [ETH] [MINS]</code>  |  <code>/dcaoff [TOKEN]</code>\\n\\n"
                "🎯 <b>Take Profit</b>\\n"
                "  <code>/takeprofit [TOKEN] [PCT]</code>\\n\\n"
                "🔔 <b>Price Alerts</b>\\n"
                "  <code>/watch [TOKEN] [PRICE] [above/below]</code>",
                chat_id
            )'''

new_settings = '''        elif data == "menu_settings":
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🛡️ Anti-Rug ON", "callback_data": "cmd_antrug_on"}, {"text": "🛡️ Anti-Rug OFF", "callback_data": "cmd_antrug_off"}],
                    [{"text": "⚡ Sniper ON", "callback_data": "cmd_snipe_on"}, {"text": "⚡ Sniper OFF", "callback_data": "cmd_snipe_off"}],
                    [{"text": "🕳️ Trenches ON", "callback_data": "cmd_trenches_on"}, {"text": "🕳️ Trenches OFF", "callback_data": "cmd_trenches_off"}],
                    [{"text": "🔙 Back to Main Menu", "callback_data": "menu_back"}]
                ]
            }
            self.send_message(
                "<b>⚙️ Settings &amp; Control Panel</b>\\n\\n"
                "Tap a button below to quick-toggle a setting, or use the manual commands:\\n\\n"
                "👥 <b>Copy Trading:</b> <code>/copy [ADDR] [ETH]</code>\\n"
                "🕒 <b>DCA Orders:</b> <code>/dca [TOKEN] [ETH] [MINS]</code>\\n"
                "🎯 <b>Take Profit:</b> <code>/takeprofit [TOKEN] [PCT]</code>\\n"
                "🔔 <b>Price Alerts:</b> <code>/watch [TOKEN] [PRICE] [above/below]</code>",
                chat_id, reply_markup=keyboard
            )'''

content = content.replace(old_settings, new_settings)

# Update other menus to have a Back button
for menu_str, replacement in [
    ('        elif data == "menu_limits":\n            self.send_message("<b>🎯 Limit Orders</b>\\n\\nReply with: <code>/takeprofit [TOKEN] [PERCENTAGE]</code>\\n<i>Example: /takeprofit PEPE 50</i>", chat_id)',
     '        elif data == "menu_limits":\n            self.send_message("<b>🎯 Limit Orders</b>\\n\\nReply with: <code>/takeprofit [TOKEN] [PERCENTAGE]</code>\\n<i>Example: /takeprofit PEPE 50</i>", chat_id, reply_markup={"inline_keyboard": [[{"text": "🔙 Back", "callback_data": "menu_back"}]]})'),
     
    ('        elif data == "menu_dca":\n            self.send_message("<b>🕒 DCA Orders</b>\\n\\nSet a recurring auto-buy:\\n<code>/dca [TOKEN] [ETH] [MINUTES]</code>\\n<i>Example: /dca 0x123... 0.05 60</i>\\n\\nCancel with: <code>/dcaoff [TOKEN]</code>", chat_id)',
     '        elif data == "menu_dca":\n            self.send_message("<b>🕒 DCA Orders</b>\\n\\nSet a recurring auto-buy:\\n<code>/dca [TOKEN] [ETH] [MINUTES]</code>\\n<i>Example: /dca 0x123... 0.05 60</i>\\n\\nCancel with: <code>/dcaoff [TOKEN]</code>", chat_id, reply_markup={"inline_keyboard": [[{"text": "🔙 Back", "callback_data": "menu_back"}]]})'),
     
    ('        elif data == "menu_import":\n            self.send_message("<b>📥 Import Wallet</b>\\n\\nReply with: <code>/import [PRIVATE_KEY]</code>\\n\\n<i>⚠️ SECURITY: Your private key will be encrypted via AES-GCM and your message will be instantly deleted from the chat for safety.</i>", chat_id)',
     '        elif data == "menu_import":\n            self.send_message("<b>📥 Import Wallet</b>\\n\\nReply with: <code>/import [PRIVATE_KEY]</code>\\n\\n<i>⚠️ SECURITY: Your private key will be encrypted via AES-GCM and your message will be instantly deleted from the chat for safety.</i>", chat_id, reply_markup={"inline_keyboard": [[{"text": "🔙 Back", "callback_data": "menu_back"}]]})'),
     
    ('        elif data == "menu_withdraw":\n            self.send_message("<b>📤 Withdraw ETH</b>\\n\\nReply with: <code>/withdraw [ADDRESS] [AMOUNT]</code>\\n<i>Example: /withdraw 0x123... 0.5</i>\\n\\n<i>Tip: Use \\'all\\' as the amount to withdraw your entire balance.</i>", chat_id)',
     '        elif data == "menu_withdraw":\n            self.send_message("<b>📤 Withdraw ETH</b>\\n\\nReply with: <code>/withdraw [ADDRESS] [AMOUNT]</code>\\n<i>Example: /withdraw 0x123... 0.5</i>\\n\\n<i>Tip: Use \\'all\\' as the amount to withdraw your entire balance.</i>", chat_id, reply_markup={"inline_keyboard": [[{"text": "🔙 Back", "callback_data": "menu_back"}]]})'),
     
    ('        elif data == "menu_buy":\n            self.send_message("<b>🟢 Buy Token</b>\\n\\nReply with: <code>/buy [TOKEN_ADDRESS] [ETH_AMOUNT]</code>\\n<i>Example: /buy 0x123... 0.5</i>\\n\\n<i>🛡️ Every buy is automatically protected by the EVM Honeypot Simulator.</i>", chat_id)',
     '        elif data == "menu_buy":\n            self.send_message("<b>🟢 Buy Token</b>\\n\\nReply with: <code>/buy [TOKEN_ADDRESS] [ETH_AMOUNT]</code>\\n<i>Example: /buy 0x123... 0.5</i>\\n\\n<i>🛡️ Every buy is automatically protected by the EVM Honeypot Simulator.</i>", chat_id, reply_markup={"inline_keyboard": [[{"text": "🔙 Back", "callback_data": "menu_back"}]]})'),
     
    ('        elif data == "menu_scanner":\n            self.send_message("<b>🔍 Token Scanner</b>\\n\\nReply with: <code>/scan [TOKEN_ADDRESS]</code>\\n<i>Runs a full EVM simulation + honeypot + tax analysis on any token before you commit capital.</i>", chat_id)',
     '        elif data == "menu_scanner":\n            self.send_message("<b>🔍 Token Scanner</b>\\n\\nReply with: <code>/scan [TOKEN_ADDRESS]</code>\\n<i>Runs a full EVM simulation + honeypot + tax analysis on any token before you commit capital.</i>", chat_id, reply_markup={"inline_keyboard": [[{"text": "🔙 Back", "callback_data": "menu_back"}]]})'),
     
    ('        elif data == "menu_snipe":\n            self.send_message("<b>⚡ Mempool Sniper</b>\\n\\nReply with: <code>/snipe on [MAX_SPEND_ETH] [MIN_LIQUIDITY_ETH]</code>\\n<i>Example: /snipe on 0.05 1.0</i>\\n\\nOr disable with: <code>/snipe off</code>\\n\\n<i>🚀 Monitors the Base mempool for brand new token launches and buys in Block 0 before the chart even loads. EVM Shield is active on every snipe.</i>", chat_id)',
     '        elif data == "menu_snipe":\n            self.send_message("<b>⚡ Mempool Sniper</b>\\n\\nReply with: <code>/snipe on [MAX_SPEND_ETH] [MIN_LIQUIDITY_ETH]</code>\\n<i>Example: /snipe on 0.05 1.0</i>\\n\\nOr disable with: <code>/snipe off</code>\\n\\n<i>🚀 Monitors the Base mempool for brand new token launches and buys in Block 0 before the chart even loads. EVM Shield is active on every snipe.</i>", chat_id, reply_markup={"inline_keyboard": [[{"text": "🔙 Back", "callback_data": "menu_back"}]]})'),
     
    ('        elif data == "menu_copy":\n            self.send_message("<b>👥 Copy Trade (Vampire Mode)</b>\\n\\nReply with: <code>/copy [TARGET_ADDRESS] [MAX_SPEND_ETH]</code>\\n<i>Example: /copy 0x123... 0.1</i>\\n\\n<i>🦇 The bot will monitor this wallet in the mempool and front-run their buys so you get in cheaper!</i>", chat_id)',
     '        elif data == "menu_copy":\n            self.send_message("<b>👥 Copy Trade (Vampire Mode)</b>\\n\\nReply with: <code>/copy [TARGET_ADDRESS] [MAX_SPEND_ETH]</code>\\n<i>Example: /copy 0x123... 0.1</i>\\n\\n<i>🦇 The bot will monitor this wallet in the mempool and front-run their buys so you get in cheaper!</i>", chat_id, reply_markup={"inline_keyboard": [[{"text": "🔙 Back", "callback_data": "menu_back"}]]})')
]

for old, new in [
    ('        elif data == "menu_trenches":\n            self.send_message(\n                "<b>🕳️ Trenches Mode (Ultra-Degen)</b>\\n\\n"\n                "Auto-snipes micro-cap launches under your set market cap limit.\\n\\n"\n                "<code>/trenches on [MAX_ETH] [MAX_MCAP]</code>\\n"\n                "<i>Example: /trenches on 0.02 50000</i>\\n\\n"\n                "<code>/trenches off</code> to deactivate\\n\\n"\n                "⚠️ <b>WARNING:</b> High risk. EVM Shield always active.",\n                chat_id\n            )',
     '        elif data == "menu_trenches":\n            self.send_message(\n                "<b>🕳️ Trenches Mode (Ultra-Degen)</b>\\n\\n"\n                "Auto-snipes micro-cap launches under your set market cap limit.\\n\\n"\n                "<code>/trenches on [MAX_ETH] [MAX_MCAP]</code>\\n"\n                "<i>Example: /trenches on 0.02 50000</i>\\n\\n"\n                "<code>/trenches off</code> to deactivate\\n\\n"\n                "⚠️ <b>WARNING:</b> High risk. EVM Shield always active.",\n                chat_id,\n                reply_markup={"inline_keyboard": [[{"text": "🔙 Back", "callback_data": "menu_back"}]]}\n            )')
]:
    content = content.replace(old, new)

# Now add the handlers for the new quick-toggles we added to settings
quick_toggles = '''
        elif data == "cmd_antrug_on":
            self.handle_command("/antrug on", chat_id)
        elif data == "cmd_antrug_off":
            self.handle_command("/antrug off", chat_id)
        elif data == "cmd_snipe_on":
            self.handle_command("/snipe on 0.05 1.0", chat_id) # Default values
        elif data == "cmd_snipe_off":
            self.handle_command("/snipe off", chat_id)
        elif data == "cmd_trenches_on":
            self.handle_command("/trenches on 0.05 100000", chat_id) # Default values
        elif data == "cmd_trenches_off":
            self.handle_command("/trenches off", chat_id)
'''

content = content.replace('        elif data.startswith("menu_"):', quick_toggles + '        elif data.startswith("menu_"):')


with open('core/telegram_bot_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Sub-buttons upgraded!")
