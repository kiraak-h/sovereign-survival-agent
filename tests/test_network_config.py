# sovereign-survival-agent/tests/test_network_config.py
"""
Test Suite for Base L2 Network Configuration.
"""
import pytest
from core.network_config import get_active_network, NETWORKS, NetworkMode


def test_network_config_returns_base_sepolia_when_configured(monkeypatch):
    monkeypatch.setenv("NETWORK_MODE", "BASE_SEPOLIA")
    net = get_active_network()
    assert net.chain_id == 84532
    assert "Sepolia" in net.name
    assert net.is_production is False


def test_network_config_returns_base_mainnet_when_configured(monkeypatch):
    monkeypatch.setenv("NETWORK_MODE", "BASE_MAINNET")
    net = get_active_network()
    assert net.chain_id == 8453
    assert "Mainnet" in net.name
    assert net.is_production is True


def test_network_config_defines_base_mainnet_specs():
    mainnet = NETWORKS[NetworkMode.BASE_MAINNET]
    assert mainnet.chain_id == 8453
    assert mainnet.usdc_address == "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    assert mainnet.is_production is True
