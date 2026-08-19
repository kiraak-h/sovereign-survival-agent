# sovereign-survival-agent/scripts/test_credentials.py
"""
Live Credentials & Notifications Tester:
Validates GitHub API access, Telegram Bot connectivity, and Discord Webhooks.
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv(".env.agent")

print("=" * 60)
print("=== TESTING SOVEREIGN AGENT CREDENTIALS & ALERTS ===")
print("=" * 60)

# 1. Test GitHub Token
gh_token = os.getenv("GITHUB_TOKEN")
if gh_token:
    print("\n[*] Testing GitHub API Token...")
    res = requests.get("https://api.github.com/user", headers={
        "Authorization": f"Bearer {gh_token}",
        "Accept": "application/vnd.github+json"
    })
    if res.status_code == 200:
        user_data = res.json()
        print(f"    [+] GitHub Authenticated as: @{user_data.get('login')} ({user_data.get('name')})")
        print("    [+] Remote PR Dispatch: ENABLED (Agent can open live pull requests)")
    else:
        print(f"    [!] GitHub Token Invalid (HTTP {res.status_code}): {res.text[:150]}")
else:
    print("\n[-] GITHUB_TOKEN: Not set (Running in 1-Click Draft Preview mode)")

# 2. Test Telegram Bot
tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
tg_chat_id = os.getenv("TELEGRAM_CHAT_ID")
if tg_token and tg_chat_id:
    print("\n[*] Testing Telegram Bot Alert...")
    url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
    payload = {
        "chat_id": tg_chat_id,
        "text": "<b>[TEST] Sovereign AI Agent Connected!</b>\n\nYour mobile alert channel is active.",
        "parse_mode": "HTML"
    }
    try:
        res = requests.post(url, json=payload, timeout=5)
        if res.status_code == 200:
            print("    [+] Telegram Alert Sent Successfully! (Check your phone)")
        else:
            print(f"    [!] Telegram Error (HTTP {res.status_code}): {res.text[:150]}")
    except Exception as e:
        print(f"    [!] Telegram Connection Error: {e}")
else:
    print("\n[-] TELEGRAM: Not configured")

# 3. Test Discord Webhook
discord_url = os.getenv("DISCORD_WEBHOOK_URL")
if discord_url:
    print("\n[*] Testing Discord Webhook...")
    payload = {
        "embeds": [{
            "title": "🧬 Sovereign AI Agent Connected!",
            "description": "Discord notification channel is active and receiving alerts.",
            "color": 0x00FF00
        }]
    }
    try:
        res = requests.post(discord_url, json=payload, timeout=5)
        if res.status_code in (200, 204):
            print("    [+] Discord Notification Sent Successfully!")
        else:
            print(f"    [!] Discord Webhook Error (HTTP {res.status_code})")
    except Exception as e:
        print(f"    [!] Discord Connection Error: {e}")
else:
    print("\n[-] DISCORD_WEBHOOK_URL: Not configured")

# 4. Test Gemini / OpenAI API Keys
gemini_key = os.getenv("GEMINI_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")
print("\n[*] AI Reasoning Engines:")
print(f"    - GEMINI_API_KEY: {'[+] Configured' if gemini_key else '[-] Using Heuristics / Local Fallback'}")
print(f"    - OPENAI_API_KEY: {'[+] Configured' if openai_key else '[-] None'}")

print("\n" + "=" * 60)
print("Credential check complete.")
print("=" * 60)
