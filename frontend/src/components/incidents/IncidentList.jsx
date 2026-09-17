import React from 'react';
import { AlertCircle, Download, Clock, MapPin } from 'lucide-react';
import { useTraffic } from '../../context/TrafficContext';

export const IncidentList = () => {
  const { telemetry } = useTraffic();
  const incidents = telemetry.incidents || [];

  const exportReport = (format) => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(incidents, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `traffic_incidents_${Date.now()}.${format}`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const getSeverityBadge = (severity) => {
    switch (severity) {
      case 'CRITICAL':
        return 'bg-red-50 text-red-700 border-red-200';
      case 'HIGH':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      default:
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-red-50 text-red-600 border border-red-100">
            <AlertCircle className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-bold text-slate-900 text-sm">Real-Time AI Incident Logs</h2>
            <p className="text-xs text-slate-500 font-mono">Automated Anomaly Detection Stream</p>
          </div>
        </div>

        {/* Export Buttons */}
        <div className="flex items-center space-x-2 text-xs font-mono">
          <button
            onClick={() => exportReport('json')}
            className="px-3 py-1.5 rounded-lg bg-slate-50 text-slate-700 hover:text-slate-900 border border-slate-200 hover:border-slate-300 flex items-center space-x-1.5 transition-colors shadow-2xs"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            <span>Export JSON</span>
          </button>
        </div>
      </div>

      {/* List of Incidents */}
      <div className="space-y-3">
        {incidents.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-xs font-mono">No active incident reports</div>
        ) : (
          incidents.map((inc) => (
            <div
              key={inc.id}
              className="p-4 rounded-xl bg-slate-50 border border-slate-200 hover:border-slate-300 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="space-y-1.5 flex-1">
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded border ${getSeverityBadge(inc.severity)}`}>
                    {inc.severity}
                  </span>
                  <h4 className="font-bold text-sm text-slate-900">{inc.type.replace('_', ' ')}</h4>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">{inc.description}</p>
                <div className="flex items-center space-x-4 text-[11px] text-slate-500 font-mono pt-1">
                  <span className="flex items-center space-x-1">
                    <MapPin className="w-3.5 h-3.5 text-sky-600" />
                    <span>{inc.location}</span>
                  </span>
                  <span className="flex items-center space-x-1">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    <span>{new Date(inc.timestamp).toLocaleTimeString()}</span>
                  </span>
                </div>
              </div>

              <div className="flex items-center space-x-3 shrink-0">
                <span className="px-3 py-1 text-xs font-mono rounded-lg bg-white text-slate-700 border border-slate-200 shadow-2xs">
                  Status: <strong className="text-sky-700">{inc.status}</strong>
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
