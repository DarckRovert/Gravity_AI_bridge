import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',
  images: {
    unoptimized: true,
  },
  transpilePackages: [
    '@web3modal/ethers',
    '@web3modal/scaffold',
    '@web3modal/ui',
    '@web3modal/core',
    '@web3modal/base',
    '@motionone/dom',
    'motion'
  ],
  // Exclude non-browser packages from bundling for server-side processing
  serverExternalPackages: [
    'unstorage',
    '@tensorflow/tfjs',
    '@tensorflow/tfjs-core',
    '@tensorflow/tfjs-backend-cpu',
    '@tensorflow/tfjs-backend-webgl',
    '@tensorflow-models/mobilenet',
  ],
};

export default nextConfig;
