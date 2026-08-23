# Project Memory: Sovereign Survival Agent

## Context
This project is an autonomous Web3 smart contract security auditor agent operating on Base L2. 
It possesses two primary revenue channels:
1. **Web2 CI/CD (GitHub Actions)**: Developers buy $50 prepaid API keys using USDC on-chain. The backend (/v1/keys/generate) verifies the transaction hash.
2. **Web3 M2M (A2A API)**: Autonomous trading bots pay $0.25 USDC per audit using EIP-2612 signatures natively. The official Python SDK is sovereign-oracle (published to PyPI).

## Architectural Decisions
- **Strict Separation of Concerns**: This repository (sovereign-survival-agent) must NEVER interact with or mention the SaaS project repository. They are entirely disconnected.
- **On-Chain Verification vs Mocks**: The API key generation was previously a mock. It is now cryptographically secured using web3.py to verify transaction receipts against the official Base USDC contract.
- **EIP-712 over EIP-191**: Machine-to-machine micropayments use th_account.messages.encode_typed_data to construct EIP-712 structured data that perfectly matches the USDC Base Mainnet DOMAIN_SEPARATOR. This ensures the collected PaymentPermit signatures can be successfully executed on-chain.

## Burn Book (Failed Approaches)
- **Failure**: Returning 
ull from the A2A API endpoint.
  - **Reason**: The eturn res_data statement was accidentally deleted during a refactor. Always ensure endpoints return the processed payload.
- **Failure**: Using ncode_defunct for EIP-2612 permits in wallet.py.
  - **Reason**: The USDC contract requires strict EIP-712 structured data. Text hashes (ncode_defunct) will result in signature mismatch errors on-chain.

## Active Scratchpad
- Phase 1 (Web2 Developer Monetization) is complete and live on GitHub Marketplace.
- Phase 2 (M2M Trading Bot Plugin) is complete and published to PyPI (sovereign-oracle).
- **Next Steps**: Monitor incoming traffic, deploy the daemon to claim the collected EIP-2612 permits on-chain, or move to Phase 3 (if applicable).
