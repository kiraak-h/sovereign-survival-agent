        elif data == "menu_trenches":
            latest_tokens = []
            try:
                import urllib.request, json, ssl
                from datetime import datetime
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                
                req = urllib.request.Request('https://api.geckoterminal.com/api/v2/networks/base/new_pools', headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
                with urllib.request.urlopen(req, context=ctx, timeout=5) as r:
                    res_data = json.loads(r.read())
                    pools = res_data.get('data', [])[:5]
                    
                tokens_list = []
                for p in pools:
                    attrs = p.get('attributes', {})
                    name = attrs.get('name', 'Unknown').split(' / ')[0]
                    fdv = float(attrs.get('fdv_usd') or 0)
                    liq = float(attrs.get('reserve_in_usd') or 0)
                    
                    chg_dict = attrs.get('price_change_percentage') or {}
                    chg = float(chg_dict.get('m5') or chg_dict.get('m15') or 0)
                    
                    created_at = attrs.get('pool_created_at', '')
                    age_mins = 0
                    if created_at:
                        try:
                            # 2026-08-25T15:17:23Z
                            created_dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
                            age_mins = int((datetime.utcnow() - created_dt).total_seconds() / 60)
                        except: pass

                    base_token_id = p.get('relationships', {}).get('base_token', {}).get('data', {}).get('id', '')
                    token_addr = base_token_id.replace('base_', '')
                    if token_addr:
                        tokens_list.append(token_addr)
                        latest_tokens.append({'name': name, 'address': token_addr, 'fdv': fdv, 'liq': liq, 'chg': chg, 'safe': True, 'age': age_mins})
                        
                # Batch GoPlus Security Scan
                if tokens_list:
                    g_url = f"https://api.gopluslabs.io/api/v1/token_security/8453?contract_addresses={','.join(tokens_list)}"
                    g_req = urllib.request.Request(g_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(g_req, context=ctx, timeout=5) as gr:
                        g_data = json.loads(gr.read()).get('result', {})
                        
                    for t in latest_tokens:
                        res = g_data.get(t['address'].lower(), {})
                        hp = res.get('is_honeypot') == '1' or res.get('cannot_sell_all') == '1'
                        t['safe'] = not hp
            except Exception as e:
                print("Live Menu Error:", e)

            inline_kb = []
            msg_text = "<b>☢️ Trenches: Live Base Launches</b>\n\n"
            
            if latest_tokens:
                msg_text += "<i>Latest tokens detected on-chain:</i>\n\n"
                for t in latest_tokens:
                    safe_icon = "🟢" if t['safe'] else "🔴"
                    chg_icon = "+" if t['chg'] >= 0 else ""
                    msg_text += f"{safe_icon} <b><a href='https://dexscreener.com/base/{t['address']}'>{t['name']}</a></b> (Age: {t['age']}m)\n"
                    msg_text += f"<code>{t['address']}</code>\n"
                    msg_text += f"💧 Liq: <b></b> | 📈 MCAP: <b></b> | 5m: {chg_icon}{t['chg']:.1f}%\n\n"
                    
                    if t['safe']:
                        cb_data = f"tsnipe_{t['address']}"
                        inline_kb.append([{"text": f"🔫 1-Click Snipe 0.02 ETH", "callback_data": cb_data[:64]}])
            else:
                msg_text += "<i>No new tokens found right now.</i>\n\n"

            msg_text += (
                "<b>Auto-Sniper:</b>\n"
                "<code>/trenches on [MAX_ETH] [MAX_MCAP]</code>\n"
                "<i>Example: /trenches on 0.02 50000</i>\n"
            )

            inline_kb.append([{"text": "🔄 Refresh Live Data", "callback_data": "menu_trenches"}])
            inline_kb.append([{"text": "☢️ Trenches ON", "callback_data": "cmd_trenches_on"}, {"text": "☢️ Trenches OFF", "callback_data": "cmd_trenches_off"}])
            inline_kb.append([{"text": "⬅️ Back", "callback_data": "menu_back"}])

            keyboard = {"inline_keyboard": inline_kb}
            self.send_message(msg_text, chat_id, reply_markup=keyboard)
