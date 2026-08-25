import sys

with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# We want to change send_message to automatically add a back button
# if reply_markup is None AND it's not a loading message (ends with '...')

old_send = '''    def send_message(
        self,
        text: str,
        chat_id: Optional[str] = None,
        reply_markup: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Sends an HTML formatted message with optional inline keyboard buttons."""
        cid = chat_id or self.allowed_chat_id
        if not self.token or not cid:
            return False
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            payload: Dict[str, Any] = {
                "chat_id": cid,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            if reply_markup:
                payload["reply_markup"] = reply_markup'''

new_send = '''    def send_message(
        self,
        text: str,
        chat_id: Optional[str] = None,
        reply_markup: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Sends an HTML formatted message with optional inline keyboard buttons."""
        cid = chat_id or self.allowed_chat_id
        if not self.token or not cid:
            return False
            
        # Automatically add a Back button if no keyboard is provided,
        # UNLESS the message is a temporary loading state (contains '...')
        if reply_markup is None and "..." not in text and "Sovereign Sniper · Base" not in text:
            reply_markup = {"inline_keyboard": [[{"text": "🔙 Back", "callback_data": "menu_back"}]]}
            
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            payload: Dict[str, Any] = {
                "chat_id": cid,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            if reply_markup:
                payload["reply_markup"] = reply_markup'''

content = content.replace(old_send, new_send)

with open('core/telegram_bot_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Injected global Back button into send_message")
