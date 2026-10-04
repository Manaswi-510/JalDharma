import React from 'react';
import {
  Droplets,
  TrendingUp,
  CheckCircle2,
  AlertTriangle,
  Scale,
  Percent,
  Server,
  ShieldCheck,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import overviewData from '../data/overview.json';

export default function OverviewPage({ onNavigateToVillage }) {
  const {
    totalWaterAvailableL,
    totalPredictedDemandL,
    totalAllocatedL,
    totalShortageL,
    averageSatisfactionPct,
    fairnessIndex,
    giniCoefficient,
    minServiceCompliancePct,
    waterSources,
    topPriorityVillages,
    allocationStrategies,
    snapshotDate,
  } = overviewData;

  const fulfillmentRate = ((totalAllocatedL / totalPredictedDemandL) * 100).toFixed(1);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* 1. TOP WATER GREETING BANNER (Like Reference Image 1) */}
      <div className="water-welcome-banner">
        <div className="welcome-text">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
            <span className="water-pill-badge" style={{ background: '#e0f2fe', color: '#0369a1' }}>
              <Droplets size={14} />
              JAL DHARMA AI • Water Command
            </span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-light)' }}>
              Date: {snapshotDate}
            </span>
          </div>
          <h2>JAL DHARMA 💧</h2>
          <p>AI-Powered Water Demand Prediction & Equitable Allocation System</p>
        </div>

        <video
          autoPlay
          loop
          muted
          playsInline
          className="welcome-banner-img"
          style={{ width: '220px', height: '95px', objectFit: 'cover' }}
        >
          <source src="/background/animekpopcy_ssspin.io_1791119012.mp4" type="video/mp4" />
        </video>
      </div>

      {/* 2. THE 6 CORE REQUIREMENTS (PDF Page 21 Checklist) */}
      <div className="water-metrics-grid">
        {/* Metric 1: Total Water Available */}
        <div className="water-metric-box">
          <div className="water-metric-top">
            <span className="water-metric-label">1. Total Water Available</span>
            <div className="water-metric-icon">
              <Droplets size={20} />
            </div>
          </div>
          <div>
            <div className="water-metric-val">
              {(totalWaterAvailableL / 1e6).toFixed(1)} <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>ML/d</span>
            </div>
            <div className="water-metric-sub">
              <span>{totalWaterAvailableL.toLocaleString()} Litres/day (3 Reservoirs)</span>
            </div>
          </div>
        </div>

        {/* Metric 2: Total Predicted Demand */}
        <div className="water-metric-box">
          <div className="water-metric-top">
            <span className="water-metric-label">2. Predicted Demand</span>
            <div className="water-metric-icon" style={{ background: '#ede9fe', color: '#7c3aed' }}>
              <TrendingUp size={20} />
            </div>
          </div>
          <div>
            <div className="water-metric-val">
              {(totalPredictedDemandL / 1e6).toFixed(2)} <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>ML/d</span>
            </div>
            <div className="water-metric-sub">
              <span>{totalPredictedDemandL.toLocaleString()} L regional requirement</span>
            </div>
          </div>
        </div>

        {/* Metric 3: Total Allocated */}
        <div className="water-metric-box">
          <div className="water-metric-top">
            <span className="water-metric-label">3. Total Allocated</span>
            <div className="water-metric-icon" style={{ background: '#dcfce7', color: '#16a34a' }}>
              <CheckCircle2 size={20} />
            </div>
          </div>
          <div>
            <div className="water-metric-val" style={{ color: '#16a34a' }}>
              {(totalAllocatedL / 1e6).toFixed(2)} <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>ML/d</span>
            </div>
            <div className="water-metric-sub" style={{ color: '#16a34a', fontWeight: 600 }}>
              <span>{fulfillmentRate}% fulfillment rate</span>
            </div>
          </div>
        </div>

        {/* Metric 4: Total Shortage */}
        <div className="water-metric-box">
          <div className="water-metric-top">
            <span className="water-metric-label">4. Total Shortage</span>
            <div className="water-metric-icon" style={{ background: '#fee2e2', color: '#dc2626' }}>
              <AlertTriangle size={20} />
            </div>
          </div>
          <div>
            <div className="water-metric-val" style={{ color: '#dc2626' }}>
              {(totalShortageL / 1e6).toFixed(2)} <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>ML/d</span>
            </div>
            <div className="water-metric-sub" style={{ color: '#dc2626' }}>
              <span>{totalShortageL.toLocaleString()} L unmet deficit</span>
            </div>
          </div>
        </div>

        {/* Metric 5: Average Satisfaction */}
        <div className="water-metric-box">
          <div className="water-metric-top">
            <span className="water-metric-label">5. Avg Satisfaction</span>
            <div className="water-metric-icon" style={{ background: '#fef3c7', color: '#d97706' }}>
              <Percent size={20} />
            </div>
          </div>
          <div>
            <div className="water-metric-val">
              {averageSatisfactionPct}%
            </div>
            <div className="water-metric-sub">
              <span className="water-pill-badge" style={{ background: '#dcfce7', color: '#166534', padding: '0.15rem 0.5rem' }}>
                {minServiceCompliancePct}% villages &ge; 70% service
              </span>
            </div>
          </div>
        </div>

        {/* Metric 6: Fairness Index */}
        <div className="water-metric-box">
          <div className="water-metric-top">
            <span className="water-metric-label">6. Fairness Index</span>
            <div className="water-metric-icon" style={{ background: '#e0f2fe', color: '#0284c7' }}>
              <Scale size={20} />
            </div>
          </div>
          <div>
            <div className="water-metric-val" style={{ color: '#0284c7' }}>
              {fairnessIndex.toFixed(4)}
            </div>
            <div className="water-metric-sub">
              <span>Jain's Index (Ideal = 1.0) • Gini: {giniCoefficient.toFixed(3)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 3. WATER DROPLET CONSUMPTION & CAPSULE GAUGES (Exact look from Image 1!) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '1.25rem' }}>
        {/* Droplet Water Consumption Card */}
        <div className="water-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <h3 style={{ fontSize: '1.05rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Droplets size={18} color="var(--water-blue)" />
              Daily Water Allocation & Fulfillment
            </h3>
            <span className="water-pill-badge">Live System</span>
          </div>

          <div className="droplet-gauge-container">
            <div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Delivered Today</div>
              <div style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--text-dark)' }}>
                {(totalAllocatedL / 1e6).toFixed(2)} <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>Million Litres</span>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                Required Demand: <strong>{(totalPredictedDemandL / 1e6).toFixed(2)} ML</strong>
              </div>
              <div style={{ fontSize: '0.8rem', color: '#16a34a', fontWeight: 600, marginTop: '0.2rem' }}>
                ✓ {fulfillmentRate}% overall fulfillment
              </div>
            </div>

            {/* Visual Droplet Graphic (Like Image 1) */}
            <div className="droplet-graphic">
              <div
                className="droplet-fill"
                style={{ height: `${fulfillmentRate}%` }}
              />
              <span className="droplet-percent-text">{fulfillmentRate}%</span>
            </div>
          </div>

          {/* Linear bar */}
          <div style={{ marginTop: '0.75rem', height: '10px', background: '#f1f5f9', borderRadius: '6px', overflow: 'hidden' }}>
            <div
              style={{
                width: `${fulfillmentRate}%`,
                height: '100%',
                background: 'linear-gradient(90deg, #38bdf8, #0284c7)',
                borderRadius: '6px',
              }}
            />
          </div>
        </div>

        {/* Capsule Water Gauges (Like Temperature & Pressure in Image 1) */}
        <div className="water-card" style={{ display: 'flex', justifyContent: 'space-around', alignItems: 'center' }}>
          {/* Capsule 1: Deliverability Ratio */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)' }}>Supply Capacity</div>
            <div className="capsule-gauge">
              <div className="capsule-fill" style={{ height: '88%' }} />
            </div>
            <div style={{ fontWeight: 800, fontSize: '0.95rem', color: 'var(--text-dark)' }}>
              240 <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>ML/d</span>
            </div>
          </div>

          {/* Capsule 2: Satisfaction Ratio */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)' }}>Satisfaction</div>
            <div className="capsule-gauge">
              <div className="capsule-fill" style={{ height: `${averageSatisfactionPct}%` }} />
            </div>
            <div style={{ fontWeight: 800, fontSize: '0.95rem', color: 'var(--water-blue)' }}>
              {averageSatisfactionPct}%
            </div>
          </div>

          {/* Capsule 3: Water Justice Index */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)' }}>Jain's Fairness</div>
            <div className="capsule-gauge">
              <div className="capsule-fill" style={{ height: `${(fairnessIndex * 100).toFixed(0)}%`, background: 'linear-gradient(180deg, #10b981, #059669)' }} />
            </div>
            <div style={{ fontWeight: 800, fontSize: '0.95rem', color: '#10b981' }}>
              {fairnessIndex.toFixed(2)}
            </div>
          </div>
        </div>
      </div>

      {/* 4. PRIMARY WATER SOURCES (Reservoir Levels) */}
      <div className="water-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ fontSize: '1.05rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Server size={18} color="var(--water-blue)" />
            Primary Water Intake Sources & Storage Levels
          </h3>
          <span className="water-pill-badge">{waterSources.length} Active Sources</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
          {waterSources.map((src) => {
            const storagePct = ((src.storageL / src.capacityL) * 100).toFixed(0);
            return (
              <div
                key={src.id}
                style={{
                  background: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: 'var(--radius-sm)',
                  padding: '1rem',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.35rem' }}>
                  <div style={{ fontWeight: 700, fontSize: '0.92rem' }}>{src.name}</div>
                  <span className="water-pill-badge" style={{ background: '#dcfce7', color: '#166534', padding: '0.15rem 0.5rem', fontSize: '0.7rem' }}>
                    {src.status}
                  </span>
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                  {src.type} • Daily Deliverable: <strong>{(src.dailySupplyL / 1e6).toFixed(0)} ML</strong>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>
                  <span>Storage: {(src.storageL / 1e9).toFixed(1)}B L</span>
                  <span style={{ fontWeight: 700, color: 'var(--water-blue)' }}>{storagePct}% Full</span>
                </div>
                <div style={{ height: '6px', background: '#e2e8f0', borderRadius: '3px', overflow: 'hidden' }}>
                  <div
                    style={{
                      width: `${storagePct}%`,
                      height: '100%',
                      background: 'linear-gradient(90deg, #38bdf8, #0284c7)',
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 5. TOP HIGH-VULNERABILITY VILLAGES (Phase 18) */}
      <div className="water-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ fontSize: '1.05rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <ShieldCheck size={18} color="#d97706" />
            Top High-Vulnerability Villages (Water Justice Protection)
          </h3>
          <span className="water-pill-badge" style={{ background: '#fef3c7', color: '#92400e' }}>
            Phase 18 Priority Ranked
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table className="water-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Village Name</th>
                <th>Population</th>
                <th>Vulnerability Index</th>
                <th>Shortage History</th>
                <th>Priority Score</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {topPriorityVillages.map((v) => (
                <tr key={v.village_id}>
                  <td>
                    <span
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: '24px',
                        height: '24px',
                        borderRadius: '50%',
                        background: v.priority_rank <= 3 ? '#fee2e2' : '#fef3c7',
                        color: v.priority_rank <= 3 ? '#b91c1c' : '#b45309',
                        fontWeight: 800,
                        fontSize: '0.75rem',
                      }}
                    >
                      {v.priority_rank}
                    </span>
                  </td>
                  <td style={{ fontWeight: 700 }}>
                    {v.village_name} <span style={{ color: 'var(--text-light)', fontWeight: 400 }}>({v.village_id})</span>
                  </td>
                  <td>{v.population.toLocaleString()}</td>
                  <td>
                    <span
                      className="water-pill-badge"
                      style={{
                        background: v.vulnerability_index >= 0.8 ? '#fee2e2' : '#fef3c7',
                        color: v.vulnerability_index >= 0.8 ? '#991b1b' : '#92400e',
                      }}
                    >
                      {(v.vulnerability_index * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td>{v.historical_shortage}</td>
                  <td style={{ fontWeight: 700, color: 'var(--water-deep)' }}>
                    {v.priority_score.toFixed(3)}
                  </td>
                  <td>
                    <button
                      onClick={() => onNavigateToVillage(v.village_id)}
                      style={{
                        background: '#e0f2fe',
                        border: 'none',
                        color: '#0369a1',
                        padding: '0.35rem 0.75rem',
                        borderRadius: 'var(--radius-full)',
                        fontSize: '0.78rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.3rem',
                      }}
                    >
                      <span>Forecast</span>
                      <ArrowRight size={13} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 6. ALLOCATION STRATEGY SCORECARD (Phase 20) */}
      <div className="water-card">
        <h3 style={{ fontSize: '1.05rem', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Scale size={18} color="#059669" />
          Allocation Method Benchmark (Phase 20 Research Results)
        </h3>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
          Evaluated under 70% supply scarcity across 45 rural villages.
        </p>

        <div style={{ overflowX: 'auto' }}>
          <table className="water-table">
            <thead>
              <tr>
                <th>Strategy</th>
                <th>Objective Philosophy</th>
                <th>Fulfillment Rate</th>
                <th>Jain's Fairness</th>
                <th>Gini Index</th>
                <th>Weighted Shortage</th>
                <th>Recommendation</th>
              </tr>
            </thead>
            <tbody>
              {allocationStrategies.map((s) => (
                <tr key={s.strategy}>
                  <td style={{ fontWeight: 800, color: s.strategy === 'Equity-Aware' ? 'var(--water-deep)' : 'inherit' }}>
                    {s.strategy}
                  </td>
                  <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    {s.strategy === 'Proportional' && 'Strict egalitarian distribution according to demand ratio'}
                    {s.strategy === 'Max-Flow' && 'Greedy network throughput maximization (leaves peripheral nodes starved)'}
                    {s.strategy === 'Equity-Aware' && 'Water Justice: prioritizes vulnerable villages, minimizes human deprivation'}
                  </td>
                  <td>{s.fulfillmentPct.toFixed(1)}%</td>
                  <td>
                    <span className="water-pill-badge" style={{ background: s.fairness >= 0.85 ? '#dcfce7' : '#fef3c7', color: s.fairness >= 0.85 ? '#166534' : '#92400e' }}>
                      {s.fairness.toFixed(4)}
                    </span>
                  </td>
                  <td>{s.gini.toFixed(4)}</td>
                  <td style={{ fontWeight: s.strategy === 'Equity-Aware' ? 800 : 400, color: s.strategy === 'Equity-Aware' ? '#059669' : 'inherit' }}>
                    {s.weightedShortage.toLocaleString()} L
                  </td>
                  <td>
                    {s.strategy === 'Equity-Aware' ? (
                      <span className="water-pill-badge" style={{ background: '#dcfce7', color: '#166534' }}>
                        ★ Recommended
                      </span>
                    ) : (
                      <span className="water-pill-badge" style={{ background: '#f1f5f9', color: '#64748b' }}>
                        Baseline
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
