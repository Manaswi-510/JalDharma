import React from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import {
  Scale,
  Percent,
  AlertOctagon,
  ShieldCheck,
  Sparkles,
  ArrowRight,
  TrendingDown,
  Info
} from 'lucide-react';
import { WATER_JUSTICE_DATA } from '../../data/waterData';

export default function WaterJusticePage() {
  const {
    jainsFairnessIndex,
    averageSatisfactionPct,
    weightedShortageKL,
    chronicDeficitVillages,
    equityCurve,
    disparityBars,
  } = WATER_JUSTICE_DATA;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top 3 Justice Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
        {/* Fairness Index */}
        <div className="glass-panel kpi-card" style={{ borderLeft: '4px solid #ec4899' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="kpi-label">Jain's Fairness Index</span>
            <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(236, 72, 153, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ec4899' }}>
              <Scale size={20} />
            </div>
          </div>
          <div className="kpi-value" style={{ color: '#be185d' }}>
            0.94 <span style={{ fontSize: '1.1rem', color: '#94a3b8' }}>/ 1.00</span>
          </div>
          <div style={{ fontSize: '0.82rem', color: '#be185d', marginTop: '0.4rem', fontWeight: 600 }}>
            Optimal Equity Tier (Threshold: ≥ 0.90)
          </div>
        </div>

        {/* Average Satisfaction */}
        <div className="glass-panel kpi-card" style={{ borderLeft: '4px solid #8b5cf6' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="kpi-label">Average Satisfaction</span>
            <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(139, 92, 246, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#8b5cf6' }}>
              <Percent size={20} />
            </div>
          </div>
          <div className="kpi-value" style={{ color: '#7c3aed' }}>
            {averageSatisfactionPct}%
          </div>
          <div style={{ fontSize: '0.82rem', color: '#64748b', marginTop: '0.4rem' }}>
            Zero villages below minimum lifeline 75%
          </div>
        </div>

        {/* Weighted Shortage */}
        <div className="glass-panel kpi-card" style={{ borderLeft: '4px solid #f59e0b' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="kpi-label">Demographic Weighted Shortage</span>
            <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(245, 158, 11, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#f59e0b' }}>
              <AlertOctagon size={20} />
            </div>
          </div>
          <div className="kpi-value" style={{ color: '#d97706' }}>
            {weightedShortageKL} <span style={{ fontSize: '1.1rem' }}>kL</span>
          </div>
          <div style={{ fontSize: '0.82rem', color: '#64748b', marginTop: '0.4rem' }}>
            Adjusted by Socio-Economic Vulnerability Index
          </div>
        </div>
      </div>

      {/* Row 2: Disparity Spectrum & Lorenz Equity Distribution Curve */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(480px, 1fr))', gap: '1.5rem' }}>
        {/* Disparity Bar Chart: Sorted from lowest to highest */}
        <div className="glass-panel" style={{ padding: '1.75rem' }}>
          <div style={{ marginBottom: '1.25rem' }}>
            <h3 style={{ fontSize: '1.15rem', color: '#0f172a' }}>Village Satisfaction Disparity Spectrum</h3>
            <p style={{ fontSize: '0.82rem', color: '#64748b' }}>
              Sorted from lowest to highest satisfaction. Highlighting the 75% constitutional equity safety floor.
            </p>
          </div>

          <div style={{ height: '300px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={disparityBars} margin={{ top: 10, right: 10, left: -10, bottom: 25 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(226, 232, 240, 0.8)" />
                <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 11 }} angle={-35} textAnchor="end" />
                <YAxis tick={{ fill: '#64748b', fontSize: 12 }} domain={[60, 100]} />
                <Tooltip
                  contentStyle={{
                    background: 'rgba(15, 23, 42, 0.94)',
                    backdropFilter: 'blur(8px)',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    borderRadius: '12px',
                    color: '#ffffff',
                    fontSize: '0.85rem',
                  }}
                  formatter={(val) => [`${val}%`, 'Satisfaction']}
                />
                <Bar dataKey="satisfaction" name="Satisfaction %" fill="#0284c7" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Equity Distribution Curve (Lorenz Curve) */}
        <div className="glass-panel" style={{ padding: '1.75rem' }}>
          <div style={{ marginBottom: '1.25rem' }}>
            <h3 style={{ fontSize: '1.15rem', color: '#0f172a' }}>Equity Distribution Curve (Lorenz Model)</h3>
            <p style={{ fontSize: '0.82rem', color: '#64748b' }}>
              Cumulative population share vs. water allocation share. Area near the 45° diagonal confirms high equity (Gini: 0.105).
            </p>
          </div>

          <div style={{ height: '300px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={equityCurve} margin={{ top: 10, right: 20, left: -10, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(226, 232, 240, 0.8)" />
                <XAxis dataKey="popShare" tick={{ fill: '#64748b', fontSize: 12 }} unit="%" />
                <YAxis tick={{ fill: '#64748b', fontSize: 12 }} unit="%" domain={[0, 100]} />
                <Tooltip
                  contentStyle={{
                    background: 'rgba(15, 23, 42, 0.94)',
                    backdropFilter: 'blur(8px)',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    borderRadius: '12px',
                    color: '#ffffff',
                    fontSize: '0.85rem',
                  }}
                  formatter={(val, name) => [`${val}%`, name]}
                />
                <Legend wrapperStyle={{ fontSize: '0.85rem' }} />
                <Line
                  type="monotone"
                  dataKey="perfectEquality"
                  name="Perfect Equality (45° Line)"
                  stroke="#94a3b8"
                  strokeDasharray="4 4"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="actualWaterShare"
                  name="Actual Allocation Curve"
                  stroke="#ec4899"
                  strokeWidth={3}
                  dot={{ r: 4, fill: '#ec4899' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Outlier Alerts: Flagging Chronic Deficits with AI Recommendations */}
      <div className="glass-panel" style={{ padding: '1.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1.25rem' }}>
          <Sparkles size={20} color="#0284c7" />
          <h3 style={{ fontSize: '1.15rem', color: '#0f172a' }}>
            AI Equity Re-Routing Recommendations (Outlier Mitigation)
          </h3>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
          {chronicDeficitVillages.map((item, idx) => (
            <div
              key={idx}
              style={{
                background: '#f8fafc',
                border: '1px solid #e2e8f0',
                borderRadius: '16px',
                padding: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <span style={{ fontSize: '1rem', fontWeight: 800, color: '#0f172a' }}>{item.name}</span>
                  <span style={{ fontSize: '0.75rem', background: '#fee2e2', color: '#b91c1c', padding: '0.2rem 0.5rem', borderRadius: '9999px', fontWeight: 700 }}>
                    Shortage: {item.shortage}
                  </span>
                </div>
                <div style={{ fontSize: '0.82rem', color: '#64748b', marginBottom: '0.75rem' }}>
                  <strong>Root Cause:</strong> {item.reason}
                </div>
              </div>

              <div style={{ background: '#e0f2fe', padding: '0.75rem', borderRadius: '10px', border: '1px solid #bae6fd' }}>
                <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#0369a1', textTransform: 'uppercase', marginBottom: '0.2rem' }}>
                  Recommended Action:
                </div>
                <div style={{ fontSize: '0.82rem', color: '#0c4a6e', fontWeight: 600 }}>
                  {item.recommendation}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
