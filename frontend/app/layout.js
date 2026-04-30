import './globals.css';
import ThemeToggle from './components/ThemeToggle';
import GlobalTooltip from './components/GlobalTooltip';
import { CurrencyProvider } from './contexts/CurrencyContext';

export const metadata = {
  title: 'Muressons Corporation — Executive Cockpit',
  description:
    'A 10-round corporate sustainability simulation. Lead four business units through ESG crises, investment trade-offs, and stakeholder dynamics.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <CurrencyProvider>
          {children}
        </CurrencyProvider>
        <ThemeToggle />
        <GlobalTooltip />
      </body>
    </html>
  );
}

