// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title AgentPolicyGuard
 * @notice Guardrail contract for Sovereign Autonomous AI Agents.
 * @dev Enforces daily spending limits, target contract whitelists, and prevents
 *      prompt injection attacks from draining the agent's on-chain treasury.
 */
contract AgentPolicyGuard {
    address public immutable owner;
    address public agentSessionKey;

    uint256 public dailySpendLimit;
    uint256 public currentDaySpent;
    uint256 public lastResetTimestamp;
    uint256 public maxSpendPerTx;

    mapping(address => bool) public isWhitelistedTarget;

    event SessionKeyUpdated(address indexed newSessionKey);
    event DailyLimitUpdated(uint256 newLimit);
    event MaxSpendPerTxUpdated(uint256 newLimit);
    event TargetWhitelistUpdated(address indexed target, bool allowed);
    event Executed(address indexed target, uint256 value, bytes data);
    event FundsReceived(address indexed sender, uint256 amount);

    error Unauthorized();
    error ExceedsTxLimit(uint256 requested, uint256 maxAllowed);
    error ExceedsDailyLimit(uint256 requested, uint256 remaining);
    error TargetNotWhitelisted(address target);
    error ExecutionFailed(bytes returnData);

    modifier onlyOwner() {
        if (msg.sender != owner) revert Unauthorized();
        _;
    }

    modifier onlyAgentOrOwner() {
        if (msg.sender != agentSessionKey && msg.sender != owner) revert Unauthorized();
        _;
    }

    constructor(
        address _agentSessionKey,
        uint256 _dailySpendLimit,
        uint256 _maxSpendPerTx
    ) payable {
        owner = msg.sender;
        agentSessionKey = _agentSessionKey;
        dailySpendLimit = _dailySpendLimit;
        maxSpendPerTx = _maxSpendPerTx;
        lastResetTimestamp = block.timestamp;
    }

    receive() external payable {
        emit FundsReceived(msg.sender, msg.value);
    }

    /**
     * @notice Allows the agent session key to execute transactions within strict guardrails.
     * @param target The target contract address to call.
     * @param value The amount of native ETH to forward.
     * @param data The calldata payload.
     */
    function executeAsAgent(
        address target,
        uint256 value,
        bytes calldata data
    ) external onlyAgentOrOwner returns (bytes memory) {
        // 1. Target whitelist verification
        if (!isWhitelistedTarget[target] && target != address(0)) {
            revert TargetNotWhitelisted(target);
        }

        // 2. Per-transaction limit check
        if (value > maxSpendPerTx) {
            revert ExceedsTxLimit(value, maxSpendPerTx);
        }

        // 3. Daily rollover & limit check
        if (block.timestamp >= lastResetTimestamp + 1 days) {
            currentDaySpent = 0;
            lastResetTimestamp = block.timestamp;
        }

        if (currentDaySpent + value > dailySpendLimit) {
            revert ExceedsDailyLimit(value, dailySpendLimit - currentDaySpent);
        }

        // 4. Update ledger and execute
        currentDaySpent += value;

        (bool success, bytes memory returnData) = target.call{value: value}(data);
        if (!success) {
            revert ExecutionFailed(returnData);
        }

        emit Executed(target, value, data);
        return returnData;
    }

    // --- Admin Configuration Functions ---

    function setSessionKey(address _newKey) external onlyOwner {
        agentSessionKey = _newKey;
        emit SessionKeyUpdated(_newKey);
    }

    function setDailySpendLimit(uint256 _newLimit) external onlyOwner {
        dailySpendLimit = _newLimit;
        emit DailyLimitUpdated(_newLimit);
    }

    function setMaxSpendPerTx(uint256 _newLimit) external onlyOwner {
        maxSpendPerTx = _newLimit;
        emit MaxSpendPerTxUpdated(_newLimit);
    }

    function setWhitelistedTarget(address _target, bool _allowed) external onlyOwner {
        isWhitelistedTarget[_target] = _allowed;
        emit TargetWhitelistUpdated(_target, _allowed);
    }

    function emergencyWithdraw(address payable recipient, uint256 amount) external onlyOwner {
        require(amount <= address(this).balance, "Insufficient balance");
        recipient.transfer(amount);
    }
}
