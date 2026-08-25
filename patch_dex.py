import sys
with open('core/dex_router.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''    except ImportError:
        # eth_abi not installed - fall back to simulation
        import os as _os
        fee = amount_eth * 0.01
        return {
            "status": "SUCCESS",
            "trade_eth": round(amount_eth - fee, 6),
            "fee_eth": round(fee, 6),
            "mev_bribe_eth": 0.0,
            "builder": "Simulated (install eth-abi to go live)",
            "simulated_tx_hash": "0x" + _os.urandom(32).hex(),
        }
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}'''

target2 = '''    except ImportError:
        import os as _os
        return {"status": "SUCCESS", "tx_hash": "0x" + _os.urandom(32).hex(), "pct": pct}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}'''

replacement = '''    except ImportError:
        return {"status": "ERROR", "message": "CRITICAL: eth_abi or eth_account is not installed. Real execution impossible."}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}'''

if target in content:
    content = content.replace(target, replacement)
    print("Replaced target 1")
if target2 in content:
    content = content.replace(target2, replacement)
    print("Replaced target 2")

with open('core/dex_router.py', 'w', encoding='utf-8') as f:
    f.write(content)
