import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  logging: {
    fetches: {
      fullUrl: true,
    },
  },
  experimental: {
    // next.js: 1656ms, application-code: 153ms
    serverActions: {
      allowedOrigins: ["pukat-master:6969", "pukat-master:3000", "pukat-master", "100.85.142.33:6969", "100.85.142.33"]
    }
  },
  // This is the property Next.js Turbo/HMR specifically requested
  // @ts-ignore - Some versions might have this in experimental or top level
  allowedDevOrigins: ['pukat-master', 'pukat-master:6969', 'pukat-master:3000', '100.85.142.33:6969', '100.85.142.33'],
  
  devIndicators: {
    appIsrStatus: true,
  },
};

export default nextConfig;
