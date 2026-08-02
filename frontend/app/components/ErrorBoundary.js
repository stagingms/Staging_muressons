'use client';
import React from 'react';

/**
 * FIX-QA-002: Graceful Failure Error Boundary
 * 
 * Catches unhandled React render errors and displays a user-friendly
 * recovery message instead of a blank screen or raw stack trace.
 * 
 * Usage: Wrap around any component tree that should be resilient:
 *   <ErrorBoundary><ExecutiveCockpit /></ErrorBoundary>
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    // Log to console for debugging (non-technical users won't see this)
    console.error('[ErrorBoundary] Caught render error:', error, errorInfo);
  }

  handleReload = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.reload();
  };

  handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)',
          fontFamily: "'DM Sans', sans-serif",
          color: '#e2e8f0',
          padding: 20,
        }}>
          <div style={{
            maxWidth: 520,
            textAlign: 'center',
            background: 'rgba(30, 41, 59, 0.8)',
            borderRadius: 16,
            padding: '40px 32px',
            border: '1px solid rgba(99, 102, 241, 0.2)',
            boxShadow: '0 25px 50px rgba(0,0,0,0.5)',
            backdropFilter: 'blur(12px)',
          }}>
            {/* Icon */}
            <div style={{ fontSize: 48, marginBottom: 16 }}>⚠️</div>

            {/* Title */}
            <h2 style={{
              fontSize: '1.25rem',
              fontWeight: 700,
              marginBottom: 12,
              color: '#f8fafc',
              letterSpacing: '-0.02em',
            }}>
              Something went wrong
            </h2>

            {/* User-friendly message */}
            <p style={{
              fontSize: '0.875rem',
              color: '#94a3b8',
              lineHeight: 1.6,
              marginBottom: 24,
            }}>
              The simulation encountered an unexpected issue. Your progress has been 
              saved automatically. Please try one of the options below to continue.
            </p>

            {/* Action buttons */}
            <div style={{
              display: 'flex',
              gap: 12,
              justifyContent: 'center',
              flexWrap: 'wrap',
            }}>
              <button
                onClick={this.handleRetry}
                style={{
                  padding: '10px 24px',
                  borderRadius: 8,
                  border: '1px solid rgba(99, 102, 241, 0.4)',
                  background: 'rgba(99, 102, 241, 0.15)',
                  color: '#a5b4fc',
                  fontWeight: 600,
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  transition: 'background 0.2s ease, color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease, transform 0.2s ease',
                }}
                onMouseEnter={(e) => {
                  e.target.style.background = 'rgba(99, 102, 241, 0.3)';
                  e.target.style.transform = 'translateY(-1px)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.background = 'rgba(99, 102, 241, 0.15)';
                  e.target.style.transform = 'translateY(0)';
                }}
              >
                🔄 Try Again
              </button>

              <button
                onClick={this.handleReload}
                style={{
                  padding: '10px 24px',
                  borderRadius: 8,
                  border: '1px solid rgba(16, 185, 129, 0.4)',
                  background: 'rgba(16, 185, 129, 0.15)',
                  color: '#6ee7b7',
                  fontWeight: 600,
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  transition: 'background 0.2s ease, color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease, transform 0.2s ease',
                }}
                onMouseEnter={(e) => {
                  e.target.style.background = 'rgba(16, 185, 129, 0.3)';
                  e.target.style.transform = 'translateY(-1px)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.background = 'rgba(16, 185, 129, 0.15)';
                  e.target.style.transform = 'translateY(0)';
                }}
              >
                🔃 Reload Page
              </button>
            </div>

            {/* Technical details (collapsed) */}
            <details style={{
              marginTop: 20,
              textAlign: 'left',
              fontSize: '0.7rem',
              color: '#64748b',
            }}>
              <summary style={{ cursor: 'pointer', userSelect: 'none', marginBottom: 6 }}>
                Technical Details (for support)
              </summary>
              <pre style={{
                padding: 10,
                borderRadius: 8,
                background: 'rgba(0,0,0,0.3)',
                overflowX: 'auto',
                maxHeight: 120,
                fontSize: '0.65rem',
                lineHeight: 1.4,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}>
                {this.state.error?.toString()}
                {'\n'}
                {this.state.errorInfo?.componentStack?.slice(0, 500)}
              </pre>
            </details>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
