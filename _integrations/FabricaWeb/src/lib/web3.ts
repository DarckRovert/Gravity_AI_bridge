// Web3Modal — Lazy-loaded to avoid Turbopack build errors
// These packages are only loaded at runtime when the user clicks "Connect Wallet"

export interface WalletState {
    address: string | null;
    balance: string | null;
    chainId: number | null;
    isConnected: boolean;
}

// 🍬 $DULCE Token Contract Address (Placeholder - Polygon Amoy Testnet)
export const DULCE_TOKEN_ADDRESS = "0x0000000000000000000000000000000000000000";

// 📜 ABI Minimalista (ERC-20 Standard + Mint)
export const DULCE_ABI = [
    "function name() view returns (string)",
    "function symbol() view returns (string)",
    "function balanceOf(address) view returns (uint)",
    "function transfer(address to, uint amount)",
    "function mint(address to, uint amount)", // Solo Owner/Minter
    "event Transfer(address indexed from, address indexed to, uint amount)"
];

// Lazy-initialized Web3Modal instance
let web3ModalInstance: ReturnType<typeof import('@web3modal/ethers/react')['createWeb3Modal']> | null = null;

async function getWeb3Modal() {
    if (web3ModalInstance) return web3ModalInstance;

    // Try importing from the root package to avoid problematic sub-dependencies
    const { createWeb3Modal, defaultConfig } = await import('@web3modal/ethers');

    const projectId = process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID || 'YOUR_PROJECT_ID';

    const amoy = {
        chainId: 80002,
        name: 'Polygon Amoy',
        currency: 'MATIC',
        explorerUrl: 'https://amoy.polygonscan.com',
        rpcUrl: 'https://rpc-amoy.polygon.technology'
    };

    const metadata = {
        name: 'Pastelito Next',
        description: 'Pastelería Web3 & AI',
        url: typeof window !== 'undefined' ? window.location.origin : 'https://pastelito.app',
        icons: ['https://pastelito.app/logo.png']
    };

    web3ModalInstance = createWeb3Modal({
        ethersConfig: defaultConfig({ metadata }),
        chains: [amoy],
        projectId,
        enableAnalytics: true
    });

    return web3ModalInstance;
}

export const connectWallet = async (): Promise<WalletState> => {
    const modal = await getWeb3Modal();
    if (!modal) throw new Error('Web3Modal failed to initialize');

    await modal.open();

    return new Promise((resolve) => {
        const check = setInterval(() => {
            const state = modal.getAddress();
            if (state) {
                clearInterval(check);
                resolve({
                    address: state,
                    balance: "0.00",
                    chainId: 80002,
                    isConnected: true
                });
            }
        }, 500);

        // Timeout 60s
        setTimeout(() => { clearInterval(check); }, 60000);
    });
};
