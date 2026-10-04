import React, { useState } from 'react';
import LandingHub from './components/LandingHub';
import DashboardLayout from './components/DashboardLayout';
import OverviewPage from './components/pages/OverviewPage';
import DemandPredictionPage from './components/pages/DemandPredictionPage';
import GisMapPage from './components/pages/GisMapPage';
import AllocationPage from './components/pages/AllocationPage';
import NetworkPage from './components/pages/NetworkPage';
import WaterJusticePage from './components/pages/WaterJusticePage';

export default function App() {
  // Screen 0 ('hub') vs Interior Dashboards ('dashboard')
  const [currentScreen, setCurrentScreen] = useState('hub');
  // Pages: 'overview', 'prediction', 'gis', 'allocation', 'network', 'justice'
  const [activePage, setActivePage] = useState('overview');

  const handleSelectModule = (moduleId) => {
    setActivePage(moduleId);
    setCurrentScreen('dashboard');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleBackToHub = () => {
    setCurrentScreen('hub');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSelectTab = (tabId) => {
    setActivePage(tabId);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <>
      {/* Dynamic Living Video Backgrounds */}
      {currentScreen === 'hub' ? (
        <div className="video-bg-container">
          <video
            key="hub-video"
            autoPlay
            loop
            muted
            playsInline
            className="video-bg-media"
          >
            <source src="/background/Shobhit42_0_ssspin.io_1791118782.mp4" type="video/mp4" />
          </video>
          <div className="overlay-landing" />
        </div>
      ) : (
        <div className="video-bg-container">
          <video
            key="dashboard-video"
            autoPlay
            loop
            muted
            playsInline
            className="video-bg-media"
          >
            <source src="/background/animekpopcy_ssspin.io_1791119012.mp4" type="video/mp4" />
          </video>
          <div className="overlay-dashboard" />
        </div>
      )}

      {/* Screen Router */}
      {currentScreen === 'hub' ? (
        <LandingHub onSelectModule={handleSelectModule} />
      ) : (
        <DashboardLayout
          activeTab={activePage}
          onSelectTab={handleSelectTab}
          onBackToHub={handleBackToHub}
        >
          {activePage === 'overview' && (
            <OverviewPage onNavigateToPage={handleSelectTab} />
          )}
          {activePage === 'prediction' && (
            <DemandPredictionPage />
          )}
          {activePage === 'gis' && (
            <GisMapPage onNavigateToPage={handleSelectTab} />
          )}
          {activePage === 'allocation' && (
            <AllocationPage />
          )}
          {activePage === 'network' && (
            <NetworkPage />
          )}
          {activePage === 'justice' && (
            <WaterJusticePage />
          )}
        </DashboardLayout>
      )}
    </>
  );
}
