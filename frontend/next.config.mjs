/** @type {import('next').NextConfig} */
const nextConfig = {
  // Phase 1.4: Suppress dev-mode error overlay for cleaner cockpit UX
  devIndicators: false,
  // Proxy API calls to the backend in development
  // In production, configure via environment variable
  async rewrites() {
    const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
      {
        source: '/health',
        destination: `${backendUrl}/health`,
      },
    ];
  },
};

export default nextConfig;
