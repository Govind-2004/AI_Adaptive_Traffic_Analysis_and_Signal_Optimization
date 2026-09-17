import React from 'react';
import { HeaderStats } from '../components/layout/HeaderStats';
import { CameraFeedGrid } from '../components/dashboard/CameraFeedGrid';
import { TrafficMap } from '../components/dashboard/TrafficMap';
import { TrafficVolumeChart } from '../components/analytics/TrafficVolumeChart';
import { SignalController } from '../components/signals/SignalController';
import { IncidentList } from '../components/incidents/IncidentList';

export const DashboardPage = () => {
  return (
    <div className="space-y-6">
      {/* Top Telemetry KPI Cards */}
      <HeaderStats />

      {/* Main Grid Layout: Camera Surveillance + GIS Traffic Heatmap */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <CameraFeedGrid />
        <TrafficMap />
      </div>

      {/* Secondary Row: Traffic Volume AI Forecast & Signal Controller */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TrafficVolumeChart />
        <SignalController />
      </div>

      {/* Incident Console Preview */}
      <IncidentList />
    </div>
  );
};
