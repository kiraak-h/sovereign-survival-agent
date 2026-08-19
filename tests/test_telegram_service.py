# sovereign-survival-agent/tests/test_telegram_service.py
"""
Test Suite for Two-Way Interactive Telegram Remote Control.
"""
import pytest
from core.models import AgentState
from core.metabolism import MetabolismManager
from core.telegram_bot_service import TelegramBotService


def test_telegram_bot_service_handles_vitals_command():
    state = AgentState(
        agent_address="0x3C187eC3757e1C76aAC4D83f97608b3cA3191FcA",
        session_key_address="0x97F88CA501AF4A75C9F8fd8C56d230a43e407134",
        treasury_usdc=45.50
    )
    metabolism = MetabolismManager(state)
    
    sent_messages = []

    class MockTelegramService(TelegramBotService):
        def send_message(self, text, chat_id=None):
            sent_messages.append(text)
            return True

    service = MockTelegramService(
        bot_token="test_token",
        allowed_chat_id="12345",
        metabolism=metabolism
    )

    service.handle_command("/vitals", "12345")
    assert len(sent_messages) == 1
    assert "Agent Vitals" in sent_messages[0]
    assert "45.5000" in sent_messages[0]


def test_telegram_bot_service_handles_help_command():
    sent_messages = []

    class MockTelegramService(TelegramBotService):
        def send_message(self, text, chat_id=None):
            sent_messages.append(text)
            return True

    service = MockTelegramService(bot_token="test_token", allowed_chat_id="12345")
    service.handle_command("/help", "12345")
    assert len(sent_messages) == 1
    assert "/vitals" in sent_messages[0]
    assert "/scan" in sent_messages[0]
