import React from 'react';
import { 
  LayoutDashboard, 
  Video, 
  BarChart3, 
  Sliders, 
  AlertTriangle, 
  Wrench,
  Radio
} from 'lucide-react';
import { useTraffic } from '../../context/TrafficContext';

export const Sidebar = () => {
  const { activeTab, setActiveTab, telemetry } = useTraffic();

  const navItems = [
    { id: 'dashboard', label: 'Command Center', icon: LayoutDashboard, badge: null },
    { id: 'feeds', label: 'Live Video Streams', icon: Video, badge: '4 FEEDS' },
    { id: 'analytics', label: 'Traffic Analytics', icon: BarChart3, badge: null },
    { id: 'signals', label: 'Signal Controller', icon: Sliders, badge: 'AI ADAPTIVE' },
    { id: 'incidents', label: 'Incident Console', icon: AlertTriangle, badge: telemetry.incidents?.length || 3, badgeColor: 'bg-red-100 text-red-700 border-red-200' },
    { id: 'settings', label: 'API & ML Pipeline', icon: Wrench, badge: 'READY' },
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col justify-between hidden md:flex shrink-0 min-h-[calc(100vh-4rem)]">
      <div className="p-4 space-y-6">
        {/* Navigation Group */}
        <div>
          <div className="px-3 mb-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider font-mono">
            Navigation Menu
          </div>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-[#E0F2FE] text-[#0284C7] font-semibold border border-sky-200 shadow-2xs'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <Icon className={`w-4 h-4 ${isActive ? 'text-[#0284C7]' : 'text-slate-400'}`} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className={`px-2 py-0.5 text-[10px] font-bold font-mono rounded ${
                      item.badgeColor || 'bg-slate-100 text-slate-600 border border-slate-200'
                    }`}>
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Real-time System Status Card */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wider text-[10px]">System Telemetry</span>
            <Radio className="w-3.5 h-3.5 text-emerald-600" />
          </div>
          <div className="space-y-2 font-mono text-xs text-slate-600">
            <div className="flex justify-between">
              <span>Model:</span>
              <span className="text-sky-700 font-semibold">YOLOv8-Traffic</span>
            </div>
            <div className="flex justify-between">
              <span>FPS Stream:</span>
              <span className="text-emerald-700 font-semibold">60 FPS</span>
            </div>
            <div className="flex justify-between">
              <span>Latency:</span>
              <span className="text-slate-800 font-semibold">14 ms</span>
            </div>
          </div>
        </div>
      </div>

      {/* Footer info */}
      <div className="p-4 border-t border-slate-200 text-center">
        <p className="text-[11px] text-slate-400">
          Smart City Infrastructure © 2026
        </p>
      </div>
    </aside>
  );
};
