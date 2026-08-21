# sovereign-survival-agent/tests/test_telegram_service.py
"""
Test Suite for Two-Way Interactive Telegram Remote Control & Mobile Cockpit.
"""
import pytest
from core.models import AgentState
from core.metabolism import MetabolismManager
from core.telegram_bot_service import TelegramBotService
from core.static_analyzer import RealSolidityStaticAnalyzer


def test_telegram_bot_service_handles_vitals_command():
    state = AgentState(
        agent_address="0x3C187eC3757e1C76aAC4D83f97608b3cA3191FcA",
        session_key_address="0x97F88CA501AF4A75C9F8fd8C56d230a43e407134",
        treasury_usdc=45.50
    )
    metabolism = MetabolismManager(state)
    sent_messages = []

    class MockTelegramService(TelegramBotService):
        def send_message(self, text, chat_id=None, reply_markup=None):
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
        def send_message(self, text, chat_id=None, reply_markup=None):
            sent_messages.append(text)
            return True

    service = MockTelegramService(bot_token="test_token", allowed_chat_id="12345")
    service.handle_command("/help", "12345")
    assert len(sent_messages) == 1
    assert "/vitals" in sent_messages[0]
    assert "/scan" in sent_messages[0]


def test_telegram_bot_service_handles_direct_solidity_audit():
    sent_messages = []

    class MockTelegramService(TelegramBotService):
        def send_message(self, text, chat_id=None, reply_markup=None):
            sent_messages.append(text)
            return True

    service = MockTelegramService(bot_token="test_token", allowed_chat_id="12345")
    sample_contract = """
    // SPDX-License-Identifier: MIT
    pragma solidity 0.8.20;
    contract Vault {
        mapping(address => uint256) public balances;
        function deposit() external payable { balances[msg.sender] += msg.value; }
    }
    """
    service.handle_command(sample_contract, "12345")
    assert len(sent_messages) >= 2
    assert "Smart Contract Security Report" in sent_messages[1]
    assert "Vault" in sent_messages[1]
    assert "100/100" in sent_messages[1]


def test_telegram_bot_service_sends_revenue_alert():
    sent_messages = []

    class MockTelegramService(TelegramBotService):
        def send_message(self, text, chat_id=None, reply_markup=None):
            sent_messages.append(text)
            return True

    service = MockTelegramService(bot_token="test_token", allowed_chat_id="12345")
    service.send_revenue_alert("Fix Reentrancy Vulnerability", 150.0, "0x1234567890abcdef")
    assert len(sent_messages) == 1
    assert "REVENUE CLAIMED" in sent_messages[0]
    assert "+$150.00 USDC" in sent_messages[0]
    assert "0x1234567890abcdef" in sent_messages[0]


def test_telegram_bot_service_handles_callback_query():
    sent_messages = []

    class MockTelegramService(TelegramBotService):
        def send_message(self, text, chat_id=None, reply_markup=None):
            sent_messages.append(text)
            return True

    service = MockTelegramService(bot_token="test_token", allowed_chat_id="12345")
    query = {
        "id": "q1",
        "data": "view_vitals",
        "message": {"chat": {"id": 12345}}
    }
    service._handle_callback_query(query)
    assert len(sent_messages) >= 1
