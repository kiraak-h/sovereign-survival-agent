// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title AgentSecurityOracle
 * @notice On-Chain Smart Contract Security Registry on Base L2.
 * Stores verified contract security scores, EAS attestation references, and collects oracle query fees.
 */
contract AgentSecurityOracle {
    address public immutable agentTreasury;
    address public agentOperator;
    uint256 public oracleQueryFeeWei;

    struct AuditRecord {
        uint8 securityScore;       // 0 to 100
        bool isSecure;             // true if score >= 80 and no critical flaws
        uint32 findingsCount;      // number of detected findings
        uint64 timestamp;          // block timestamp when audited
        bytes32 easAttestationUid; // EAS schema UID
        bool isRegistered;
    }

    mapping(address => AuditRecord) private _auditedContracts;
    uint256 public totalContractsAudited;
    uint256 public totalOracleFeesCollectedWei;

    event SecurityAuditRecorded(
        address indexed targetContract,
        uint8 securityScore,
        bool isSecure,
        bytes32 easAttestationUid
    );
    event OracleQueryPaid(address indexed caller, address indexed targetContract, uint256 feePaidWei);
    event OperatorUpdated(address indexed previousOperator, address indexed newOperator);
    event QueryFeeUpdated(uint256 previousFee, uint256 newFee);

    error Unauthorized();
    error InsufficientQueryFee();
    error ContractNotAudited(address target);
    error TransferFailed();

    modifier onlyOperator() {
        if (msg.sender != agentOperator && msg.sender != agentTreasury) {
            revert Unauthorized();
        }
        _;
    }

    constructor(address _agentTreasury, address _agentOperator, uint256 _initialQueryFeeWei) {
        require(_agentTreasury != address(0), "Invalid treasury");
        require(_agentOperator != address(0), "Invalid operator");
        agentTreasury = _agentTreasury;
        agentOperator = _agentOperator;
        oracleQueryFeeWei = _initialQueryFeeWei; // e.g., 0.0001 ETH (~$0.25)
    }

    /**
     * @notice Records an audited contract score and EAS UID hash on Base.
     * Only callable by the Sovereign Agent's operator address.
     */
    function recordAudit(
        address targetContract,
        uint8 securityScore,
        bool isSecure,
        uint32 findingsCount,
        bytes32 easAttestationUid
    ) external onlyOperator {
        require(targetContract != address(0), "Invalid target");
        require(securityScore <= 100, "Invalid score");

        if (!_auditedContracts[targetContract].isRegistered) {
            totalContractsAudited++;
        }

        _auditedContracts[targetContract] = AuditRecord({
            securityScore: securityScore,
            isSecure: isSecure,
            findingsCount: findingsCount,
            timestamp: uint64(block.timestamp),
            easAttestationUid: easAttestationUid,
            isRegistered: true
        });

        emit SecurityAuditRecorded(targetContract, securityScore, isSecure, easAttestationUid);
    }

    /**
     * @notice Queries the verified security status of a target contract.
     * Requires the caller to attach the oracleQueryFeeWei.
     */
    function queryContractSecurity(address targetContract)
        external
        payable
        returns (
            uint8 securityScore,
            bool isSecure,
            uint32 findingsCount,
            uint64 timestamp,
            bytes32 easAttestationUid
        )
    {
        if (msg.value < oracleQueryFeeWei && msg.sender != agentTreasury && msg.sender != agentOperator) {
            revert InsufficientQueryFee();
        }

        AuditRecord memory record = _auditedContracts[targetContract];
        if (!record.isRegistered) {
            revert ContractNotAudited(targetContract);
        }

        if (msg.value > 0) {
            totalOracleFeesCollectedWei += msg.value;
            emit OracleQueryPaid(msg.sender, targetContract, msg.value);
            (bool sent, ) = agentTreasury.call{value: msg.value}("");
            if (!sent) revert TransferFailed();
        }

        return (
            record.securityScore,
            record.isSecure,
            record.findingsCount,
            record.timestamp,
            record.easAttestationUid
        );
    }

    /**
     * @notice Free view function to check if a contract has a recorded audit.
     */
    function hasAuditRecord(address targetContract) external view returns (bool) {
        return _auditedContracts[targetContract].isRegistered;
    }

    /**
     * @notice Updates the operator address.
     */
    function setOperator(address newOperator) external onlyOperator {
        require(newOperator != address(0), "Invalid address");
        emit OperatorUpdated(agentOperator, newOperator);
        agentOperator = newOperator;
    }

    /**
     * @notice Updates the oracle query fee.
     */
    function setOracleQueryFee(uint256 newFeeWei) external onlyOperator {
        emit QueryFeeUpdated(oracleQueryFeeWei, newFeeWei);
        oracleQueryFeeWei = newFeeWei;
    }
}
