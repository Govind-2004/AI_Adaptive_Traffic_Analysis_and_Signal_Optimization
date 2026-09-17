import React from 'react';
import { TrafficProvider, useTraffic } from './context/TrafficContext';
import { Navbar } from './components/layout/Navbar';
import { Sidebar } from './components/layout/Sidebar';

import { DashboardPage } from './pages/DashboardPage';
import { LiveFeedsPage } from './pages/LiveFeedsPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { SignalControlPage } from './pages/SignalControlPage';
import { IncidentsPage } from './pages/IncidentsPage';
import { IntegrationSettingsPage } from './pages/IntegrationSettingsPage';
import { EmergencyOverrideModal } from './components/signals/EmergencyOverrideModal';

const MainContent = () => {
  const { activeTab } = useTraffic();

  const renderView = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardPage />;
      case 'feeds':
        return <LiveFeedsPage />;
      case 'analytics':
        return <AnalyticsPage />;
      case 'signals':
        return <SignalControlPage />;
      case 'incidents':
        return <IncidentsPage />;
      case 'settings':
        return <IntegrationSettingsPage />;
      default:
        return <DashboardPage />;
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F7FA] text-slate-900 flex flex-col font-sans selection:bg-sky-100 selection:text-sky-900">
      <Navbar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 p-4 md:p-6 overflow-y-auto max-w-7xl mx-auto w-full">
          {renderView()}
        </main>
      </div>
      <EmergencyOverrideModal />
    </div>
  );
};

export default function App() {
  return (
    <TrafficProvider>
      <MainContent />
    </TrafficProvider>
  );
}
