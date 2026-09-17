import React from 'react';
import { ShieldAlert, CheckCircle2, X } from 'lucide-react';
import { useTraffic } from '../../context/TrafficContext';

export const EmergencyOverrideModal = () => {
  const { 
    emergencyModalOpen, 
    setEmergencyModalOpen, 
    selectedIntersection, 
    handleEmergencyOverride 
  } = useTraffic();

  if (!emergencyModalOpen) return null;

  const handleConfirm = () => {
    handleEmergencyOverride(selectedIntersection);
    setEmergencyModalOpen(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-fade-in">
      <div className="bg-white border border-red-200 rounded-2xl max-w-md w-full p-6 shadow-xl space-y-5 relative">
        <button
          onClick={() => setEmergencyModalOpen(false)}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-600"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center space-x-3 text-red-600">
          <div className="p-3 rounded-xl bg-red-50 ring-1 ring-red-200">
            <ShieldAlert className="w-7 h-7 text-red-600" />
          </div>
          <div>
            <h3 className="font-extrabold text-lg text-slate-900">Emergency Priority Clearance</h3>
            <p className="text-xs text-red-600 font-mono">High-Priority Command Dispatch</p>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2 text-xs font-mono text-slate-700">
          <p className="text-slate-800">
            You are about to force a continuous <span className="text-emerald-700 font-bold">GREEN SIGNAL CLEARANCE</span> for:
          </p>
          <div className="p-2.5 rounded bg-white border border-red-200 text-sky-700 font-bold shadow-2xs">
            {selectedIntersection || 'Selected Intersection'}
          </div>
          <p className="text-slate-500 text-[11px]">
            This will suspend standard AI adaptive cycles and prioritize emergency responder corridor access (Ambulance / Fire Truck).
          </p>
        </div>

        <div className="flex items-center justify-end space-x-3 pt-2 border-t border-slate-100">
          <button
            onClick={() => setEmergencyModalOpen(false)}
            className="px-4 py-2 text-xs font-mono font-medium rounded-xl bg-slate-100 text-slate-700 hover:bg-slate-200"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            className="px-4 py-2 text-xs font-mono font-bold rounded-xl bg-red-600 hover:bg-red-700 text-white shadow-xs flex items-center space-x-1.5"
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>CONFIRM EMERGENCY OVERRIDE</span>
          </button>
        </div>
      </div>
    </div>
  );
};
