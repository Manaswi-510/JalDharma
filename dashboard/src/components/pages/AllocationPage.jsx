import React, { useState } from 'react';
import {
  SlidersHorizontal,
  Search,
  Filter,
  CheckCircle2,
  AlertTriangle,
  X,
  Save,
  RotateCcw,
  Sparkles,
  Droplets
} from 'lucide-react';
import { VILLAGES_DATABASE } from '../../data/waterData';

export default function AllocationPage() {
  const [villages, setVillages] = useState(VILLAGES_DATABASE);
  const [searchQuery, setSearchQuery] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('ALL');
  const [editingVillage, setEditingVillage] = useState(null);
  const [sliderAllocated, setSliderAllocated] = useState(0);

  // Filtered dataset
  const filteredVillages = villages.filter(v => {
    const matchesSearch = v.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesPriority = priorityFilter === 'ALL' || v.priority.startsWith(priorityFilter);
    return matchesSearch && matchesPriority;
  });

  const handleOpenAdjustModal = (village) => {
    setEditingVillage(village);
    setSliderAllocated(village.allocatedKL);
  };

  const handleSaveQuota = () => {
    if (!editingVillage) return;
    const newShortage = Math.max(0, editingVillage.demandKL - sliderAllocated);
    const newSatisfaction = Math.min(100, Math.round((sliderAllocated / editingVillage.demandKL) * 1000) / 10);
    const newStatus = newSatisfaction >= 90 ? 'Low' : newSatisfaction >= 75 ? 'Medium' : 'High';

    setVillages(prev => prev.map(v => {
      if (v.id === editingVillage.id) {
        return {
          ...v,
          allocatedKL: sliderAllocated,
          shortageKL: newShortage,
          satisfaction: newSatisfaction,
          status: newStatus,
        };
      }
      return v;
    }));

    setEditingVillage(null);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Header & Search/Filter Controls */}
      <div className="glass-panel" style={{ padding: '1.5rem 1.75rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.35rem', color: '#0f172a', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <SlidersHorizontal size={22} color="#8b5cf6" />
            <span>Village Water Allocation Ledgers</span>
          </h2>
          <p style={{ fontSize: '0.85rem', color: '#64748b' }}>
            Equitable distribution quotas computed via HiGHS LP Solver based on priority weightings
          </p>
        </div>

        {/* Search & Filters */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          {/* Search Box */}
          <div style={{ position: 'relative' }}>
            <Search size={16} color="#94a3b8" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="text"
              placeholder="Search village..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                padding: '0.5rem 1rem 0.5rem 2.25rem',
                borderRadius: '12px',
                border: '1px solid #cbd5e1',
                background: '#ffffff',
                fontSize: '0.85rem',
                outline: 'none',
                minWidth: '200px',
              }}
            />
          </div>

          {/* Priority Filter Buttons */}
          <div style={{ display: 'flex', gap: '0.35rem', background: '#f1f5f9', padding: '0.25rem', borderRadius: '12px' }}>
            {['ALL', 'P1', 'P2', 'P3'].map(p => (
              <button
                key={p}
                onClick={() => setPriorityFilter(p)}
                style={{
                  padding: '0.35rem 0.75rem',
                  borderRadius: '8px',
                  border: 'none',
                  background: priorityFilter === p ? '#8b5cf6' : 'transparent',
                  color: priorityFilter === p ? '#ffffff' : '#64748b',
                  fontSize: '0.78rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                {p === 'ALL' ? 'All Tiers' : `${p} Tier`}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Allocation Table */}
      <div className="glass-panel" style={{ padding: '1.25rem', overflowX: 'auto' }}>
        <table className="glass-table">
          <thead>
            <tr>
              <th>Village Name</th>
              <th>Priority Tier</th>
              <th>Predicted Demand</th>
              <th>Allocated Quota</th>
              <th>Shortage</th>
              <th>Satisfaction Rate</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredVillages.map((v) => {
              const priorityColor = v.priority.startsWith('P1') ? '#ef4444' : v.priority.startsWith('P2') ? '#f59e0b' : '#10b981';
              const satisfactionColor = v.satisfaction >= 90 ? '#10b981' : v.satisfaction >= 75 ? '#f59e0b' : '#ef4444';

              return (
                <tr key={v.id}>
                  <td>
                    <div style={{ fontWeight: 700, color: '#0f172a' }}>{v.name}</div>
                    <div style={{ fontSize: '0.72rem', color: '#64748b' }}>Pop: {v.population.toLocaleString()} • {v.tank}</div>
                  </td>
                  <td>
                    <span
                      style={{
                        padding: '0.25rem 0.6rem',
                        borderRadius: '9999px',
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        background: `${priorityColor}18`,
                        color: priorityColor,
                        border: `1px solid ${priorityColor}40`,
                      }}
                    >
                      {v.priority}
                    </span>
                  </td>
                  <td style={{ fontWeight: 600 }}>{v.demandKL} kL</td>
                  <td style={{ fontWeight: 700, color: '#0284c7' }}>{v.allocatedKL} kL</td>
                  <td style={{ fontWeight: 700, color: v.shortageKL > 50 ? '#ef4444' : v.shortageKL > 0 ? '#f59e0b' : '#10b981' }}>
                    {v.shortageKL} kL
                  </td>
                  <td style={{ minWidth: '180px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <span style={{ fontWeight: 700, color: satisfactionColor, minWidth: '45px', fontSize: '0.85rem' }}>
                        {v.satisfaction}%
                      </span>
                      <div style={{ flex: 1, height: '8px', background: '#e2e8f0', borderRadius: '9999px', overflow: 'hidden' }}>
                        <div style={{ width: `${v.satisfaction}%`, height: '100%', background: satisfactionColor, borderRadius: '9999px' }} />
                      </div>
                    </div>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <button
                      onClick={() => handleOpenAdjustModal(v)}
                      style={{
                        padding: '0.4rem 0.85rem',
                        borderRadius: '8px',
                        border: '1px solid #cbd5e1',
                        background: '#ffffff',
                        color: '#0284c7',
                        fontSize: '0.78rem',
                        fontWeight: 700,
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = '#0284c7';
                        e.currentTarget.style.color = '#ffffff';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = '#ffffff';
                        e.currentTarget.style.color = '#0284c7';
                      }}
                    >
                      Adjust Quota
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Adjust Quota Modal with Interactive Slider */}
      {editingVillage && (
        <div className="modal-backdrop" onClick={() => setEditingVillage(null)}>
          <div
            className="glass-panel"
            style={{ width: '100%', maxWidth: '520px', padding: '2rem', position: 'relative' }}
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setEditingVillage(null)}
              style={{ position: 'absolute', top: '1.25rem', right: '1.25rem', background: '#f1f5f9', border: 'none', borderRadius: '50%', width: '32px', height: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}
            >
              <X size={16} />
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem' }}>
              <div style={{ width: '40px', height: '40px', borderRadius: '12px', background: 'rgba(139, 92, 246, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#8b5cf6' }}>
                <SlidersHorizontal size={22} />
              </div>
              <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0f172a' }}>
                  Adjust Water Quota: {editingVillage.name}
                </h3>
                <div style={{ fontSize: '0.78rem', color: '#64748b' }}>
                  {editingVillage.priority} • Base Demand: {editingVillage.demandKL} kL
                </div>
              </div>
            </div>

            {/* Live Slider Section */}
            <div style={{ background: '#f8fafc', padding: '1.5rem', borderRadius: '16px', border: '1px solid #e2e8f0', margin: '1rem 0' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#334155' }}>Dispatched Allocation (kL):</span>
                <span style={{ fontSize: '1.5rem', fontWeight: 800, color: '#0284c7' }}>{sliderAllocated} kL</span>
              </div>

              <input
                type="range"
                min="0"
                max={editingVillage.demandKL * 1.2}
                step="5"
                value={sliderAllocated}
                onChange={(e) => setSliderAllocated(Number(e.target.value))}
                style={{ width: '100%', accentColor: '#0284c7', height: '8px', cursor: 'pointer' }}
              />

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.4rem' }}>
                <span>0 kL (0%)</span>
                <span>Full Demand: {editingVillage.demandKL} kL (100%)</span>
                <span>Surplus: {Math.round(editingVillage.demandKL * 1.2)} kL</span>
              </div>
            </div>

            {/* Impact Calculation Preview */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '1.5rem' }}>
              <div style={{ background: '#f1f5f9', padding: '0.85rem', borderRadius: '12px' }}>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Resulting Shortage</div>
                <div style={{ fontSize: '1.15rem', fontWeight: 800, color: editingVillage.demandKL - sliderAllocated > 0 ? '#dc2626' : '#059669' }}>
                  {Math.max(0, editingVillage.demandKL - sliderAllocated)} kL
                </div>
              </div>
              <div style={{ background: '#f1f5f9', padding: '0.85rem', borderRadius: '12px' }}>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Resulting Satisfaction</div>
                <div style={{ fontSize: '1.15rem', fontWeight: 800, color: sliderAllocated >= editingVillage.demandKL * 0.9 ? '#059669' : '#d97706' }}>
                  {Math.min(100, Math.round((sliderAllocated / editingVillage.demandKL) * 1000) / 10)}%
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button
                onClick={handleSaveQuota}
                style={{ flex: 1, padding: '0.75rem', background: 'linear-gradient(135deg, #0284c7, #06b6d4)', color: '#ffffff', border: 'none', borderRadius: '12px', fontSize: '0.88rem', fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}
              >
                <Save size={16} /> Save & Re-balance LP
              </button>
              <button
                onClick={() => setEditingVillage(null)}
                style={{ padding: '0.75rem 1.25rem', background: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1', borderRadius: '12px', fontSize: '0.88rem', fontWeight: 600, cursor: 'pointer' }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
