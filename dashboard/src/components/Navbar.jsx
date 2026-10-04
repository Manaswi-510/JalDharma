import React from 'react';
import { Droplet, BarChart3, TrendingUp, Layers, Activity } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab }) {
  return (
    <header className="header-nav">
      <div className="nav-inner">
        {/* Brand */}
        <div className="nav-brand">
          <div className="brand-icon">
            <Droplet size={24} />
          </div>
          <div>
            <div className="brand-title">JAL DHARMA AI</div>
            <div className="brand-subtitle">Water Demand & Justice Intelligence</div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="nav-tabs">
          <button
            className={`nav-tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
            id="tab-overview"
          >
            <BarChart3 size={16} />
            <span>Page 1: Overview</span>
          </button>

          <button
            className={`nav-tab-btn ${activeTab === 'prediction' ? 'active' : ''}`}
            onClick={() => setActiveTab('prediction')}
            id="tab-prediction"
          >
            <TrendingUp size={16} />
            <span>Page 2: Demand Prediction</span>
          </button>
        </nav>

        {/* System Health / Status Indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div className="badge badge-cyan" style={{ padding: '0.35rem 0.85rem' }}>
            <span className="live-dot" />
            <span>AI Predictor Active</span>
          </div>
        </div>
      </div>
    </header>
  );
}
