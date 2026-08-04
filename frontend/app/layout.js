import './globals.css';
// Phase A (player redesign): design tokens — definitions only, nothing
// consumes them yet, so this import is zero-visual-change by construction.
import './styles/tokens.css';
import { DM_Sans, JetBrains_Mono } from 'next/font/google';
import ThemeToggle from './components/ThemeToggle';
import GlobalTooltip from './components/GlobalTooltip';
import ErrorBoundary from './components/ErrorBoundary';
import MotionPrefs from './components/MotionPrefs';
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
        {/* PHASE 8. First focusable thing on every page. The cockpit puts a
            logo, a round line, a rail of tabs and a KPI column between the
            document start and the decision; a keyboard user should not have to
            walk all of it every round. Targets #main-stage, which the cockpit's
            centre column carries. */}
        <a href="#main-stage" className="skip-link">Skip to the decision</a>
        <ErrorBoundary>
          <MotionPrefs>
            <CurrencyProvider>
              {children}
            </CurrencyProvider>
          </MotionPrefs>
        </ErrorBoundary>
        <ThemeToggle />
        <GlobalTooltip />
      </body>
    </html>
  );
}
