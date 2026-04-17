// Type declarations for modules without TypeScript definitions

declare module '@web3modal/ethers/react' {
    export function createWeb3Modal(config: {
        ethersConfig: ReturnType<typeof defaultConfig>;
        chains: Array<{
            chainId: number;
            name: string;
            currency: string;
            explorerUrl: string;
            rpcUrl: string;
        }>;
        projectId: string;
        enableAnalytics?: boolean;
    }): {
        open: () => Promise<void>;
        getAddress: () => string | undefined;
    };
    export function defaultConfig(config: {
        metadata: {
            name: string;
            description: string;
            url: string;
            icons: string[];
        };
    }): unknown;
}

declare module '@tensorflow/tfjs' {
    // TensorFlow.js types are handled by @tensorflow-models/mobilenet
    const tf: unknown;
    export = tf;
}

declare module '@tensorflow-models/mobilenet' {
    export interface MobileNet {
        classify(element: HTMLImageElement | HTMLVideoElement | HTMLCanvasElement): Promise<Array<{
            className: string;
            probability: number;
        }>>;
    }
    export function load(config?: { version?: number; alpha?: number }): Promise<MobileNet>;
}
