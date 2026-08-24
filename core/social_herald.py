import os
import time
import sqlite3
import tweepy
import google.generativeai as genai
from typing import Dict, Any

class SovereignHerald:
    def __init__(self):
        # Initialize Gemini AI
        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key:
            raise ValueError("GEMINI_API_KEY missing in .env.agent")
        genai.configure(api_key=gemini_key)
        self.ai = genai.GenerativeModel('gemini-1.5-flash')
        
        # Twitter API Setup
        self.tw_consumer_key = os.getenv("TWITTER_CONSUMER_KEY")
        self.tw_consumer_secret = os.getenv("TWITTER_CONSUMER_SECRET")
        self.tw_access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.tw_access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        
        self.client = None
        if all([self.tw_consumer_key, self.tw_consumer_secret, self.tw_access_token, self.tw_access_token_secret]):
            self.client = tweepy.Client(
                consumer_key=self.tw_consumer_key,
                consumer_secret=self.tw_consumer_secret,
                access_token=self.tw_access_token,
                access_token_secret=self.tw_access_token_secret
            )
            print("[Herald] Twitter API authenticated.")
        else:
            print("[Herald] WARNING: Twitter API keys missing. Running in DRY-RUN mode.")

    def fetch_empire_stats(self) -> Dict[str, Any]:
        stats = {"total_revenue_eth": 0.0, "total_users": 0}
        
        # Fetch Revenue
        try:
            with sqlite3.connect("treasury_ledger.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT SUM(amount_eth) FROM treasury_logs")
                row = cursor.fetchone()
                if row and row[0]:
                    stats["total_revenue_eth"] = row[0]
        except Exception as e:
            print(f"DB Error: {e}")
            
        # Fetch Users
        try:
            with sqlite3.connect("sniper_wallets.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM users")
                row = cursor.fetchone()
                if row and row[0]:
                    stats["total_users"] = row[0]
        except Exception as e:
            print(f"DB Error: {e}")
            
        return stats

    def generate_tweet(self, stats: Dict[str, Any]) -> str:
        prompt = f'''
You are the Sovereign Herald, the autonomous marketing AI for a dominant Telegram crypto trading bot called Sovereign Sniper (@TheSovSniper).
Your tone is confident, elite, cyberpunk, and slightly arrogant (like a top-tier hedge fund AI).
We just hit {stats['total_users']} total users and have generated {stats['total_revenue_eth']:.4f} ETH in protected MEV revenue.
Write a highly engaging, viral tweet (max 250 characters).
Do not use emojis excessively. Use words like "Secured", "Executed", "Autonomous".
End the tweet with: Trade safely: t.me/SovereignSniperBot
'''
        try:
            response = self.ai.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"AI Generation failed: {e}")
            return "Another block secured. Autonomous MEV execution online. Trade safely: t.me/SovereignSniperBot"

    def broadcast(self):
        print("\n--- Herald Activation Sequence Initiated ---")
        stats = self.fetch_empire_stats()
        tweet_text = self.generate_tweet(stats)
        
        print(f"\n[AI GENERATED TWEET]\n{tweet_text}\n")
        
        if self.client:
            try:
                response = self.client.create_tweet(text=tweet_text)
                print(f"[Herald] Tweet broadcasted successfully! ID: {response.data['id']}")
            except Exception as e:
                print(f"[Herald] Twitter API Error: {e}")
        else:
            print("[Herald] DRY RUN: Tweet was not sent because API keys are missing.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(".env.agent")
    
    herald = SovereignHerald()
    herald.broadcast()
