# agent/tests/test_api_server.py
"""
Test Suite for Sovereign Agent HTTP-402 FastAPI Gateway.
"""
import pytest
from fastapi.testclient import TestClient
from eth_account import Account
from server import app, _agent_state, _wallet, _policy, _oracle


client = TestClient(app)


def test_get_agent_vitals():
    response = client.get("/v1/agent/vitals")
    assert response.status_code == 200
    data = response.json()
    assert "treasury_usdc" in data
    assert "runway_hours" in data
    assert "is_alive" in data
    assert data["is_alive"] is True


def test_get_service_pricing():
    response = client.get("/v1/agent/pricing")
    assert response.status_code == 200
    data = response.json()
    assert "current_effective_fee_usdc" in data
    assert "USDC" in data["accepted_token"]


def test_audit_endpoint_rejects_unpaid_request():
    payload = {
        "code": "contract Test {}",
        "payer_address": "0x1234567890123456789012345678901234567890",
        "payment_permit": {
            "payer_address": "0x1234567890123456789012345678901234567890",
            "token_address": "0x036cbd53842c5426634e7929541ec2318f3dcf7e",
            "amount_usdc": 0.01,  # Insufficient amount
            "nonce": 1,
            "deadline": 9999999999,
            "signature": "0xdeadbeef"
        }
    }
    response = client.post("/v1/audit/smart-contract", json=payload)
    assert response.status_code == 402
    assert "error" in response.json()


def test_audit_endpoint_processes_valid_paid_request():
    test_user = Account.create()
    required_fee = _policy.get_dynamic_service_fee(_oracle.base_audit_fee_usdc)

    permit = _wallet.create_mock_payment_permit(
        payer_key=test_user.key.hex(),
        amount_usdc=required_fee
    )

    payload = {
        "code": """
        contract Vault {
            mapping(address => uint256) public balances;
            function withdraw() public {
                (bool s, ) = msg.sender.call{value: 1 ether}("");
                require(s);
                balances[msg.sender] = 0;
            }
        }
        """,
        "payer_address": test_user.address,
        "payment_permit": permit.model_dump(mode="json")
    }

    response = client.post("/v1/audit/smart-contract", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["result"]["status"] == "VULNERABLE"
    assert data["fee_charged_usdc"] == required_fee
