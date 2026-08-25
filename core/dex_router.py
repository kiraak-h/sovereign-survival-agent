    except ImportError:
        return {"status": "ERROR", "message": "CRITICAL: eth_abi or eth_account is not installed. Real execution impossible."}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}


def execute_withdrawal(private_key: str, destination: str, amount) -> dict:
    """
    Sends real ETH from the bot wallet to a destination address via Alchemy.
    amount can be a float (ETH) or 'all' to send max balance minus gas.
    """
    try:
        from eth_account import Account
        account = Account.from_key(private_key)
        sender = account.address

        gas_price = _get_gas_price()
        gas_limit = 21000
        gas_cost_wei = gas_price * gas_limit
        chain_id = 8453

        # Fetch live balance
        bal_resp = _rpc("eth_getBalance", [sender, "latest"])
        balance_wei = int(bal_resp.get("result", "0x0"), 16)

        if amount == "all":
            send_wei = balance_wei - gas_cost_wei - int(0.0001 * 1e18)  # keep dust
        else:
            send_wei = int(float(amount) * 1e18)

        if send_wei <= 0:
            return {"status": "ERROR", "message": "Insufficient balance to cover gas."}

        nonce = _get_nonce(sender)
        tx = {
            "chainId": chain_id,
            "to": destination,
            "value": send_wei,
            "gas": gas_limit,
            "gasPrice": gas_price,
            "nonce": nonce,
            "data": "0x",
        }

        signed = account.sign_transaction(tx)
        resp = _rpc("eth_sendRawTransaction", ["0x" + signed.raw_transaction.hex()])

        if "result" in resp:
            return {
                "status": "SUCCESS",
                "amount": round(send_wei / 1e18, 6),
                "tx_hash": resp["result"],
            }
        else:
            return {"status": "ERROR", "message": resp.get("error", {}).get("message", "RPC error")}

    except Exception as e:
        return {"status": "ERROR", "message": str(e)}


def execute_partial_sell(private_key: str, token: str, pct: int) -> dict:
    """
    Sells a percentage of an ERC-20 token bag.
    Reads current balance, calculates pct%, and executes swapExactTokensForETH.
    """
    try:
        from eth_account import Account
        import eth_abi

        account = Account.from_key(private_key)
        sender = account.address
        chain_id = 8453

        # Get current token balance via Alchemy
        selector_bal = bytes.fromhex("70a08231")
        padded = bytes.fromhex("000000000000000000000000" + sender[2:])
        call_data = "0x" + (selector_bal + padded).hex()

        bal_resp = _rpc("eth_call", [{"to": token, "data": call_data}, "latest"])
        raw_balance = int(bal_resp.get("result", "0x0"), 16)

        if raw_balance == 0:
            return {"status": "ERROR", "message": "Zero token balance."}

        sell_amount = int(raw_balance * pct / 100)

        # Build approve + swapExactTokensForETH
        # approve(router, sell_amount)
        approve_selector = bytes.fromhex("095ea7b3")
        approve_data = "0x" + (approve_selector + eth_abi.encode(["address", "uint256"], [UNISWAP_V2_ROUTER, sell_amount])).hex()

        gas_price = _get_gas_price()
        nonce = _get_nonce(sender)

        approve_tx = {
            "chainId": chain_id, "to": token,
            "value": 0, "gas": 100000,
            "gasPrice": gas_price, "nonce": nonce,
            "data": approve_data,
        }
        signed_approve = account.sign_transaction(approve_tx)
        _rpc("eth_sendRawTransaction", ["0x" + signed_approve.raw_transaction.hex()])

        # swapExactTokensForETH(amountIn, amountOutMin, path, to, deadline)
        deadline = int(time.time()) + 120
        path = [token, WETH_BASE]
        swap_selector = bytes.fromhex("18cbafe5")
        swap_data = "0x" + (swap_selector + eth_abi.encode(
            ["uint256", "uint256", "address[]", "address", "uint256"],
            [sell_amount, 0, path, sender, deadline]
        )).hex()

        swap_tx = {
            "chainId": chain_id, "to": UNISWAP_V2_ROUTER,
            "value": 0, "gas": 300000,
            "gasPrice": gas_price, "nonce": nonce + 1,
            "data": swap_data,
        }
        signed_swap = account.sign_transaction(swap_tx)
        resp = _rpc("eth_sendRawTransaction", ["0x" + signed_swap.raw_transaction.hex()])

        if "result" in resp:
            return {"status": "SUCCESS", "tx_hash": resp["result"], "pct": pct}
        else:
            return {"status": "ERROR", "message": resp.get("error", {}).get("message", "Sell failed")}

    except ImportError:
        return {"status": "ERROR", "message": "CRITICAL: eth_abi or eth_account is not installed. Real execution impossible."}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}


def get_portfolio_positions(address: str, known_tokens: list = None) -> list:
    """Delegates to the Alchemy-powered portfolio engine."""
    from core.portfolio import get_portfolio_positions as _real
    return _real(address, known_tokens)


def execute_sell(private_key: str, token_address: str, percentage: float = 100.0) -> dict:
    """Alias used by limit_engine: sells a percentage of a token bag."""
    pct = int(percentage)
    return execute_partial_sell(private_key, token_address, pct)



