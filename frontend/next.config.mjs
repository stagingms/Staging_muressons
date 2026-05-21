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

  // M3: Security headers applied to every page response
  async headers() {
    // Content-Security-Policy notes:
    //   script-src 'unsafe-inline'  — required for the two inline <script> blocks
    //     in layout.js (theme-flash prevention + fetch interceptor).
    //     Remove once those are extracted to external files with a nonce.
    //   style-src 'unsafe-inline'   — required for the many inline <style> /
    //     dangerouslySetInnerHTML style blocks across components.
    //   cdn.jsdelivr.net            — TechnicalGlossary.js loads MathJax from there.
    //   fonts.googleapis.com        — CEOInterview.js and SideTrackPanel.module.css
    //     import Google Fonts at runtime (not covered by next/font self-hosting).
    //   fonts.gstatic.com           — actual font files served by Google.
    //   ws: wss:                    — WebSocket connections to the backend.
    const csp = [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
      "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
      "font-src 'self' https://fonts.gstatic.com",
      "img-src 'self' data: blob:",
      "connect-src 'self' ws: wss:",
      "media-src 'self' blob:",
      "object-src 'none'",
      "frame-ancestors 'none'",
      "base-uri 'self'",
    ].join('; ');

    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Frame-Options',           value: 'DENY' },
          { key: 'X-Content-Type-Options',    value: 'nosniff' },
          { key: 'Referrer-Policy',           value: 'strict-origin-when-cross-origin' },
          { key: 'Permissions-Policy',        value: 'geolocation=(), camera=(), microphone=()' },
          { key: 'Content-Security-Policy',   value: csp },
        ],
      },
    ];
  },
};

export default nextConfig;
