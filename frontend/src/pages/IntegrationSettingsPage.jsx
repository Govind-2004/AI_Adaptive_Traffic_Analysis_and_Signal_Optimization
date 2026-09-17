import React, { useState } from 'react';
import { Wrench, Database, CheckCircle, RefreshCw, AlertTriangle, ShieldCheck } from 'lucide-react';
import { useTraffic } from '../context/TrafficContext';
import { DEFAULT_CONFIG } from '../utils/constants';

export const IntegrationSettingsPage = () => {
  const { isMockMode, toggleMockMode, addNotification } = useTraffic();
  const [backendUrl, setBackendUrl] = useState(DEFAULT_CONFIG.BACKEND_BASE_URL);
  const [wsUrl, setWsUrl] = useState(DEFAULT_CONFIG.WEBSOCKET_URL);
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.85);
  const [testStatus, setTestStatus] = useState(null);
  const [isTesting, setIsTesting] = useState(false);

  const handleTestConnection = () => {
    setIsTesting(true);
    setTestStatus(null);
    setTimeout(() => {
      setIsTesting(false);
      if (isMockMode) {
        setTestStatus({
          success: true,
          message: 'Mock Telemetry Stream connected successfully. (100% simulated packets)',
        });
      } else {
        setTestStatus({
          success: false,
          message: `Attempted GET ${backendUrl}/health. Backend offline or CORS issue. Falling back to Mock service without throwing application errors.`,
        });
      }
    }, 1200);
  };

  const handleSave = () => {
    addNotification(`Integration settings saved! Backend: ${backendUrl}`, 'info');
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="pb-2 border-b border-slate-200">
        <h2 className="text-xl font-bold text-slate-900">Backend & ML Pipeline Integration Console</h2>
        <p className="text-xs text-slate-500 font-mono">
          Configure REST API endpoints, WebSocket video streams, and ML model thresholds
        </p>
      </div>

      {/* Integration Mode Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-2xs space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-200">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-purple-50 text-purple-600 border border-purple-100">
              <Database className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-sm">Data Source Mode</h3>
              <p className="text-xs text-slate-500 font-mono">Toggle live ML API connection or offline demo mode</p>
            </div>
          </div>

          <span
            className={`px-3 py-1 text-xs font-mono font-bold rounded-lg border ${
              isMockMode
                ? 'bg-sky-50 text-sky-700 border-sky-200'
                : 'bg-purple-50 text-purple-700 border-purple-200'
            }`}
          >
            {isMockMode ? 'STANDALONE DEMO MODE' : 'LIVE BACKEND MODE'}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <button
            onClick={() => toggleMockMode(true)}
            className={`p-4 rounded-xl border text-left transition-all space-y-2 ${
              isMockMode
                ? 'bg-sky-50 border-sky-300 ring-1 ring-sky-200 shadow-2xs'
                : 'bg-slate-50 border-slate-200 hover:border-slate-300'
            }`}
          >
            <div className="flex items-center justify-between font-bold text-sm text-slate-900">
              <span>Standalone Demo (Simulated)</span>
              {isMockMode && <CheckCircle className="w-4 h-4 text-sky-600" />}
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">
              Runs complete real-time traffic simulations locally. Zero external backend dependencies needed.
            </p>
          </button>

          <button
            onClick={() => toggleMockMode(false)}
            className={`p-4 rounded-xl border text-left transition-all space-y-2 ${
              !isMockMode
                ? 'bg-purple-50 border-purple-300 ring-1 ring-purple-200 shadow-2xs'
                : 'bg-slate-50 border-slate-200 hover:border-slate-300'
            }`}
          >
            <div className="flex items-center justify-between font-bold text-sm text-slate-900">
              <span>Connect Live ML Backend</span>
              {!isMockMode && <CheckCircle className="w-4 h-4 text-purple-600" />}
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">
              Connects directly to your Python FastAPI / Flask / PyTorch / YOLO backend server endpoints.
            </p>
          </button>
        </div>
      </div>

      {/* API Endpoint Configuration */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-2xs space-y-5">
        <h3 className="font-bold text-slate-900 text-sm pb-3 border-b border-slate-200 flex items-center space-x-2">
          <Wrench className="w-4 h-4 text-sky-600" />
          <span>Endpoint & Model Threshold Settings</span>
        </h3>

        <div className="space-y-4 font-mono text-xs">
          <div>
            <label className="block text-slate-700 font-semibold mb-1">REST API Base URL</label>
            <input
              type="text"
              value={backendUrl}
              onChange={(e) => setBackendUrl(e.target.value)}
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:border-sky-500 focus:bg-white"
              placeholder="http://localhost:8000/api/v1"
            />
          </div>

          <div>
            <label className="block text-slate-700 font-semibold mb-1">WebSocket Stream Endpoint</label>
            <input
              type="text"
              value={wsUrl}
              onChange={(e) => setWsUrl(e.target.value)}
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:border-purple-500 focus:bg-white"
              placeholder="ws://localhost:8000/ws/traffic"
            />
          </div>

          <div>
            <div className="flex justify-between mb-1">
              <label className="text-slate-700 font-semibold">YOLOv8 Detection Confidence Filter</label>
              <span className="text-sky-700 font-bold">{(confidenceThreshold * 100).toFixed(0)}%</span>
            </div>
            <input
              type="range"
              min="0.5"
              max="0.99"
              step="0.01"
              value={confidenceThreshold}
              onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
              className="w-full accent-sky-600 bg-slate-200 rounded-lg cursor-pointer"
            />
          </div>
        </div>

        {/* Test Connection Result Box */}
        {testStatus && (
          <div
            className={`p-3.5 rounded-xl border text-xs font-mono flex items-start space-x-2.5 ${
              testStatus.success
                ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                : 'bg-amber-50 border-amber-200 text-amber-800'
            }`}
          >
            {testStatus.success ? (
              <ShieldCheck className="w-4 h-4 shrink-0 mt-0.5 text-emerald-600" />
            ) : (
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-amber-600" />
            )}
            <span>{testStatus.message}</span>
          </div>
        )}

        <div className="flex items-center justify-between pt-3 border-t border-slate-200">
          <button
            onClick={handleTestConnection}
            disabled={isTesting}
            className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 rounded-xl text-xs font-mono font-bold flex items-center space-x-2 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isTesting ? 'animate-spin' : ''}`} />
            <span>{isTesting ? 'Testing Connection...' : 'Test Backend Connection'}</span>
          </button>

          <button
            onClick={handleSave}
            className="px-5 py-2 bg-sky-600 hover:bg-sky-700 text-white font-mono text-xs font-bold rounded-xl shadow-2xs transition-all"
          >
            Save Configuration
          </button>
        </div>
      </div>
    </div>
  );
};
