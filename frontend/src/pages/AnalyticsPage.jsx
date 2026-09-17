import React from 'react';
import { TrafficVolumeChart } from '../components/analytics/TrafficVolumeChart';
import { VehicleDistributionChart } from '../components/analytics/VehicleDistributionChart';
import { SpeedAnalysisChart } from '../components/analytics/SpeedAnalysisChart';

export const AnalyticsPage = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between pb-2 border-b border-slate-200">
        <div>
          <h2 className="text-xl font-bold text-slate-900">AI Traffic Analytics & Deep Insights</h2>
          <p className="text-xs text-slate-500 font-mono">Historical Telemetry & Predictive Machine Learning Models</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TrafficVolumeChart />
        <VehicleDistributionChart />
      </div>

      <SpeedAnalysisChart />
    </div>
  );
};
