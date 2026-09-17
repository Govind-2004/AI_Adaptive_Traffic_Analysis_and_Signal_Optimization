import React, { useState } from 'react';
import { 
  Activity, 
  Bell, 
  Cpu, 
  Settings, 
  ShieldAlert, 
  CheckCircle,
  Database,
  Layers,
  Radio
} from 'lucide-react';
import { useTraffic } from '../../context/TrafficContext';

export const Navbar = () => {
  const { 
    telemetry, 
    isMockMode, 
    toggleMockMode, 
    notifications, 
    dismissNotification,
    setActiveTab
  } = useTraffic();

  const [showNotifications, setShowNotifications] = useState(false);

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between sticky top-0 z-40 shadow-xs">
      {/* Brand & System Status */}
      <div className="flex items-center space-x-5">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-sky-600 flex items-center justify-center shadow-xs">
            <Cpu className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="font-bold text-base tracking-tight text-slate-900">
                TRAFFIC<span className="text-sky-600">AI</span>
              </h1>
              <span className="px-2 py-0.5 text-[10px] font-semibold tracking-wider rounded bg-sky-50 text-sky-700 border border-sky-200 uppercase">
                v2.4 Pro
              </span>
            </div>
            <p className="text-[11px] text-slate-500 font-mono flex items-center space-x-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span>Neural Pipeline Operational</span>
            </p>
          </div>
        </div>

        {/* Global Congestion KPI Indicator */}
        <div className="hidden md:flex items-center px-3.5 py-1.5 rounded-lg bg-slate-50 border border-slate-200 space-x-2 text-xs">
          <Activity className="w-4 h-4 text-sky-600" />
          <span className="text-slate-600 font-medium">Congestion Index:</span>
          <span className={`font-bold font-mono ${telemetry.congestionIndex > 70 ? 'text-red-600' : 'text-emerald-600'}`}>
            {telemetry.congestionIndex}%
          </span>
        </div>
      </div>

      {/* Action Controls & Mode Switcher */}
      <div className="flex items-center space-x-3">
        {/* Backend Integration Mode Switcher */}
        <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs">
          <button
            onClick={() => toggleMockMode(true)}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg transition-all text-xs ${
              isMockMode 
                ? 'bg-sky-100 text-sky-700 font-semibold border border-sky-200 shadow-2xs' 
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Simulated Stream</span>
          </button>
          <button
            onClick={() => toggleMockMode(false)}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg transition-all text-xs ${
              !isMockMode 
                ? 'bg-purple-100 text-purple-700 font-semibold border border-purple-200 shadow-2xs' 
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            <span>Live ML Backend API</span>
          </button>
        </div>

        {/* Notification Bell */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="w-9 h-9 rounded-lg bg-white border border-slate-200 flex items-center justify-center text-slate-600 hover:text-slate-900 hover:border-slate-300 transition-colors relative shadow-2xs"
          >
            <Bell className="w-4 h-4" />
            {notifications.length > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-red-600 text-[10px] font-bold text-white flex items-center justify-center ring-2 ring-white">
                {notifications.length}
              </span>
            )}
          </button>

          {/* Notifications Dropdown */}
          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 bg-white border border-slate-200 rounded-xl shadow-lg z-50 overflow-hidden">
              <div className="p-3 border-b border-slate-100 flex items-center justify-between bg-slate-50">
                <span className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center space-x-1.5">
                  <ShieldAlert className="w-3.5 h-3.5 text-sky-600" />
                  <span>Realtime AI Alerts</span>
                </span>
                <span className="text-[10px] text-slate-500 font-mono">{notifications.length} Unread</span>
              </div>
              <div className="max-h-64 overflow-y-auto divide-y divide-slate-100">
                {notifications.length === 0 ? (
                  <div className="p-4 text-center text-xs text-slate-500">No active warnings</div>
                ) : (
                  notifications.map((n) => (
                    <div key={n.id} className="p-3 hover:bg-slate-50 flex items-start space-x-3 transition-colors text-xs">
                      {n.type === 'emergency' ? (
                        <Radio className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
                      ) : n.type === 'alert' ? (
                        <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                      ) : (
                        <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                      )}
                      <div className="flex-1">
                        <p className="text-slate-800 font-medium leading-snug">{n.text}</p>
                        <span className="text-[10px] text-slate-400 mt-1 block">{n.time}</span>
                      </div>
                      <button 
                        onClick={() => dismissNotification(n.id)}
                        className="text-slate-400 hover:text-slate-600 text-sm font-bold"
                      >
                        ×
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Integration Settings Quick Shortcut */}
        <button
          onClick={() => setActiveTab('settings')}
          className="w-9 h-9 rounded-lg bg-white border border-slate-200 flex items-center justify-center text-slate-600 hover:text-sky-600 hover:border-sky-300 transition-colors shadow-2xs"
          title="API Integration Settings"
        >
          <Settings className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
