import './globals.css';
import { DM_Sans, JetBrains_Mono } from 'next/font/google';
import ThemeToggle from './components/ThemeToggle';
import GlobalTooltip from './components/GlobalTooltip';
import ErrorBoundary from './components/ErrorBoundary';
import { CurrencyProvider } from './contexts/CurrencyContext';

// next/font handles preloading, self-hosting, font-display, and FOUT prevention
// automatically — no manual <link> tags needed.
// Use distinct injection variable names to avoid collision with the
// --font-sans / --font-mono declarations already in globals.css.
const dmSans = DM_Sans({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700', '800', '900'],
  variable: '--font-dm-sans',
  display: 'swap',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  weight: ['400', '500', '700'],
  variable: '--font-jetbrains-mono',
  display: 'swap',
});

export const metadata = {
  title: 'Muressons Global Corporation — Executive Cockpit',
  description:
    'A 10-round corporate sustainability simulation. Lead four business units through ESG crises, investment trade-offs, and stakeholder dynamics.',
};

export default function RootLayout({ children }) {
  return (
    <html
      lang="en"
      dir="ltr"
      suppressHydrationWarning
      className={`${dmSans.variable} ${jetbrainsMono.variable}`}
    >
      <head>
        {/* Inline script runs synchronously before any CSS paint, preventing the
            dark→light flash when the user's OS prefers light mode. It mirrors the
            same logic as ThemeToggle's useState initialiser so data-theme is set
            on <html> before React hydrates — no transition fires on mount.
            Must live inside <head> — Next.js rejects sync scripts outside it.  */}
        <script dangerouslySetInnerHTML={{ __html: `(function(){try{var t=localStorage.getItem('muressons-theme');var p=window.matchMedia('(prefers-color-scheme: light)').matches?'light':'dark';document.documentElement.setAttribute('data-theme',t||p);}catch(e){}})();` }} />
        
        {/* Global Fetch Interceptor to ensure JWT cookies are sent to admin endpoints */}
        <script dangerouslySetInnerHTML={{ __html: `
            (function() {
                if (typeof window !== 'undefined') {
                    const originalFetch = window.fetch;
                    window.fetch = async function () {
                        let [resource, config] = arguments;
                        if (typeof resource === 'string' && resource.includes('/api/admin')) {
                            config = config || {};
                            config.credentials = 'include';
                            
                            // Basic CSRF mitigation for mutating requests
                            if (config.method && !['GET', 'HEAD', 'OPTIONS'].includes(config.method.toUpperCase())) {
                                config.headers = config.headers || {};
                                config.headers['X-Requested-With'] = 'XMLHttpRequest';
                            }
                        }
                        return originalFetch(resource, config);
                    };
                }
            })();
        ` }} />
      </head>
      <body suppressHydrationWarning>
        <ErrorBoundary>
          <CurrencyProvider>
            {children}
          </CurrencyProvider>
        </ErrorBoundary>
        <ThemeToggle />
        <GlobalTooltip />
      </body>
    </html>
  );
}
