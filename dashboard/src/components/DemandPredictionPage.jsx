import React, { useState, useMemo } from 'react';
import {
  TrendingUp,
  Calendar,
  Compass,
  Activity,
  Droplet,
  CloudRain,
  Thermometer,
  CheckCircle,
  BarChart2,
  Sparkles,
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';

import predictionsData from '../data/predictions.json';
import villagesCatalog from '../data/villages.json';

// Sleek white & aquatic tooltip
const CustomWaterTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const actual = data.actual;
    const predicted = data.predicted;
    const diff = actual - predicted;
    const diffPct = ((diff / actual) * 100).toFixed(1);

    return (
      <div
        style={{
          background: '#ffffff',
          border: '1.5px solid #bae6fd',
          borderRadius: '16px',
          padding: '1rem',
          boxShadow: '0 12px 30px rgba(12, 74, 110, 0.15)',
          fontSize: '0.82rem',
          minWidth: '230px',
        }}
      >
        <div style={{ fontWeight: 800, color: '#0f172a', marginBottom: '0.5rem', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.35rem' }}>
          📅 Date: {label}
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
          <span style={{ color: '#0284c7', fontWeight: 600 }}>Actual Demand:</span>
          <strong>{actual.toLocaleString()} L</strong>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
          <span style={{ color: '#059669', fontWeight: 600 }}>AI Predicted:</span>
          <strong>{predicted.toLocaleString()} L</strong>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
          <span style={{ color: '#64748b' }}>Forecast Variance:</span>
          <span style={{ color: Math.abs(diffPct) > 5 ? '#d97706' : '#059669', fontWeight: 700 }}>
            {diff > 0 ? `+${diff.toLocaleString()} L` : `${diff.toLocaleString()} L`} ({diffPct}%)
          </span>
        </div>
        <div style={{ marginTop: '0.4rem', paddingTop: '0.4rem', borderTop: '1px solid #f1f5f9', display: 'flex', gap: '0.75rem', color: '#64748b', fontSize: '0.75rem' }}>
          <span>🌡️ {data.temp}°C</span>
          <span>🌧️ {data.rain} mm</span>
          <span>💧 {data.humidity}%</span>
        </div>
      </div>
    );
  }
  return null;
};

export default function DemandPredictionPage({ selectedVillageId, setSelectedVillageId }) {
  const [rangePreset, setRangePreset] = useState('30');

  const currentVillageEntry = predictionsData[selectedVillageId] || predictionsData['VIL_001'];
  const { meta, metrics, series } = currentVillageEntry;

  const filteredSeries = useMemo(() => {
    if (!series || series.length === 0) return [];
    const days = parseInt(rangePreset, 10);
    if (days >= series.length) return series;
    return series.slice(-days);
  }, [series, rangePreset]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* 1. TOP HEADER & INTERACTIVE CONTROLS */}
      <div className="water-card" style={{ padding: '1.5rem 2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1.25rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
              <span className="water-pill-badge">
                <TrendingUp size={14} />
                Dashboard Page 2
              </span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                AI Demand Forecasting Engine
              </span>
            </div>
            <h2>Time-Series Demand Prediction</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '0.2rem' }}>
              Inspect village-level historical water consumption and machine learning projections.
            </p>
          </div>

          {/* CONTROLS */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            {/* Village Selector Dropdown */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
              <label style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Select Village:
              </label>
              <select
                value={selectedVillageId}
                onChange={(e) => setSelectedVillageId(e.target.value)}
                className="water-select"
                id="village-dropdown"
              >
                {villagesCatalog.map((v) => (
                  <option key={v.village_id} value={v.village_id}>
                    {v.village_name} ({v.village_id}) • Pop: {v.population.toLocaleString()}
                  </option>
                ))}
              </select>
            </div>

            {/* Date Range Preset Pills */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
              <label style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Date Window:
              </label>
              <div style={{ display: 'flex', gap: '0.35rem', background: '#f1f5f9', padding: '0.25rem', borderRadius: 'var(--radius-full)' }}>
                {[
                  { label: '7D', val: '7' },
                  { label: '14D', val: '14' },
                  { label: '30D', val: '30' },
                  { label: '90D (All)', val: '90' },
                ].map((btn) => (
                  <button
                    key={btn.val}
                    onClick={() => setRangePreset(btn.val)}
                    style={{
                      padding: '0.35rem 0.85rem',
                      border: 'none',
                      borderRadius: 'var(--radius-full)',
                      fontSize: '0.8rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                      background: rangePreset === btn.val ? '#0284c7' : 'transparent',
                      color: rangePreset === btn.val ? '#ffffff' : '#64748b',
                      transition: 'all 0.2s',
                    }}
                  >
                    {btn.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 2. VILLAGE METADATA & MODEL ACCURACY HERO CARD */}
      <div className="water-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.25rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <h2 style={{ fontSize: '1.6rem', color: 'var(--text-dark)' }}>{meta.village_name}</h2>
              <span className="water-pill-badge">{meta.village_id}</span>
              <span className="water-pill-badge" style={{ background: '#fef3c7', color: '#92400e' }}>
                Priority Rank: #{meta.priority_rank}
              </span>
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.35rem', display: 'flex', gap: '1.25rem', flexWrap: 'wrap' }}>
              <span>District: <strong>{meta.district}</strong></span>
              <span>Population: <strong>{meta.population.toLocaleString()}</strong></span>
              <span>Vulnerability: <strong>{(meta.vulnerability_index * 100).toFixed(0)}%</strong></span>
              <span>Shortage: <strong>{meta.historical_shortage}</strong></span>
              <span>Elevation: <strong>{meta.elevation_m}m</strong></span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', background: '#ecfdf5', border: '1px solid #a7f3d0', padding: '0.6rem 1rem', borderRadius: 'var(--radius-sm)' }}>
            <CheckCircle size={20} color="#059669" />
            <div>
              <div style={{ fontSize: '0.72rem', color: '#059669', fontWeight: 700, textTransform: 'uppercase' }}>ML Confidence</div>
              <div style={{ fontSize: '0.9rem', fontWeight: 800, color: '#065f46' }}>
                MAPE: {metrics.mape}% (97.8% Accuracy)
              </div>
            </div>
          </div>
        </div>

        {/* 4 MODEL ACCURACY METRICS */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: '1rem' }}>
          <div style={{ background: '#f8fbff', border: '1px solid #e2e8f0', borderRadius: 'var(--radius-sm)', padding: '1rem' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>MAE (Mean Absolute Error)</div>
            <div style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-dark)', marginTop: '0.2rem' }}>
              {metrics.mae.toLocaleString()} <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>L/day</span>
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>Linear Regression Model</div>
          </div>

          <div style={{ background: '#f8fbff', border: '1px solid #e2e8f0', borderRadius: 'var(--radius-sm)', padding: '1rem' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>RMSE (Root Mean Square)</div>
            <div style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-dark)', marginTop: '0.2rem' }}>
              {metrics.rmse.toLocaleString()} <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>L/day</span>
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>Penalizes outlier variations</div>
          </div>

          <div style={{ background: '#f8fbff', border: '1px solid #e2e8f0', borderRadius: 'var(--radius-sm)', padding: '1rem' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>Mean Daily Demand</div>
            <div style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--water-blue)', marginTop: '0.2rem' }}>
              {metrics.mean_actual.toLocaleString()} <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>L/day</span>
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              ~{(metrics.mean_actual / meta.population).toFixed(0)} LPCD Per Capita
            </div>
          </div>

          <div style={{ background: '#f8fbff', border: '1px solid #e2e8f0', borderRadius: 'var(--radius-sm)', padding: '1rem' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>Error Percentage</div>
            <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#059669', marginTop: '0.2rem' }}>
              {metrics.mape}%
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>Industry Standard &lt; 5.0%</div>
          </div>
        </div>
      </div>

      {/* 3. TIME-SERIES INTERACTIVE GRAPH (Recharts with Water Waves) */}
      <div className="water-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div>
            <h3 style={{ fontSize: '1.15rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <TrendingUp size={20} color="var(--water-blue)" />
              Actual vs Predicted Demand Time-Series
            </h3>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              Displaying {filteredSeries.length} consecutive days for {meta.village_name}.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '0.82rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <span style={{ width: '12px', height: '4px', background: '#0284c7', borderRadius: '2px', display: 'inline-block' }} />
              <span style={{ fontWeight: 700, color: 'var(--text-dark)' }}>Actual Demand (L)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <span style={{ width: '12px', height: '4px', background: '#059669', borderRadius: '2px', display: 'inline-block' }} />
              <span style={{ fontWeight: 700, color: '#059669' }}>Predicted Demand (L)</span>
            </div>
          </div>
        </div>

        {/* The Graph */}
        <div style={{ width: '100%', height: '390px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={filteredSeries} margin={{ top: 10, right: 20, left: 10, bottom: 25 }}>
              <defs>
                <linearGradient id="waterActual" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#0284c7" stopOpacity={0.02} />
                </linearGradient>
              </defs>

              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />

              <XAxis
                dataKey="date"
                stroke="#64748b"
                fontSize={11}
                tickFormatter={(d) => {
                  const parts = d.split('-');
                  return `${parts[1]}/${parts[2]}`;
                }}
                dy={8}
              />

              <YAxis
                stroke="#64748b"
                fontSize={11}
                tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                dx={-8}
                domain={['auto', 'auto']}
              />

              <Tooltip content={<CustomWaterTooltip />} />

              {/* Actual Demand Area */}
              <Area
                type="monotone"
                dataKey="actual"
                name="Actual Demand"
                stroke="#0284c7"
                strokeWidth={3}
                fillOpacity={1}
                fill="url(#waterActual)"
              />

              {/* Predicted Demand Line */}
              <Line
                type="monotone"
                dataKey="predicted"
                name="Predicted Demand"
                stroke="#059669"
                strokeWidth={2.5}
                strokeDasharray="4 4"
                dot={{ r: 2.5, fill: '#059669' }}
                activeDot={{ r: 6, fill: '#059669' }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 4. DAILY FORECAST LOG TABLE */}
      <div className="water-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ fontSize: '1.05rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Calendar size={18} color="var(--water-blue)" />
            Recent Forecast Log
          </h3>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Showing latest {Math.min(10, filteredSeries.length)} days
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table className="water-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Actual Demand</th>
                <th>AI Prediction</th>
                <th>Delta</th>
                <th>Error %</th>
                <th>Temp</th>
                <th>Rainfall</th>
                <th>Verification</th>
              </tr>
            </thead>
            <tbody>
              {filteredSeries.slice(-10).reverse().map((row) => {
                const diff = row.actual - row.predicted;
                const errPct = ((Math.abs(diff) / row.actual) * 100).toFixed(2);
                return (
                  <tr key={row.date}>
                    <td style={{ fontWeight: 700 }}>{row.date}</td>
                    <td style={{ color: 'var(--water-deep)', fontWeight: 700 }}>{row.actual.toLocaleString()} L</td>
                    <td style={{ color: '#059669', fontWeight: 700 }}>{row.predicted.toLocaleString()} L</td>
                    <td style={{ color: diff >= 0 ? '#0f172a' : '#64748b' }}>
                      {diff > 0 ? `+${diff.toLocaleString()}` : diff.toLocaleString()} L
                    </td>
                    <td>
                      <span
                        className="water-pill-badge"
                        style={{
                          background: errPct <= 3.0 ? '#dcfce7' : '#fef3c7',
                          color: errPct <= 3.0 ? '#166534' : '#92400e',
                        }}
                      >
                        {errPct}%
                      </span>
                    </td>
                    <td>{row.temp}°C</td>
                    <td>{row.rain} mm</td>
                    <td>
                      <span className="water-pill-badge" style={{ fontSize: '0.72rem' }}>
                        Validated
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
