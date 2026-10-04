import React from 'react';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  TrendingUp,
  MapPin,
  SlidersHorizontal,
  Activity,
  Scale,
  Droplets,
  ArrowRight,
  ShieldCheck,
  Cpu
} from 'lucide-react';

const MODULES = [
  {
    id: 'overview',
    title: 'Executive Overview',
    subtitle: '6 Key KPIs, water availability, demand vs. shortage',
    icon: LayoutDashboard,
    badge: 'Real-Time Sync',
    accentColor: '#0284c7',
  },
  {
    id: 'prediction',
    title: 'Demand Prediction',
    subtitle: 'Village-level forecasting & time-series ML models',
    icon: TrendingUp,
    badge: 'AI Linear Reg',
    accentColor: '#06b6d4',
  },
  {
    id: 'gis',
    title: 'GIS Network Map',
    subtitle: 'Spatial sources, tanks, pipelines, and shortage heatmaps',
    icon: MapPin,
    badge: 'Interactive Topology',
    accentColor: '#10b981',
  },
  {
    id: 'allocation',
    title: 'Village Allocation',
    subtitle: 'Distribution ledgers, satisfaction %, and priority tiers',
    icon: SlidersHorizontal,
    badge: 'LP Solver HiGHS',
    accentColor: '#8b5cf6',
  },
  {
    id: 'network',
    title: 'Pipeline & Hydraulics',
    subtitle: 'Real-time flow rates, capacities, and leak telemetry',
    icon: Activity,
    badge: 'Telemetry Active',
    accentColor: '#f59e0b',
  },
  {
    id: 'justice',
    title: 'Water Justice & Equity',
    subtitle: "Jain's Fairness Index, weighted shortage, and disparity",
    icon: Scale,
    badge: 'Constitutional Equity',
    accentColor: '#ec4899',
  },
];

export default function LandingHub({ onSelectModule }) {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', padding: '2rem 1.5rem', position: 'relative', zIndex: 10 }}>
      {/* Center Stage Animated Header */}
      <motion.div
        initial={{ opacity: 0, y: -25, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        style={{ textAlign: 'center', maxWidth: '850px', marginBottom: '3rem' }}
      >
        {/* Brand Badge */}
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(255, 255, 255, 0.12)', backdropFilter: 'blur(10px)', border: '1px solid rgba(255, 255, 255, 0.25)', borderRadius: '9999px', padding: '0.4rem 1.25rem', color: '#e0f2fe', fontSize: '0.85rem', fontWeight: 600, marginBottom: '1.25rem' }}>
          <Droplets size={16} color="#38bdf8" />
          <span>Next-Gen Hydro-Informatics & Equity Engine</span>
          <span style={{ width: '4px', height: '4px', borderRadius: '50%', background: '#38bdf8' }} />
          <span style={{ color: '#38bdf8' }}>v2.4 Active</span>
        </div>

        {/* Main Title */}
        <h1 style={{ fontSize: 'clamp(2.75rem, 6vw, 4.25rem)', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.03em', lineHeight: 1.1, textShadow: '0 0 45px rgba(6, 182, 212, 0.45)' }}>
          Jai Dharma <span style={{ background: 'linear-gradient(135deg, #38bdf8, #06b6d4, #22d3ee)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>AI</span>
        </h1>

        {/* Tagline */}
        <p style={{ fontSize: 'clamp(1.1rem, 2vw, 1.35rem)', color: '#cbd5e1', marginTop: '1rem', fontWeight: 400, letterSpacing: '-0.01em', textShadow: '0 2px 10px rgba(0, 0, 0, 0.6)' }}>
          Intelligent Water Allocation, Network Flow & Equity Governance
        </p>

        {/* Sub-pills */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '1.5rem', marginTop: '1.25rem', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#94a3b8', fontSize: '0.82rem' }}>
            <ShieldCheck size={15} color="#10b981" /> 45 Protected Villages
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#94a3b8', fontSize: '0.82rem' }}>
            <Cpu size={15} color="#38bdf8" /> HiGHS Linear Programming
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#94a3b8', fontSize: '0.82rem' }}>
            <Scale size={15} color="#ec4899" /> Jain's Fairness Index 0.94
          </div>
        </div>
      </motion.div>

      {/* Interactive 3x2 Glass Grid */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '1.5rem',
          maxWidth: '1240px',
          width: '100%',
        }}
      >
        {MODULES.map((mod, index) => {
          const Icon = mod.icon;
          return (
            <motion.div
              key={mod.id}
              whileHover={{ y: -8, transition: { duration: 0.25 } }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onSelectModule(mod.id)}
              style={{
                background: 'rgba(255, 255, 255, 0.88)',
                backdropFilter: 'blur(20px)',
                WebkitBackdropFilter: 'blur(20px)',
                border: '1px solid rgba(255, 255, 255, 0.65)',
                borderRadius: '24px',
                padding: '1.75rem',
                cursor: 'pointer',
                boxShadow: '0 20px 40px -10px rgba(0, 0, 0, 0.4), 0 0 20px rgba(6, 182, 212, 0.1)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                position: 'relative',
                overflow: 'hidden',
                transition: 'border-color 0.25s, box-shadow 0.25s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'rgba(6, 182, 212, 0.8)';
                e.currentTarget.style.boxShadow = '0 25px 50px -10px rgba(2, 132, 199, 0.5), 0 0 35px rgba(6, 182, 212, 0.35)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.65)';
                e.currentTarget.style.boxShadow = '0 20px 40px -10px rgba(0, 0, 0, 0.4), 0 0 20px rgba(6, 182, 212, 0.1)';
              }}
            >
              {/* Subtle Ambient Radial Glow */}
              <div
                style={{
                  position: 'absolute',
                  top: '-30px',
                  right: '-30px',
                  width: '120px',
                  height: '120px',
                  borderRadius: '50%',
                  background: `radial-gradient(circle, ${mod.accentColor}33 0%, transparent 70%)`,
                  pointerEvents: 'none',
                }}
              />

              <div>
                {/* Header row: Icon & Badge */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
                  <div
                    style={{
                      width: '52px',
                      height: '52px',
                      borderRadius: '16px',
                      background: `linear-gradient(135deg, ${mod.accentColor}20, ${mod.accentColor}40)`,
                      border: `1px solid ${mod.accentColor}50`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: mod.accentColor,
                      boxShadow: `0 8px 16px ${mod.accentColor}25`,
                    }}
                  >
                    <Icon size={26} />
                  </div>

                  <span
                    style={{
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      padding: '0.3rem 0.75rem',
                      borderRadius: '9999px',
                      background: `${mod.accentColor}18`,
                      color: mod.accentColor,
                      border: `1px solid ${mod.accentColor}35`,
                      letterSpacing: '0.04em',
                      textTransform: 'uppercase',
                    }}
                  >
                    {mod.badge}
                  </span>
                </div>

                {/* Title & Description */}
                <h3 style={{ fontSize: '1.35rem', fontWeight: 800, color: '#0f172a', marginBottom: '0.45rem', letterSpacing: '-0.02em' }}>
                  {mod.title}
                </h3>
                <p style={{ fontSize: '0.9rem', color: '#475569', lineHeight: 1.5, fontWeight: 500 }}>
                  {mod.subtitle}
                </p>
              </div>

              {/* Action Link Footer */}
              <div style={{ marginTop: '1.75rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid rgba(226, 232, 240, 0.8)', paddingTop: '1rem' }}>
                <span style={{ fontSize: '0.82rem', fontWeight: 700, color: mod.accentColor }}>
                  Launch System
                </span>
                <div
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    background: '#f1f5f9',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#0f172a',
                    transition: 'all 0.2s ease',
                  }}
                >
                  <ArrowRight size={16} />
                </div>
              </div>
            </motion.div>
          );
        })}
      </motion.div>
    </div>
  );
}
