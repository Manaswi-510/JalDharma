import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import {
  Droplets,
  TrendingUp,
  CheckCircle2,
  AlertTriangle,
  Scale,
  Percent,
  Layers,
  ArrowUpRight,
  ShieldAlert,
  Info
} from 'lucide-react';
import {
  SYSTEM_METRICS,
  WEEKLY_COMPARISON,
  SHORTAGE_DISTRIBUTION,
  VILLAGES_DATABASE
} from '../../data/waterData';

export default function OverviewPage({ onNavigateToPage }) {
  // Sort high shortage villages for quick overview
  const criticalVillages = VILLAGES_DATABASE.filter(v => v.status === 'High');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top 6 KPI Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem' }}>
        {/* KPI 1: Total Water Available */}
        <div className="glass-panel kpi-card" style={{ borderLeft: '4px solid #0284c7' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="kpi-label">Total Water Available</span>
            <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(2, 132, 199, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#0284c7' }}>
              <Droplets size={20} />
            </div>
          </div>
          <div className="kpi-value" style={{ color: '#0284c7' }}>
            {SYSTEM_METRICS.totalWaterAvailableML} <span style={{ fontSize: '1.1rem', fontWeight: 600 }}>ML</span>
          </div>
          <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            <span>Reservoirs: 82.0 ML • Canal: 26.0 ML</span>
          </div>
        </div>

        {/* KPI 2: Total Predicted Demand */}
        <div className="glass-panel kpi-card" style={{ borderLeft: '4px solid #06b6d4' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="kpi-label">Total Predicted Demand</span>
            <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(6, 182, 212, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#06b6d4' }}>
              <TrendingUp size={20} />
            </div>
          </div>
          <div className="kpi-value" style={{ color: '#0369a1' }}>
            {SYSTEM_METRICS.totalPredictedDemandML} <span style={{ fontSize: '1.1rem', fontWeight: 600 }}>ML</span>
          </div>
          <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '0.5rem' }}>
            Across 45 District Villages (Linear Reg)
          </div>
        </div>

        {/* KPI 3: Total Allocated */}
        <div className="glass-panel kpi-card" style={{ borderLeft: '4px solid #10b981' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="kpi-label">Total Allocated</span>
            <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(16, 185, 129, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#10b981' }}>
              <CheckCircle2 size={20} />
            </div>
          </div>
          <div className="kpi-value" style={{ color: '#059669' }}>
            {SYSTEM_METRICS.totalAllocatedML} <span style={{ fontSize: '1.1rem', fontWeight: 600 }}>ML</span>
          </div>
          <div style={{ fontSize: '0.78rem', color: '#059669', marginTop: '0.5rem', fontWeight: 600 }}>
            93.1% Regional Fulfillment
          </div>
        </div>

        {/* KPI 4: Total Shortage */}
        <div className="glass-panel kpi-card" style={{ borderLeft: '4px solid #ef4444' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="kpi-label">Total Shortage</span>
            <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(239, 68, 68, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ef4444' }}>
              <AlertTriangle size={20} />
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
            <div className="kpi-value" style={{ color: '#dc2626' }}>
              {SYSTEM_METRICS.totalShortageML} <span style={{ fontSize: '1.1rem', fontWeight: 600 }}>ML</span>
            </div>
            <span style={{ fontSize: '0.72rem', background: '#fee2e2', color: '#b91c1c', padding: '0.2rem 0.5rem', borderRadius: '9999px', fontWeight: 700 }}>
              Deficit Active
            </span>
          </div>
          <div style={{ fontSize: '0.78rem', color: '#b91c1c', marginTop: '0.5rem' }}>
            5 High-Deficit nodes isolated
          </div>
        </div>

        {/* KPI 5: Average Satisfaction */}
        <div className="glass-panel kpi-card" style={{ borderLeft: '4px solid #8b5cf6' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="kpi-label">Average Satisfaction</span>
            <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(139, 92, 246, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#8b5cf6' }}>
              <Percent size={20} />
            </div>
          </div>
          <div className="kpi-value" style={{ color: '#7c3aed' }}>
            {SYSTEM_METRICS.averageSatisfactionPct}%
          </div>
          <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '0.5rem' }}>
            Priority villages protected above 75%
          </div>
        </div>

        {/* KPI 6: Fairness Index */}
        <div className="glass-panel kpi-card" style={{ borderLeft: '4px solid #f59e0b' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="kpi-label">Fairness Index</span>
            <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(245, 158, 11, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#f59e0b' }}>
              <Scale size={20} />
            </div>
          </div>
          <div className="kpi-value" style={{ color: '#d97706' }}>
            {SYSTEM_METRICS.fairnessIndex} <span style={{ fontSize: '1.05rem', fontWeight: 600, color: '#94a3b8' }}>/ 1.00</span>
          </div>
          <div style={{ fontSize: '0.78rem', color: '#d97706', marginTop: '0.5rem', fontWeight: 600 }}>
            Jain's Index: Optimal Equity Tier
          </div>
        </div>
      </div>

      {/* Row 2: 7-Day Trend Chart & Shortage Breakdown */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(480px, 1fr))', gap: '1.5rem' }}>
        {/* Recharts Bar Chart: Available vs Demand vs Allocated */}
        <div className="glass-panel" style={{ padding: '1.75rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <div>
              <h3 style={{ fontSize: '1.15rem', color: '#0f172a' }}>7-Day Water Allocation Dynamics</h3>
              <p style={{ fontSize: '0.82rem', color: '#64748b' }}>Comparison of regional availability, predicted demand, and dispatched volume (ML)</p>
            </div>
            <span style={{ fontSize: '0.75rem', background: '#f1f5f9', color: '#475569', padding: '0.3rem 0.75rem', borderRadius: '9999px', fontWeight: 600 }}>
              Past 7 Days
            </span>
          </div>

          <div style={{ height: '320px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={WEEKLY_COMPARISON} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(226, 232, 240, 0.8)" />
                <XAxis dataKey="day" tick={{ fill: '#64748b', fontSize: 12 }} />
                <YAxis tick={{ fill: '#64748b', fontSize: 12 }} domain={[100, 155]} />
                <Tooltip
                  contentStyle={{
                    background: 'rgba(15, 23, 42, 0.92)',
                    backdropFilter: 'blur(8px)',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    borderRadius: '12px',
                    color: '#ffffff',
                    fontSize: '0.85rem',
                  }}
                  formatter={(value) => [`${value} ML`, '']}
                />
                <Legend wrapperStyle={{ paddingTop: '10px', fontSize: '0.85rem' }} />
                <Bar dataKey="available" name="Available (ML)" fill="#0284c7" radius={[4, 4, 0, 0]} />
                <Bar dataKey="demand" name="Predicted Demand (ML)" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                <Bar dataKey="allocated" name="Allocated (ML)" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Shortage Classification Breakdown */}
        <div className="glass-panel" style={{ padding: '1.75rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <div>
                <h3 style={{ fontSize: '1.15rem', color: '#0f172a' }}>Village Shortage Classification</h3>
                <p style={{ fontSize: '0.82rem', color: '#64748b' }}>Categorization of all 45 district villages based on deficit percentage</p>
              </div>
              <span style={{ fontSize: '0.75rem', background: 'rgba(2, 132, 199, 0.1)', color: '#0284c7', padding: '0.3rem 0.75rem', borderRadius: '9999px', fontWeight: 700 }}>
                45 Total Nodes
              </span>
            </div>

            {/* Categorical Progress Cards */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1rem' }}>
              {SHORTAGE_DISTRIBUTION.map((item, idx) => (
                <div key={idx} style={{ background: '#f8fafc', padding: '1rem', borderRadius: '16px', border: '1px solid #e2e8f0' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: item.color }} />
                      <span style={{ fontSize: '0.9rem', fontWeight: 700, color: '#1e293b' }}>{item.category}</span>
                    </div>
                    <div style={{ fontSize: '0.95rem', fontWeight: 800, color: item.color }}>
                      {item.count} Villages <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 500 }}>({item.percent}%)</span>
                    </div>
                  </div>
                  {/* Progress track */}
                  <div style={{ width: '100%', height: '8px', background: '#e2e8f0', borderRadius: '9999px', overflow: 'hidden' }}>
                    <div style={{ width: `${item.percent}%`, height: '100%', background: item.color, borderRadius: '9999px' }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Critical Watch Alert */}
          <div style={{ marginTop: '1.5rem', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '14px', padding: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <ShieldAlert size={22} color="#dc2626" />
              <div>
                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#991b1b' }}>5 High-Shortage Villages Under Lifeline Protection</div>
                <div style={{ fontSize: '0.75rem', color: '#b91c1c' }}>Kashti, Kalyanpur, Mandavgan, Malegaon, Pedgaon receiving priority booster quotas</div>
              </div>
            </div>
            <button
              onClick={() => onNavigateToPage('justice')}
              style={{
                background: '#dc2626',
                color: '#ffffff',
                border: 'none',
                borderRadius: '8px',
                padding: '0.4rem 0.85rem',
                fontSize: '0.75rem',
                fontWeight: 700,
                cursor: 'pointer',
                whiteSpace: 'nowrap'
              }}
            >
              Inspect Equity
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
