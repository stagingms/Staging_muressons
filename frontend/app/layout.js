import './globals.css';
import ThemeToggle from './components/ThemeToggle';
import GlobalTooltip from './components/GlobalTooltip';
import ErrorBoundary from './components/ErrorBoundary';
import { CurrencyProvider } from './contexts/CurrencyContext';

export const metadata = {
  title: 'Muressons Global Corporation — Executive Cockpit',
  description:
    'A 10-round corporate sustainability simulation. Lead four business units through ESG crises, investment trade-offs, and stakeholder dynamics.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap"
          rel="stylesheet"
        />
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

