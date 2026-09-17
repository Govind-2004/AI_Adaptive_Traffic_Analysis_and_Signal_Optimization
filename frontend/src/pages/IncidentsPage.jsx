import React from 'react';
import { IncidentList } from '../components/incidents/IncidentList';

export const IncidentsPage = () => {
  return (
    <div className="space-y-6">
      <div className="pb-2 border-b border-slate-200">
        <h2 className="text-xl font-bold text-slate-900">Incident & Anomaly Monitoring Console</h2>
        <p className="text-xs text-slate-500 font-mono">Automated Accident, Congestion & Obstruction Detection</p>
      </div>

      <IncidentList />
    </div>
  );
};
