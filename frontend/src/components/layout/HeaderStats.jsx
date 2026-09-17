import React from 'react';
import { Car, Zap, AlertCircle, Gauge } from 'lucide-react';
import { useTraffic } from '../../context/TrafficContext';

export const HeaderStats = () => {
  const { telemetry } = useTraffic();

  const cards = [
    {
      title: 'Total Active Vehicles',
      value: telemetry.totalVehicles,
      unit: 'Units',
      change: '+14% vs avg',
      isPositive: true,
      icon: Car,
      color: 'text-sky-600',
      bgColor: 'bg-sky-50',
      borderColor: 'border-slate-200',
    },
    {
      title: 'Average Flow Speed',
      value: `${telemetry.avgSpeedKmH}`,
      unit: 'km/h',
      change: '-2.4 km/h',
      isPositive: false,
      icon: Gauge,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
      borderColor: 'border-slate-200',
    },
    {
      title: 'AI Signal Efficiency',
      value: `${telemetry.adaptiveSignalEfficiency}%`,
      unit: 'Optimized',
      change: '+8.3%',
      isPositive: true,
      icon: Zap,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      borderColor: 'border-slate-200',
    },
    {
      title: 'Active Incidents',
      value: telemetry.incidents?.length || 0,
      unit: 'Events',
      change: '2 Dispatched',
      isPositive: false,
      icon: AlertCircle,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
      borderColor: 'border-slate-200',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className="p-5 rounded-xl bg-white border border-slate-200 shadow-2xs hover:border-slate-300 transition-all"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 font-medium">{card.title}</p>
                <div className="flex items-baseline space-x-2 mt-2">
                  <h3 className="text-2xl font-bold font-mono text-slate-900 tracking-tight">
                    {card.value}
                  </h3>
                  <span className="text-xs text-slate-500">{card.unit}</span>
                </div>
              </div>
              <div className={`p-3 rounded-xl ${card.bgColor} ${card.color}`}>
                <Icon className="w-6 h-6" />
              </div>
            </div>
            <div className="mt-3 flex items-center justify-between text-xs pt-3 border-t border-slate-100">
              <span className={`font-mono text-[11px] font-semibold ${card.isPositive ? 'text-emerald-600' : 'text-amber-600'}`}>
                {card.change}
              </span>
              <span className="text-slate-400 text-[10px]">Real-time Telemetry</span>
            </div>
          </div>
        );
      })}
    </div>
  );
};
