import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

const corridorData = [
  { name: '5th Ave & 42nd', speed: 18.4, limit: 35 },
  { name: 'I-95 Exit 8', speed: 42.1, limit: 55 },
  { name: 'Financial Plaza', speed: 31.8, limit: 35 },
  { name: 'Westside Hwy', speed: 12.6, limit: 45 },
];

export const SpeedAnalysisChart = () => {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs space-y-4">
      <div className="pb-3 border-b border-slate-200 flex justify-between items-center">
        <div>
          <h3 className="font-bold text-slate-900 text-sm">Corridor Speed vs Speed Limit</h3>
          <p className="text-xs text-slate-500 font-mono">Average Km/h per Monitored Zone</p>
        </div>
      </div>

      <div className="h-[240px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={corridorData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
            <XAxis dataKey="name" stroke="#64748B" fontSize={10} fontFamily="JetBrains Mono" />
            <YAxis stroke="#64748B" fontSize={10} fontFamily="JetBrains Mono" />
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
            <Bar dataKey="speed" fill="#0284C7" radius={[6, 6, 0, 0]} name="Avg Speed (km/h)" />
            <Bar dataKey="limit" fill="#CBD5E1" radius={[6, 6, 0, 0]} name="Speed Limit" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
