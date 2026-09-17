import React from 'react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

const hourlyData = [
  { time: '06:00', volume: 140, predicted: 150 },
  { time: '08:00', volume: 420, predicted: 400 },
  { time: '10:00', volume: 380, predicted: 390 },
  { time: '12:00', volume: 310, predicted: 320 },
  { time: '14:00', volume: 350, predicted: 340 },
  { time: '16:00', volume: 540, predicted: 510 },
  { time: '18:00', volume: 620, predicted: 590 },
  { time: '20:00', volume: 390, predicted: 410 },
  { time: '22:00', volume: 210, predicted: 220 },
];

export const TrafficVolumeChart = () => {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-200">
        <div>
          <h3 className="font-bold text-slate-900 text-sm">Hourly Traffic Volume & AI Predictions</h3>
          <p className="text-xs text-slate-500 font-mono">Actual vs Neural Network Forecast</p>
        </div>
        <div className="flex items-center space-x-4 text-xs font-mono">
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-full bg-sky-600"></span>
            <span className="text-slate-700 font-medium">Actual Flow</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-full bg-purple-600"></span>
            <span className="text-slate-700 font-medium">AI Forecast</span>
          </div>
        </div>
      </div>

      <div className="h-[260px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={hourlyData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorVolume" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0284C7" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#0284C7" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorPredicted" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#7C3AED" stopOpacity={0.15} />
                <stop offset="95%" stopColor="#7C3AED" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
            <XAxis dataKey="time" stroke="#64748B" fontSize={11} fontFamily="JetBrains Mono" />
            <YAxis stroke="#64748B" fontSize={11} fontFamily="JetBrains Mono" />
            <Tooltip
              contentStyle={{
                backgroundColor: '#FFFFFF',
                borderColor: '#E2E8F0',
                borderRadius: '0.75rem',
                color: '#0F172A',
                fontSize: '12px',
                fontFamily: 'JetBrains Mono',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
              }}
            />
            <Area type="monotone" dataKey="volume" stroke="#0284C7" strokeWidth={2.5} fillOpacity={1} fill="url(#colorVolume)" />
            <Area type="monotone" dataKey="predicted" stroke="#7C3AED" strokeWidth={2} strokeDasharray="4 4" fillOpacity={1} fill="url(#colorPredicted)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
