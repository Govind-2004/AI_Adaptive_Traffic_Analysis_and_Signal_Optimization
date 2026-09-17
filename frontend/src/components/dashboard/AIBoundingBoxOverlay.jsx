import React, { useEffect, useState } from 'react';
import { trafficApi } from '../../services/api';

export const AIBoundingBoxOverlay = ({ camId }) => {
  const [detections, setDetections] = useState([]);

  useEffect(() => {
    const cleanup = trafficApi.connectDetectionStream(camId, (newDetections) => {
      setDetections(newDetections);
    });
    return () => cleanup();
  }, [camId]);

  const getColorStyle = (type, isViolating) => {
    if (isViolating) {
      return {
        borderColor: '#DC2626',
        labelBg: '#DC2626',
        labelColor: '#FFFFFF',
      };
    }
    switch (type) {
      case 'bus':
      case 'truck':
        return {
          borderColor: '#7C3AED',
          labelBg: '#7C3AED',
          labelColor: '#FFFFFF',
        };
      case 'motorcycle':
        return {
          borderColor: '#D97706',
          labelBg: '#D97706',
          labelColor: '#FFFFFF',
        };
      case 'pedestrian':
        return {
          borderColor: '#16A34A',
          labelBg: '#16A34A',
          labelColor: '#FFFFFF',
        };
      default:
        return {
          borderColor: '#0284C7',
          labelBg: '#0284C7',
          labelColor: '#FFFFFF',
        };
    }
  };

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden">
      {/* AI Bounding Boxes */}
      {detections.map((box) => {
        const style = getColorStyle(box.type, box.isViolating);
        return (
          <div
            key={box.id}
            style={{
              top: box.rect.top,
              left: box.rect.left,
              width: box.rect.width,
              height: box.rect.height,
              borderColor: style.borderColor,
            }}
            className="absolute border-1.5 rounded-sm transition-all duration-500 ease-linear"
          >
            {/* Professional Label Badge */}
            <div
              style={{
                backgroundColor: style.labelBg,
                color: style.labelColor,
              }}
              className="absolute -top-5 left-0 px-1.5 py-0.5 rounded-xs text-[10px] font-mono font-bold uppercase tracking-wider flex items-center space-x-1 shadow-xs whitespace-nowrap"
            >
              <span>{box.type.toUpperCase()}</span>
              <span>{box.confidence}%</span>
              {box.isViolating && <span className="ml-1 text-[9px] bg-red-800 px-1 rounded">SPEED</span>}
            </div>
          </div>
        );
      })}
    </div>
  );
};
