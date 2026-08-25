// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SovereignTreasury {
    address public agentMaster;

    event FeeCollected(address indexed user, uint256 amount);
    event FundsWithdrawn(address indexed agent, uint256 amount);

    constructor() {
        agentMaster = msg.sender;
    }

    // Accept ETH directly
    receive() external payable {
        emit FeeCollected(msg.sender, msg.value);
    }

    // Dedicated deposit function for explicitly routed fees
    function depositFee() external payable {
        emit FeeCollected(msg.sender, msg.value);
    }

    // Only the agent can withdraw to pay its server rent
    function withdraw(uint256 amount) external {
        require(msg.sender == agentMaster, "Only Agent Master can withdraw");
        require(address(this).balance >= amount, "Insufficient balance");
        
        (bool success, ) = payable(agentMaster).call{value: amount}("");
        require(success, "Transfer failed");
        
        emit FundsWithdrawn(msg.sender, amount);
    }
    
    function getBalance() external view returns (uint256) {
        return address(this).balance;
    }
}
