import React from 'react';
import {
  Activity,
  AlertTriangle,
  ShieldAlert,
  Droplet,
  Gauge,
  CheckCircle2,
  RefreshCw,
  Zap,
  ArrowRight
} from 'lucide-react';
import { PIPELINES_DATA } from '../../data/waterData';

export default function NetworkPage() {
  // Count active warnings & leaks
  const leakLines = PIPELINES_DATA.filter(p => p.status === 'Leak Detected');
  const warningLines = PIPELINES_DATA.filter(p => p.status === 'Warning');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Warning Banner for High Pressure & Leak Telemetry */}
      {(leakLines.length > 0 || warningLines.length > 0) && (
        <div
          style={{
            background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.12), rgba(245, 158, 11, 0.12))',
            backdropFilter: 'blur(16px)',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            borderRadius: '20px',
            padding: '1.25rem 1.75rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 8px 24px rgba(239, 68, 68, 0.15)',
            flexWrap: 'wrap',
            gap: '1rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div
              style={{
                width: '46px',
                height: '46px',
                borderRadius: '14px',
                background: '#ef4444',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#ffffff',
                boxShadow: '0 4px 15px rgba(239, 68, 68, 0.4)',
              }}
            >
              <ShieldAlert size={26} />
            </div>
            <div>
              <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#991b1b', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span>Active Hydraulic Telemetry Alerts ({leakLines.length + warningLines.length})</span>
                <span style={{ fontSize: '0.72rem', background: '#dc2626', color: '#ffffff', padding: '0.15rem 0.5rem', borderRadius: '9999px', fontWeight: 700 }}>
                  Immediate Attention
                </span>
              </div>
              <div style={{ fontSize: '0.85rem', color: '#7f1d1d', marginTop: '0.2rem' }}>
                Line <strong>PIPE_005</strong> has detected pressure drop (leak suspected at 42 PSI) • <strong>PIPE_001</strong> & <strong>PIPE_004</strong> exceed 90% peak capacity.
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              style={{
                padding: '0.5rem 1rem',
                borderRadius: '10px',
                background: '#dc2626',
                color: '#ffffff',
                border: 'none',
                fontSize: '0.82rem',
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              Trigger Pressure Relief
            </button>
            <button
              style={{
                padding: '0.5rem 1rem',
                borderRadius: '10px',
                background: '#ffffff',
                color: '#7f1d1d',
                border: '1px solid #fca5a5',
                fontSize: '0.82rem',
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              Dispatch Field Crew
            </button>
          </div>
        </div>
      )}

      {/* Network Header & Quick Telemetry KPI Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem' }}>
        <div className="glass-panel kpi-card" style={{ borderLeft: '4px solid #0284c7' }}>
          <span className="kpi-label">Total Trunk Lines</span>
          <div className="kpi-value" style={{ color: '#0284c7' }}>
            8 <span style={{ fontSize: '1.1rem' }}>Active</span>
          </div>
          <div style={{ fontSize: '0.82rem', color: '#64748b', marginTop: '0.4rem' }}>
            Across 142.5 km pipeline grid
          </div>
        </div>

        <div className="glass-panel kpi-card" style={{ borderLeft: '4px solid #10b981' }}>
          <span className="kpi-label">Average Utilization</span>
          <div className="kpi-value" style={{ color: '#059669' }}>
            79.8%
          </div>
          <div style={{ fontSize: '0.82rem', color: '#059669', marginTop: '0.4rem', fontWeight: 600 }}>
            Within Safe Hydraulic Limits (&lt;85%)
          </div>
        </div>

        <div className="glass-panel kpi-card" style={{ borderLeft: '4px solid #f59e0b' }}>
          <span className="kpi-label">High Pressure Warnings</span>
          <div className="kpi-value" style={{ color: '#d97706' }}>
            3 Lines
          </div>
          <div style={{ fontSize: '0.82rem', color: '#d97706', marginTop: '0.4rem' }}>
            Utilization exceeding 90%
          </div>
        </div>

        <div className="glass-panel kpi-card" style={{ borderLeft: '4px solid #ef4444' }}>
          <span className="kpi-label">Detected Leaks</span>
          <div className="kpi-value" style={{ color: '#dc2626' }}>
            1 Alert
          </div>
          <div style={{ fontSize: '0.82rem', color: '#dc2626', marginTop: '0.4rem', fontWeight: 600 }}>
            Estimated Loss: 14 LPS
          </div>
        </div>
      </div>

      {/* Pipeline Telemetry Table */}
      <div className="glass-panel" style={{ padding: '1.5rem', overflowX: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <div>
            <h3 style={{ fontSize: '1.25rem', color: '#0f172a' }}>Real-Time Pipeline Telemetry Table</h3>
            <p style={{ fontSize: '0.82rem', color: '#64748b' }}>Live sensor monitoring of hydraulic flow, pressure PSI, and leak detection telemetry</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#0284c7', fontSize: '0.82rem', fontWeight: 600 }}>
            <RefreshCw size={15} /> Live Telemetry 1000ms Poll
          </div>
        </div>

        <table className="glass-table">
          <thead>
            <tr>
              <th>Pipeline ID & Route</th>
              <th>Max Capacity (LPS)</th>
              <th>Current Flow (LPS)</th>
              <th>Pressure (PSI)</th>
              <th>Utilization %</th>
              <th>Telemetry Status</th>
            </tr>
          </thead>
          <tbody>
            {PIPELINES_DATA.map((pipe) => {
              const statusColor =
                pipe.status === 'Operational' ? '#10b981' :
                pipe.status === 'Warning' ? '#f59e0b' : '#ef4444';

              return (
                <tr key={pipe.id}>
                  <td>
                    <div style={{ fontWeight: 700, color: '#0f172a' }}>{pipe.id}</div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{pipe.route}</div>
                  </td>
                  <td style={{ fontWeight: 600 }}>{pipe.maxCapacityLPS} LPS</td>
                  <td style={{ fontWeight: 700, color: '#0284c7' }}>{pipe.currentFlowLPS} LPS</td>
                  <td>
                    <span style={{ fontWeight: 700, color: pipe.pressurePSI > 90 ? '#ef4444' : pipe.pressurePSI < 50 ? '#dc2626' : '#334155' }}>
                      {pipe.pressurePSI} PSI
                    </span>
                  </td>
                  <td style={{ minWidth: '160px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                      <span style={{ fontWeight: 700, color: statusColor, minWidth: '45px', fontSize: '0.85rem' }}>
                        {pipe.utilization}%
                      </span>
                      <div style={{ flex: 1, height: '8px', background: '#e2e8f0', borderRadius: '9999px', overflow: 'hidden' }}>
                        <div
                          style={{
                            width: `${Math.min(100, pipe.utilization)}%`,
                            height: '100%',
                            background: statusColor,
                            borderRadius: '9999px',
                          }}
                        />
                      </div>
                    </div>
                  </td>
                  <td>
                    <span
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.4rem',
                        padding: '0.3rem 0.75rem',
                        borderRadius: '9999px',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        background: `${statusColor}18`,
                        color: statusColor,
                        border: `1px solid ${statusColor}40`,
                      }}
                    >
                      <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: statusColor }} />
                      {pipe.status}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
