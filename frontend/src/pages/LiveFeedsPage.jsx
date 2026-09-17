import React from 'react';
import { CameraFeedGrid } from '../components/dashboard/CameraFeedGrid';

export const LiveFeedsPage = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between pb-2 border-b border-slate-200">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Live Multi-Camera Surveillance Grid</h2>
          <p className="text-xs text-slate-500 font-mono">Real-time YOLOv8 ML Video Stream Analysis</p>
        </div>
      </div>

      <CameraFeedGrid />
    </div>
  );
};
