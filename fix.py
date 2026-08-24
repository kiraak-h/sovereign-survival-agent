import sys

with open("C:/Users/ameer/.gemini/antigravity/brain/e4cf8fe6-2689-4106-af84-2a114e28e2e3/scratch/fixer.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('end_sig = "    def _handle_wallet(self, cmd_text: str, chat_id: str):"', 'end_sig = "    def _handle_wallet(self, chat_id: str):"')

with open("C:/Users/ameer/.gemini/antigravity/brain/e4cf8fe6-2689-4106-af84-2a114e28e2e3/scratch/fixer.py", "w", encoding="utf-8") as f:
    f.write(content)
