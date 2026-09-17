import React from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';

const vehicleData = [
  { name: 'Passenger Cars', value: 58, color: '#0284C7' },
  { name: 'Buses & Shuttles', value: 16, color: '#7C3AED' },
  { name: 'Commercial Trucks', value: 14, color: '#D97706' },
  { name: 'Motorcycles & Bikes', value: 8, color: '#16A34A' },
  { name: 'Pedestrians', value: 4, color: '#06B6D4' },
];

export const VehicleDistributionChart = () => {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs space-y-4">
      <div className="pb-3 border-b border-slate-200">
        <h3 className="font-bold text-slate-900 text-sm">Vehicle Classification Breakdown</h3>
        <p className="text-xs text-slate-500 font-mono">Real-time YOLOv8 Inference Distribution</p>
      </div>

      <div className="h-[240px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={vehicleData}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={85}
              paddingAngle={4}
              dataKey="value"
            >
              {vehicleData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} stroke="#FFFFFF" strokeWidth={2} />
              ))}
            </Pie>
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
            <Legend
              verticalAlign="bottom"
              height={36}
              iconType="circle"
              formatter={(value) => <span className="text-xs font-mono text-slate-700">{value}</span>}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
