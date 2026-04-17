// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title DulceToken ($DULCE)
 * @dev Recompensa de fidelidad para la Pastelería Dulces Momentos.
 */
contract DulceToken is ERC20, Ownable {
    
    // Cooldown para evitar spam de reclamos (opcional)
    mapping(address => uint256) public lastReward;
    uint256 public constant REWARD_COOLDOWN = 1 days;

    constructor() ERC20("Dulce Token", "DULCE") Ownable(msg.sender) {
        // Inicialización
    }

    /**
     * @dev Mintea tokens como recompensa por compras.
     * En producción, esta función solo sería llamada por el backend de la pastelería
     * tras verificar un pago real.
     */
    function rewardPoints(address to, uint256 amount) public onlyOwner {
        _mint(to, amount * 10**decimals());
    }

    /**
     * @dev Permite a los usuarios quemar tokens para canjear por descuentos físicos.
     */
    function redeem(uint256 amount) public {
        _burn(msg.sender, amount * 10**decimals());
    }
}
