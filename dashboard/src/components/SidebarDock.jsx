import React from 'react';
import {
  Droplet,
  Home,
  TrendingUp,
  Layers,
  BarChart2,
  Settings,
  Power,
} from 'lucide-react';

export default function SidebarDock({ activeTab, setActiveTab }) {
  return (
    <aside className="left-dock">
      {/* Top Logo - JAL DHARMA */}
      <div
        className="dock-logo"
        title="JAL DHARMA AI"
        onClick={() => setActiveTab('overview')}
        style={{ cursor: 'pointer' }}
        id="dock-logo-btn"
      >
        <Droplet size={22} fill="white" />
      </div>

      {/* Navigation Buttons */}
      <nav className="dock-nav">
        <button
          className={`dock-btn ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
          title="Dashboard Page 1: Overview"
          id="dock-overview-btn"
        >
          <Home size={22} />
        </button>

        <button
          className={`dock-btn ${activeTab === 'prediction' ? 'active' : ''}`}
          onClick={() => setActiveTab('prediction')}
          title="Dashboard Page 2: Demand Prediction"
          id="dock-prediction-btn"
        >
          <TrendingUp size={22} />
        </button>

        <button
          className="dock-btn"
          title="Water Network (Phases 13-14)"
          onClick={() => setActiveTab('overview')}
        >
          <Layers size={22} />
        </button>

        <button
          className="dock-btn"
          title="Water Justice Metrics (Phases 18-20)"
          onClick={() => setActiveTab('overview')}
        >
          <BarChart2 size={22} />
        </button>
      </nav>

      {/* Bottom Settings & Status */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        <button className="dock-btn" title="Settings">
          <Settings size={20} />
        </button>
        <button className="dock-btn" title="System Online">
          <Power size={20} color="#10b981" />
        </button>
      </div>
    </aside>
  );
}
