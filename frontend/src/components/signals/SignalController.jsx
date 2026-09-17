import React from 'react';
import { Sliders, ShieldAlert, Zap, Clock } from 'lucide-react';
import { useTraffic } from '../../context/TrafficContext';

export const SignalController = () => {
  const { 
    telemetry, 
    handleUpdateSignal, 
    setEmergencyModalOpen, 
    setSelectedIntersection 
  } = useTraffic();

  const signals = telemetry.signals || [];

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-200">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-sky-50 text-sky-600 border border-sky-100">
            <Sliders className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-bold text-slate-900 text-sm">Adaptive Traffic Signal Controller</h2>
            <p className="text-xs text-slate-500 font-mono">Reinforcement Learning Traffic Timing</p>
          </div>
        </div>

        <div className="flex items-center space-x-2 text-xs font-mono">
          <span className="px-2.5 py-1 rounded-lg bg-sky-50 text-sky-700 border border-sky-200 font-semibold flex items-center space-x-1.5">
            <Zap className="w-3.5 h-3.5 text-sky-600" />
            <span>AI Dynamic Phase Active</span>
          </span>
        </div>
      </div>

      {/* Grid of Intersection Controllers */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {signals.map((sig) => {
          const isGreen = sig.status === 'GREEN';
          const isYellow = sig.status === 'YELLOW';
          const isRed = sig.status === 'RED';

          return (
            <div
              key={sig.id}
              className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3 relative"
            >
              {/* Header */}
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="font-bold text-sm text-slate-900">{sig.name}</h4>
                  <span className="text-[11px] text-slate-500 font-mono">Queue Length: {sig.queueLength} vehicles</span>
                </div>

                <div className="flex items-center space-x-1 px-2.5 py-1 rounded bg-white border border-slate-200 font-mono text-xs shadow-2xs">
                  <Clock className="w-3.5 h-3.5 text-sky-600" />
                  <span className="text-slate-900 font-bold">{sig.countdown}s</span>
                </div>
              </div>

              {/* Traffic Light Visual Indicator */}
              <div className="flex items-center justify-between p-3 rounded-lg bg-white border border-slate-200 shadow-2xs">
                <div className="flex items-center space-x-3">
                  {/* Traffic Light Housing */}
                  <div className="flex space-x-2 p-1.5 rounded-full bg-slate-900 border border-slate-700">
                    <div
                      className={`w-4 h-4 rounded-full transition-all ${
                        isRed ? 'bg-red-600 ring-2 ring-red-300' : 'bg-red-950/40'
                      }`}
                    ></div>
                    <div
                      className={`w-4 h-4 rounded-full transition-all ${
                        isYellow ? 'bg-amber-500 ring-2 ring-amber-300' : 'bg-amber-950/40'
                      }`}
                    ></div>
                    <div
                      className={`w-4 h-4 rounded-full transition-all ${
                        isGreen ? 'bg-emerald-500 ring-2 ring-emerald-300' : 'bg-emerald-950/40'
                      }`}
                    ></div>
                  </div>
                  <span className="text-xs font-mono font-bold tracking-wider text-slate-800">
                    {sig.status}
                  </span>
                </div>

                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                  {sig.mode}
                </span>
              </div>

              {/* Manual Override Controls */}
              <div className="flex items-center justify-between gap-2 pt-2 border-t border-slate-200">
                <div className="flex items-center space-x-1.5">
                  <button
                    onClick={() => handleUpdateSignal(sig.id, 'GREEN', 'MANUAL_OVERRIDE')}
                    className={`px-2.5 py-1 text-[11px] font-mono font-bold rounded border transition-colors ${
                      isGreen
                        ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                        : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-100'
                    }`}
                  >
                    GREEN
                  </button>
                  <button
                    onClick={() => handleUpdateSignal(sig.id, 'RED', 'MANUAL_OVERRIDE')}
                    className={`px-2.5 py-1 text-[11px] font-mono font-bold rounded border transition-colors ${
                      isRed
                        ? 'bg-red-100 text-red-800 border-red-300'
                        : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-100'
                    }`}
                  >
                    RED
                  </button>
                </div>

                {/* Emergency Dispatch Priority Button */}
                <button
                  onClick={() => {
                    setSelectedIntersection(sig.name);
                    setEmergencyModalOpen(true);
                  }}
                  className="px-3 py-1 bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 rounded-lg text-[11px] font-mono font-bold flex items-center space-x-1 transition-all"
                >
                  <ShieldAlert className="w-3.5 h-3.5 text-red-600" />
                  <span>EMERGENCY OVERRIDE</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
