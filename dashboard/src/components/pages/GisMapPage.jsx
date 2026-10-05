import React, { useState } from 'react';
import {
  MapPin,
  Layers,
  Droplets,
  Activity,
  AlertTriangle,
  X,
  Sliders,
  CheckCircle2,
  ShieldAlert,
  Maximize2,
  Save,
  SlidersHorizontal
} from 'lucide-react';
import { api } from '../../api/client';
import { useLiveData } from '../../api/useLiveData';
import DataWrapper from '../DataWrapper';
import {
  STORAGE_TANKS,
} from '../../data/waterData';

export default function GisMapPage({ onNavigateToPage }) {
  const [selectedVillage, setSelectedVillage] = useState(null);
  const [filterMode, setFilterMode] = useState('all');
  const [mapSliderAllocated, setMapSliderAllocated] = useState(0);
  const [mapSaving, setMapSaving] = useState(false);

  const { data: villagesRaw, loading: vLoad, error: vErr, refetch: refetchVillages } = useLiveData(api.villages);
  const { data: pipelinesRaw, loading: pLoad, error: pErr } = useLiveData(api.pipelines);
  const { data: sourcesRaw, loading: sLoad, error: sErr } = useLiveData(api.waterSources);

  const loading = vLoad || pLoad || sLoad;
  const error = vErr || pErr || sErr;

  const handleSelectVillage = (v) => {
    setSelectedVillage(v);
    setMapSliderAllocated(v.allocatedKL);
  };

  const handleSaveMapQuota = async () => {
    if (!selectedVillage) return;
    setMapSaving(true);
    try {
      const res = await api.adjustAllocation(selectedVillage.id, mapSliderAllocated);
      await refetchVillages();
      const newShortage = res.shortage_kl ?? Math.max(0, selectedVillage.demandKL - mapSliderAllocated);
      const newSatisfaction = res.satisfaction_pct ?? Math.min(100, Math.round((mapSliderAllocated / selectedVillage.demandKL) * 1000) / 10);
      const newStatus = res.status_tier ?? ((mapSliderAllocated / selectedVillage.demandKL) < 0.8 ? 'High' : (mapSliderAllocated / selectedVillage.demandKL) < 0.92 ? 'Medium' : 'Low');

      setSelectedVillage(prev => prev ? ({
        ...prev,
        allocatedKL: mapSliderAllocated,
        shortageKL: newShortage,
        satisfaction: newSatisfaction,
        status: newStatus,
      }) : null);
    } catch (err) {
      console.error('Failed to save allocation from map:', err);
      alert(`Error saving to PostgreSQL: ${err.message}`);
    } finally {
      setMapSaving(false);
    }
  };

  // Map API villages to shape the existing JSX uses
  // The GIS map uses x/y canvas coords — we derive them from lat/lon or keep index-based positioning
  const VILLAGES_DATABASE = (villagesRaw ?? []).map((v, i) => ({
    id: v.id,
    name: v.name,
    population: v.population,
    priority: v.priorityScore >= 0.7 ? 'P1 Critical' : v.priorityScore >= 0.4 ? 'P2 High' : 'P3 Standard',
    demandKL: v.demandL != null ? +(v.demandL / 1000).toFixed(1) : 0,
    allocatedKL: v.allocatedL != null ? +(v.allocatedL / 1000).toFixed(1) : 0,
    shortageKL: v.shortageL != null ? +(v.shortageL / 1000).toFixed(1) : 0,
    satisfaction: v.satisfactionPct ?? 0,
    status: v.status,
    latitude: v.latitude,
    longitude: v.longitude,
    // Map lat/lon to SVG canvas (approx bounds for Ahmednagar district)
    x: v.longitude != null ? Math.round(((v.longitude - 73.5) / (75.5 - 73.5)) * 700) : (i % 10) * 70 + 30,
    y: v.latitude != null ? Math.round(((20.5 - v.latitude) / (20.5 - 18.5)) * 520) : Math.floor(i / 10) * 100 + 40,
  }));

  // Map pipelines
  const PIPELINES_DATA = (pipelinesRaw ?? []).map(p => ({
    id: p.id,
    route: p.route,
    maxCapacityLPS: p.capacityLPerDay != null ? +(p.capacityLPerDay / 86400).toFixed(1) : 0,
    currentFlowLPS: p.currentFlowLPerDay != null ? +(p.currentFlowLPerDay / 86400).toFixed(1) : 0,
    utilization: p.utilizationPct ?? 0,
    status: p.status,
    leakDetected: p.leakDetected,
    source: p.sourceNode,
    target: p.destinationNode,
  }));

  // Map water sources
  const WATER_SOURCES = (sourcesRaw ?? []).map((s, i) => ({
    id: s.id,
    name: s.name,
    type: s.type,
    capacityML: s.totalCapacityL != null ? +(s.totalCapacityL / 1e6).toFixed(0) : 0,
    currentML: s.currentStorageL != null ? +(s.currentStorageL / 1e6).toFixed(0) : 0,
    dailyFlowML: s.dailySupplyL != null ? +(s.dailySupplyL / 1e6).toFixed(1) : 0,
    x: [220, 680, 30][i] ?? 100,
    y: [20, 60, 320][i] ?? 100,
  }));

  // Filtered villages
  const visibleVillages = VILLAGES_DATABASE.filter(v => {
    if (filterMode === 'critical') return v.status === 'High' || v.status === 'Medium';
    return true;
  });

  return (
    <DataWrapper loading={loading} error={error} pageName="GIS network">
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Map Control Bar */}
      <div className="glass-panel" style={{ padding: '1rem 1.75rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', color: '#0f172a', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <MapPin size={22} color="#0284c7" />
            <span>District Hydro-Spatial GIS Network</span>
          </h2>
          <p style={{ fontSize: '0.82rem', color: '#64748b' }}>
            Interactive vector topology: Reservoirs • Storage Sub-Tanks • Distribution Pipelines • Village Shortage Heatmap
          </p>
        </div>

        {/* Legend & Filter Pills */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#f8fafc', padding: '0.25rem 0.65rem', borderRadius: '9999px', border: '1px solid #e2e8f0', fontSize: '0.75rem' }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', color: '#15803d' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981' }} /> &lt;10% Low
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', color: '#b45309' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#f59e0b' }} /> 10-25% Med
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', color: '#b91c1c' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ef4444' }} /> &gt;25% High
            </span>
          </div>

          {/* Filter options */}
          <div style={{ display: 'flex', gap: '0.35rem' }}>
            {[
              { id: 'all', label: 'All 45 Nodes' },
              { id: 'critical', label: 'High Deficit Only' },
            ].map(f => (
              <button
                key={f.id}
                onClick={() => setFilterMode(f.id)}
                style={{
                  padding: '0.35rem 0.75rem',
                  borderRadius: '9999px',
                  border: filterMode === f.id ? 'none' : '1px solid #cbd5e1',
                  background: filterMode === f.id ? '#0284c7' : '#ffffff',
                  color: filterMode === f.id ? '#ffffff' : '#475569',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  cursor: 'pointer'
                }}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* SVG Canvas Map Container */}
      <div className="glass-panel" style={{ padding: '1.5rem', position: 'relative', overflow: 'hidden' }}>
        <div style={{ width: '100%', height: '560px', background: 'radial-gradient(circle at 50% 50%, #0c1a2e 0%, #030a14 100%)', borderRadius: '20px', position: 'relative', overflow: 'hidden', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
          {/* Subtle Grid Lines Overlay */}
          <svg width="100%" height="100%" viewBox="0 0 800 560" style={{ display: 'block' }}>
            <defs>
              <pattern id="gridPattern" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255, 255, 255, 0.05)" strokeWidth="1" />
              </pattern>

              {/* Animated Dash Array for Pipeline Flow */}
              <linearGradient id="flowGradNormal" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#38bdf8" />
                <stop offset="100%" stopColor="#0284c7" />
              </linearGradient>
              <linearGradient id="flowGradWarning" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#fbbf24" />
                <stop offset="100%" stopColor="#f59e0b" />
              </linearGradient>
              <linearGradient id="flowGradLeak" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#f87171" />
                <stop offset="100%" stopColor="#ef4444" />
              </linearGradient>
            </defs>

            {/* Background Grid */}
            <rect width="800" height="560" fill="url(#gridPattern)" />

            {/* Pipeline Polylines with Flow Indicators */}
            {/* Godavari to Central */}
            <line x1="220" y1="35" x2="360" y2="220" stroke="#f59e0b" strokeWidth="4" strokeDasharray="8 6" opacity="0.8" />
            {/* Jayakwadi to East-B */}
            <line x1="680" y1="75" x2="560" y2="220" stroke="#38bdf8" strokeWidth="4" strokeDasharray="8 6" opacity="0.8" />
            {/* Kashti Well to West-Main */}
            <line x1="45" y1="320" x2="90" y2="270" stroke="#38bdf8" strokeWidth="3" opacity="0.8" />
            {/* West-Main to Central */}
            <line x1="90" y1="270" x2="360" y2="220" stroke="#38bdf8" strokeWidth="3" strokeDasharray="6 4" opacity="0.7" />
            {/* Central to South-A */}
            <line x1="360" y1="220" x2="260" y2="380" stroke="#f59e0b" strokeWidth="4" strokeDasharray="8 6" opacity="0.8" />
            {/* Central to South-B */}
            <line x1="360" y1="220" x2="510" y2="440" stroke="#38bdf8" strokeWidth="3" strokeDasharray="6 4" opacity="0.7" />
            {/* Central to North-B */}
            <line x1="360" y1="220" x2="280" y2="90" stroke="#38bdf8" strokeWidth="3" strokeDasharray="6 4" opacity="0.7" />
            {/* North-A to Rampur (Leak Pipeline) */}
            <line x1="200" y1="150" x2="180" y2="140" stroke="#ef4444" strokeWidth="4" strokeDasharray="4 4" opacity="0.9" />

            {/* Pipeline Feeder Lines to Villages */}
            {visibleVillages.map((v) => {
              // Find matching tank coordinate
              const tank = STORAGE_TANKS.find(t => t.name === v.tank) || STORAGE_TANKS[0];
              return (
                <line
                  key={`feed-${v.id}`}
                  x1={tank.x}
                  y1={tank.y}
                  x2={v.x}
                  y2={v.y}
                  stroke="rgba(56, 189, 248, 0.25)"
                  strokeWidth="1.2"
                />
              );
            })}

            {/* 1. Water Sources Nodes */}
            {WATER_SOURCES.map((src) => (
              <g key={src.id} transform={`translate(${src.x}, ${src.y})`}>
                <circle r="18" fill="rgba(2, 132, 199, 0.35)" stroke="#38bdf8" strokeWidth="2" />
                <circle r="10" fill="#0284c7" />
                <text x="0" y="30" textAnchor="middle" fill="#7dd3fc" fontSize="11" fontWeight="700">
                  {src.name}
                </text>
                <text x="0" y="42" textAnchor="middle" fill="#94a3b8" fontSize="9">
                  {src.currentML.toLocaleString()} ML
                </text>
              </g>
            ))}

            {/* 2. Storage Tanks Nodes */}
            {STORAGE_TANKS.map((tank) => (
              <g key={tank.id} transform={`translate(${tank.x}, ${tank.y})`}>
                {/* Tank Outer Ring */}
                <rect x="-16" y="-16" width="32" height="32" rx="8" fill="rgba(15, 23, 42, 0.85)" stroke={tank.status === 'Alert' ? '#f59e0b' : '#38bdf8'} strokeWidth="2" />
                <text x="0" y="4" textAnchor="middle" fill="#ffffff" fontSize="9" fontWeight="800">
                  {Math.round(tank.fillPct)}%
                </text>
                <text x="0" y="27" textAnchor="middle" fill="#cbd5e1" fontSize="10" fontWeight="600">
                  {tank.name}
                </text>
              </g>
            ))}

            {/* 3. Village Nodes (Color-Coded by Shortage) */}
            {visibleVillages.map((v) => {
              const nodeColor = v.status === 'High' ? '#ef4444' : v.status === 'Medium' ? '#f59e0b' : '#10b981';
              const isSelected = selectedVillage && selectedVillage.id === v.id;

              return (
                <g
                  key={v.id}
                  transform={`translate(${v.x}, ${v.y})`}
                  style={{ cursor: 'pointer' }}
                  onClick={() => handleSelectVillage(v)}
                >
                  {/* Pulsing ring for High shortage nodes */}
                  {v.status === 'High' && (
                    <circle r="14" fill="none" stroke="#ef4444" strokeWidth="1.5" opacity="0.6">
                      <animate attributeName="r" values="7;18;7" dur="2s" repeatCount="indefinite" />
                      <animate attributeName="opacity" values="0.8;0.1;0.8" dur="2s" repeatCount="indefinite" />
                    </circle>
                  )}

                  {/* Village Point */}
                  <circle
                    r={isSelected ? "9" : "6"}
                    fill={nodeColor}
                    stroke="#ffffff"
                    strokeWidth={isSelected ? "2.5" : "1.5"}
                  />

                  {/* Label */}
                  <text
                    x="0"
                    y="-10"
                    textAnchor="middle"
                    fill={isSelected ? "#38bdf8" : "#e2e8f0"}
                    fontSize={isSelected ? "11" : "9"}
                    fontWeight={isSelected ? "800" : "500"}
                  >
                    {v.name}
                  </text>
                </g>
              );
            })}
          </svg>

          {/* Interactive Legend Floating Badge */}
          <div style={{ position: 'absolute', bottom: '1rem', left: '1rem', background: 'rgba(15, 23, 42, 0.85)', backdropFilter: 'blur(8px)', border: '1px solid rgba(255, 255, 255, 0.15)', borderRadius: '12px', padding: '0.65rem 1rem', color: '#cbd5e1', fontSize: '0.75rem', display: 'flex', gap: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <span style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#0284c7' }} /> Water Source
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <span style={{ width: '12px', height: '12px', borderRadius: '3px', background: '#1e293b', border: '1px solid #38bdf8' }} /> Storage Tank
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <span style={{ width: '16px', height: '3px', background: '#38bdf8' }} /> Pipeline
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <span style={{ width: '16px', height: '3px', background: '#ef4444', borderTop: '2px dashed #ef4444' }} /> Leak Telemetry Alert
            </div>
          </div>
        </div>
      </div>

      {/* Village Details Flyout Modal */}
      {selectedVillage && (
        <div className="modal-backdrop" onClick={() => setSelectedVillage(null)}>
          <div
            className="glass-panel"
            style={{ width: '100%', maxWidth: '480px', padding: '1.75rem', position: 'relative' }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close Button */}
            <button
              onClick={() => setSelectedVillage(null)}
              style={{ position: 'absolute', top: '1.25rem', right: '1.25rem', background: '#f1f5f9', border: 'none', borderRadius: '50%', width: '32px', height: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}
            >
              <X size={16} />
            </button>

            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
              <div
                style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: '12px',
                  background: selectedVillage.status === 'High' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(2, 132, 199, 0.15)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: selectedVillage.status === 'High' ? '#ef4444' : '#0284c7',
                }}
              >
                <MapPin size={24} />
              </div>
              <div>
                <h3 style={{ fontSize: '1.35rem', fontWeight: 800, color: '#0f172a' }}>{selectedVillage.name}</h3>
                <span style={{ fontSize: '0.75rem', background: '#e0f2fe', color: '#0369a1', padding: '0.15rem 0.5rem', borderRadius: '9999px', fontWeight: 700 }}>
                  {selectedVillage.priority}
                </span>
              </div>
            </div>

            {/* Metrics Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', margin: '1.25rem 0' }}>
              <div style={{ background: '#f8fafc', padding: '0.85rem', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Population</div>
                <div style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0f172a' }}>{selectedVillage.population.toLocaleString()}</div>
              </div>
              <div style={{ background: '#f8fafc', padding: '0.85rem', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Assigned Storage</div>
                <div style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0284c7' }}>{selectedVillage.tank}</div>
              </div>
              <div style={{ background: '#f8fafc', padding: '0.85rem', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Predicted Demand</div>
                <div style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0f172a' }}>{selectedVillage.demandKL} kL</div>
              </div>
              <div style={{ background: '#f8fafc', padding: '0.85rem', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Satisfaction Rate</div>
                <div style={{ fontSize: '1.15rem', fontWeight: 800, color: selectedVillage.satisfaction >= 90 ? '#059669' : '#dc2626' }}>
                  {selectedVillage.satisfaction}%
                </div>
              </div>
            </div>

            {/* Shortage Bar */}
            <div style={{ background: selectedVillage.status === 'High' ? '#fef2f2' : '#f0fdf4', padding: '1rem', borderRadius: '12px', border: `1px solid ${selectedVillage.status === 'High' ? '#fecaca' : '#bbf7d0'}`, marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.82rem', fontWeight: 700, color: selectedVillage.status === 'High' ? '#991b1b' : '#166534' }}>
                <span>Shortage Deficit: {selectedVillage.shortageKL} kL</span>
                <span>Status: {selectedVillage.status} Shortage</span>
              </div>
              <div style={{ width: '100%', height: '6px', background: 'rgba(0,0,0,0.1)', borderRadius: '9999px', overflow: 'hidden' }}>
                <div style={{ width: `${selectedVillage.satisfaction}%`, height: '100%', background: selectedVillage.status === 'High' ? '#ef4444' : '#10b981' }} />
              </div>
            </div>

            {/* Direct Quota Adjustment on Map */}
            <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '12px', border: '1px solid #e2e8f0', marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#334155', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  <SlidersHorizontal size={15} color="#0284c7" />
                  <span>Adjust Allocation Quota:</span>
                </span>
                <span style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0284c7' }}>{mapSliderAllocated} kL</span>
              </div>
              <input
                type="range"
                min="0"
                max={Math.max(10, Math.round(selectedVillage.demandKL * 1.2))}
                step="5"
                value={mapSliderAllocated}
                onChange={(e) => setMapSliderAllocated(Number(e.target.value))}
                style={{ width: '100%', accentColor: '#0284c7', height: '6px', cursor: 'pointer' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: '#94a3b8', marginTop: '0.3rem' }}>
                <span>0 kL (0%)</span>
                <span>Demand: {selectedVillage.demandKL} kL (100%)</span>
                <span>Surplus: {Math.round(selectedVillage.demandKL * 1.2)} kL</span>
              </div>

              {/* Preview of impact */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.65rem', paddingTop: '0.5rem', borderTop: '1px dashed #cbd5e1', fontSize: '0.78rem' }}>
                <span style={{ color: '#64748b' }}>
                  Expected: <strong style={{ color: mapSliderAllocated < selectedVillage.demandKL * 0.8 ? '#dc2626' : '#059669' }}>
                    {Math.min(100, Math.round((mapSliderAllocated / (selectedVillage.demandKL || 1)) * 1000) / 10)}% Satisfaction
                  </strong>
                </span>
                <button
                  onClick={handleSaveMapQuota}
                  disabled={mapSaving}
                  style={{
                    padding: '0.45rem 0.9rem',
                    background: mapSaving ? '#64748b' : 'linear-gradient(135deg, #0284c7, #06b6d4)',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '8px',
                    fontSize: '0.78rem',
                    fontWeight: 700,
                    cursor: mapSaving ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                  }}
                >
                  <Save size={13} /> {mapSaving ? 'Saving...' : 'Save & Update Map'}
                </button>
              </div>
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button
                onClick={() => {
                  setSelectedVillage(null);
                  onNavigateToPage('allocation');
                }}
                style={{ flex: 1, padding: '0.65rem', background: '#0284c7', color: '#ffffff', border: 'none', borderRadius: '10px', fontSize: '0.85rem', fontWeight: 700, cursor: 'pointer' }}
              >
                Adjust Quota in Allocation
              </button>
              <button
                onClick={() => {
                  setSelectedVillage(null);
                  onNavigateToPage('prediction');
                }}
                style={{ padding: '0.65rem 1rem', background: '#f1f5f9', color: '#334155', border: '1px solid #cbd5e1', borderRadius: '10px', fontSize: '0.85rem', fontWeight: 600, cursor: 'pointer' }}
              >
                Forecast
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
    </DataWrapper>
  );
}
