/**
 * DataWrapper - Transparent loading/error shell
 * Wraps any page with a spinner while data loads and shows an error card on failure.
 * Design is minimal so it doesn't interfere with page styling.
 */
import React from 'react';

export default function DataWrapper({ loading, error, children, pageName = 'data' }) {
  if (loading) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '300px',
        gap: '1rem',
      }}>
        {/* Animated water-drop spinner */}
        <div style={{
          width: '52px',
          height: '52px',
          borderRadius: '50%',
          background: 'linear-gradient(135deg, #0284c7, #06b6d4)',
          animation: 'spin 1s linear infinite',
          boxShadow: '0 0 24px rgba(6, 182, 212, 0.4)',
        }} />
        <p style={{ color: '#64748b', fontSize: '0.9rem', fontWeight: 600 }}>
          Loading live {pageName}…
        </p>
        <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-panel" style={{
        padding: '2rem',
        borderLeft: '4px solid #ef4444',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem',
      }}>
        <strong style={{ color: '#ef4444', fontSize: '1rem' }}>⚠ API Connection Error</strong>
        <p style={{ color: '#64748b', fontSize: '0.85rem' }}>{error}</p>
        <p style={{ color: '#94a3b8', fontSize: '0.78rem' }}>
          Make sure the backend is running: <code style={{ background: '#f1f5f9', padding: '2px 6px', borderRadius: '4px' }}>uvicorn src.api.main:app --reload --port 8000</code>
        </p>
      </div>
    );
  }

  return children;
}
