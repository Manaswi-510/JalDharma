import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  TrendingUp,
  MapPin,
  SlidersHorizontal,
  Activity,
  Scale,
  Droplets,
  ArrowLeft,
  Clock,
  ShieldCheck,
  ChevronRight
} from 'lucide-react';

const NAV_TABS = [
  { id: 'overview', label: '1. Overview', icon: LayoutDashboard },
  { id: 'prediction', label: '2. Demand Prediction', icon: TrendingUp },
  { id: 'gis', label: '3. GIS Map', icon: MapPin },
  { id: 'allocation', label: '4. Allocation', icon: SlidersHorizontal },
  { id: 'network', label: '5. Network', icon: Activity },
  { id: 'justice', label: '6. Water Justice', icon: Scale },
];

export default function DashboardLayout({ activeTab, onSelectTab, onBackToHub, children }) {
  const [currentTime, setCurrentTime] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', position: 'relative', zIndex: 10, paddingBottom: '3rem' }}>
      {/* Persistent Top Navigation Bar */}
      <header className="dashboard-topbar">
        {/* Left: Brand Badge & Return Button */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <button
            onClick={onBackToHub}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              padding: '0.45rem 1rem',
              borderRadius: '9999px',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              background: 'rgba(255, 255, 255, 0.08)',
              color: '#e2e8f0',
              fontSize: '0.82rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.18)';
              e.currentTarget.style.color = '#38bdf8';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.08)';
              e.currentTarget.style.color = '#e2e8f0';
            }}
          >
            <ArrowLeft size={16} />
            <span>Back to Hub</span>
          </button>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '10px',
                background: 'linear-gradient(135deg, #0284c7, #06b6d4)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#ffffff',
                boxShadow: '0 4px 12px rgba(6, 182, 212, 0.4)',
              }}
            >
              <Droplets size={20} />
            </div>
            <div>
              <div style={{ fontWeight: 800, fontSize: '1.05rem', color: '#ffffff', letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <span>Jai Dharma AI</span>
                <span style={{ fontSize: '0.65rem', background: 'rgba(6, 182, 212, 0.25)', color: '#38bdf8', padding: '0.15rem 0.45rem', borderRadius: '4px', border: '1px solid rgba(56, 189, 248, 0.3)' }}>v2.4</span>
              </div>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                Equitable Water Resource & Network OS
              </div>
            </div>
          </div>
        </div>

        {/* Center: Floating Navigation Tab Strip */}
        <nav className="nav-tab-strip">
          {NAV_TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                className={`nav-tab-btn ${isActive ? 'active' : ''}`}
                onClick={() => onSelectTab(tab.id)}
              >
                <Icon size={16} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Right: Live Telemetry Status & System Clock */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          {/* Status Badge */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.35rem 0.85rem',
              background: 'rgba(16, 185, 129, 0.15)',
              border: '1px solid rgba(16, 185, 129, 0.35)',
              borderRadius: '9999px',
              color: '#34d399',
              fontSize: '0.75rem',
              fontWeight: 700,
            }}
          >
            <span className="status-pulse-dot" style={{ background: '#10b981' }} />
            <span>System Status: Optimal • All Nodes Online</span>
          </div>

          {/* Clock */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#94a3b8', fontSize: '0.8rem', fontWeight: 600 }}>
            <Clock size={15} color="#38bdf8" />
            <span>{currentTime}</span>
          </div>
        </div>
      </header>

      {/* Main Page Area */}
      <main style={{ maxWidth: '1680px', width: 'calc(100% - 2rem)', margin: '0 auto', flex: 1 }}>
        {children}
      </main>
    </div>
  );
}
