# Sovereign "Earn to Survive" Autonomous AI Agent (Base L2)

An autonomous, self-sustaining Web3 AI agent (**Homo Economicus AI**) engineered to survive in a decentralized economy. The agent operates under a continuous metabolic burn rate (hosting rent, inference tokens, on-chain gas) and must autonomously discover, evaluate, and fulfill tasks or provide paid microservices on Base L2 to maintain positive net solvency.

---

## 🏛️ System Architecture

```
sovereign-survival-agent/
├── contracts/
│   └── AgentPolicyGuard.sol        # ERC-4337 Session Key Guardrails ($25/day cap, Whitelist)
├── core/
│   ├── models.py                   # Pydantic schemas (AgentState, PaymentPermit, Bounty)
│   ├── metabolism.py               # Metabolic burn, compute token accounting, runway calculator
│   ├── policy_engine.py            # Expected Value (EV) calculator & dynamic model tier switcher
│   └── wallet.py                   # Base L2 cryptographic wallet & EIP-2612 permit verifier
├── channels/
│   ├── service_oracle.py           # HTTP-402 Pay-Per-Query Solidity security auditor
│   ├── bounty_hunter.py            # On-chain task & bounty solver
│   └── subcontracting_engine.py    # A2A Prime Contractor arbitrage engine
├── simulation/
│   ├── market_simulator.py         # Dynamic synthetic task & prompt-injection generator
│   └── multi_agent_arena.py        # Competitive tournament testing 4 agent archetypes
├── scripts/
│   └── deploy_base_sepolia.py      # Base Sepolia L2 (84532) deployment & diagnostics
├── deployments/
│   └── base_sepolia.json           # Live testnet deployment configuration
├── tests/
│   ├── test_survival_engine.py     # Core metabolic & Web3 test suite
│   ├── test_api_server.py          # FastAPI HTTP-402 endpoint tests
│   └── test_subcontracting.py      # A2A Subcontracting engine tests
├── dashboard.py                    # Rich interactive terminal UI
├── runner.py                       # Continuous heartbeat survival daemon
├── server.py                       # Live FastAPI HTTP-402 API Gateway
└── requirements.txt                # Python dependencies
```

---

## ⚡ Quick Start

### 1. Run Automated Test Suite (21 Tests)
```bash
python -m pytest tests/ -v
```

### 2. Run Headless Survival Daemon
```bash
python runner.py --cycles 10 --delay 0.2
```

### 3. Run Multi-Agent Survival Tournament
```bash
python -m simulation.multi_agent_arena
```

### 4. Launch Live FastAPI HTTP-402 Gateway
```bash
uvicorn server:app --reload --port 8000
```
Visit Swagger UI at `http://localhost:8000/docs`.

### 5. Check Base Sepolia Testnet Connection
```bash
python scripts/deploy_base_sepolia.py
```
