import React, { useState } from 'react';
import { Maximize2, Eye, EyeOff, Radio, Video, ShieldCheck } from 'lucide-react';
import { useTraffic } from '../../context/TrafficContext';
import { AIBoundingBoxOverlay } from './AIBoundingBoxOverlay';

export const CameraFeedGrid = () => {
  const { feeds, selectedFeedId, setSelectedFeedId, showDetections, setShowDetections } = useTraffic();
  const [fullscreenFeed, setFullscreenFeed] = useState(null);

  const activeFeed = feeds.find((f) => f.id === selectedFeedId) || feeds[0];

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs space-y-4">
      {/* Feed Controller Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-sky-50 text-sky-600 border border-sky-100">
            <Video className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-bold text-slate-900 text-sm flex items-center space-x-2">
              <span>{activeFeed.name}</span>
              <span className="px-2 py-0.5 text-[10px] font-mono font-bold rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                LIVE HD
              </span>
            </h2>
            <p className="text-xs text-slate-500 font-mono">{activeFeed.location}</p>
          </div>
        </div>

        <div className="flex items-center space-x-3 text-xs font-mono">
          {/* AI Overlay Toggle */}
          <button
            onClick={() => setShowDetections(!showDetections)}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg border transition-all ${
              showDetections
                ? 'bg-sky-50 text-sky-700 border-sky-200 font-semibold shadow-2xs'
                : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
            }`}
          >
            {showDetections ? <Eye className="w-3.5 h-3.5 text-sky-600" /> : <EyeOff className="w-3.5 h-3.5 text-slate-400" />}
            <span>AI Bounding Boxes: {showDetections ? 'ON' : 'OFF'}</span>
          </button>

          {/* Fullscreen Button */}
          <button
            onClick={() => setFullscreenFeed(activeFeed)}
            className="p-2 rounded-lg bg-slate-50 text-slate-600 hover:text-slate-900 border border-slate-200 hover:border-slate-300 transition-colors shadow-2xs"
            title="Expand View"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Video View Box */}
      <div className="relative aspect-video rounded-xl overflow-hidden bg-slate-950 border border-slate-800 shadow-xs group">
        <img
          src={activeFeed.streamUrl}
          alt={activeFeed.name}
          className="w-full h-full object-cover opacity-95 transition-transform duration-500 group-hover:scale-102"
        />

        {/* AI Object Bounding Overlay */}
        {showDetections && <AIBoundingBoxOverlay camId={activeFeed.id} />}

        {/* Top Video Telemetry HUD */}
        <div className="absolute top-3 left-3 right-3 flex justify-between items-start pointer-events-none">
          <div className="flex items-center space-x-2 bg-slate-900/80 backdrop-blur-sm px-3 py-1.5 rounded-lg border border-slate-700/60 text-[11px] font-mono">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
            <span className="text-white font-bold">REC</span>
            <span className="text-slate-400">|</span>
            <span className="text-sky-400">{activeFeed.fps} FPS</span>
            <span className="text-slate-400">|</span>
            <span className="text-slate-200">{activeFeed.resolution}</span>
          </div>

          <div className="bg-slate-900/80 backdrop-blur-sm px-3 py-1.5 rounded-lg border border-slate-700/60 text-[11px] font-mono text-slate-200">
            Density: <span className="font-bold text-amber-400">{activeFeed.density}</span>
          </div>
        </div>

        {/* Bottom Stream Info Bar */}
        <div className="absolute bottom-3 left-3 right-3 bg-slate-900/85 backdrop-blur-sm px-4 py-2.5 rounded-lg border border-slate-700/60 flex justify-between items-center text-xs font-mono">
          <div className="flex items-center space-x-5">
            <div>
              <span className="text-slate-400 block text-[10px]">VEHICLE COUNT</span>
              <span className="text-white font-bold">{activeFeed.vehicleCount} / min</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px]">AVG SPEED</span>
              <span className="text-sky-400 font-bold">{activeFeed.avgSpeed} km/h</span>
            </div>
          </div>
          <div className="flex items-center space-x-2 text-[10px] text-emerald-400 font-semibold">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>YOLOv8 Inference Status: OK</span>
          </div>
        </div>
      </div>

      {/* Mini Feed Selector Thumbnails */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
        {feeds.map((feed) => {
          const isSelected = feed.id === selectedFeedId;
          return (
            <button
              key={feed.id}
              onClick={() => setSelectedFeedId(feed.id)}
              className={`relative rounded-xl overflow-hidden border transition-all text-left group ${
                isSelected
                  ? 'border-sky-600 ring-2 ring-sky-500/30 shadow-md scale-102'
                  : 'border-slate-200 opacity-80 hover:opacity-100 hover:border-slate-400'
              }`}
            >
              <div className="aspect-video relative bg-slate-900">
                <img src={feed.streamUrl} alt={feed.name} className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105" />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent"></div>
                <span className="absolute bottom-1.5 left-2 text-[11px] font-mono text-white font-bold truncate max-w-[90%] drop-shadow-xs">
                  {feed.id.toUpperCase()}
                </span>
                {isSelected && (
                  <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 rounded-full bg-sky-500 border border-white"></span>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
