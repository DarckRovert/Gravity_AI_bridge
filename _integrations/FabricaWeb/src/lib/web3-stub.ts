// Stub for @web3modal/ethers/react during Turbopack build
// The real module is loaded dynamically at runtime via import() in web3.ts
// This file exists solely to satisfy the Turbopack resolver

export function createWeb3Modal() {
    throw new Error('Web3Modal must be loaded dynamically at runtime');
}

export function defaultConfig() {
    return {};
}
