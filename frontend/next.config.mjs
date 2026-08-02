import path from 'path';
import { fileURLToPath } from 'url';

// Pin the workspace root to THIS folder. There is a stray package-lock.json in
// the parent (muressons-sim/) as well as this one, which made Next infer the
// wrong workspace root and caused a Turbopack panic ("Resource path 'app/page.js'
// need to be on project filesystem 'frontend'"). Pinning the root here makes
// filesystem resolution deterministic and silences the multi-lockfile warning.
const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Phase 1.4: Suppress dev-mode error overlay for cleaner cockpit UX
  devIndicators: false,

  // Deterministic workspace root (see note above).
  outputFileTracingRoot: __dirname,
  turbopack: { root: __dirname },

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
    //   frame-src youtube/vimeo     — briefing videos (RoundBriefing Read|Watch)
    //     embed as iframes. Without an explicit frame-src, iframes fall back to
    //     default-src 'self' and the embed renders Chrome's "This content is
    //     blocked" page. youtube-nocookie kept alongside youtube in case
    //     toEmbed() switches to the privacy-enhanced host later.
    //   media-src https:            — facilitator-configured direct video URLs
    //     (non-YouTube/Vimeo) play through a native <video> tag from wherever
    //     the media is hosted; config is URL-only, media is never in git.
    const csp = [
      "default-src 'self' blob:",
      "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
      "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
      "font-src 'self' https://fonts.gstatic.com",
      "img-src 'self' data: blob:",
      "connect-src 'self' ws: wss: blob:",
      "media-src 'self' blob: https:",
      "frame-src 'self' https://www.youtube.com https://www.youtube-nocookie.com https://player.vimeo.com",
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
          // F-20: HSTS. The backend middleware already sends this on /api
          // responses, but the app shell is served by Next — so the header the
          // browser actually latches onto for the origin was missing. Browsers
          // ignore HSTS over plain http, so local dev is unaffected.
          { key: 'Strict-Transport-Security', value: 'max-age=31536000; includeSubDomains' },
        ],
      },
    ];
  },
};

export default nextConfig;
