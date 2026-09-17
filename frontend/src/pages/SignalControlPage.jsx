import React from 'react';
import { SignalController } from '../components/signals/SignalController';

export const SignalControlPage = () => {
  return (
    <div className="space-y-6">
      <div className="pb-2 border-b border-slate-200">
        <h2 className="text-xl font-bold text-slate-900">Intersection Signal Timing & Dispatch</h2>
        <p className="text-xs text-slate-500 font-mono">Reinforcement Learning Adaptive Phase & Emergency Clearances</p>
      </div>

      <SignalController />
    </div>
  );
};
