import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Navigation, Video } from 'lucide-react';
import { useTraffic } from '../../context/TrafficContext';

// Fix leaflet default icon issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

export const TrafficMap = () => {
  const { feeds, setSelectedFeedId, setActiveTab } = useTraffic();
  const center = [40.7350, -73.9900]; // NYC Metro default center

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-200">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-emerald-50 text-emerald-600 border border-emerald-100">
            <Navigation className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-bold text-slate-900 text-sm">GIS Traffic Congestion Heatmap</h2>
            <p className="text-xs text-slate-500 font-mono">Live Camera Nodes & Junction Density</p>
          </div>
        </div>
        <div className="flex items-center space-x-3 text-xs font-mono">
          <span className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
            <span className="text-slate-600 font-medium">Normal</span>
          </span>
          <span className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
            <span className="text-slate-600 font-medium">Moderate</span>
          </span>
          <span className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-red-600"></span>
            <span className="text-slate-600 font-medium">Critical</span>
          </span>
        </div>
      </div>

      {/* Map Container */}
      <div className="h-[380px] rounded-xl overflow-hidden border border-slate-200 relative shadow-2xs">
        <MapContainer center={center} zoom={13} scrollWheelZoom={false} className="w-full h-full">
          <TileLayer
            attribution='&copy; <a href="https://carto.com/">CARTO</a> Positron'
            url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          />

          {feeds.map((feed) => {
            const isCritical = feed.density === 'CRITICAL' || feed.density === 'HIGH';
            const radiusColor = isCritical ? '#DC2626' : feed.density === 'MODERATE' ? '#D97706' : '#16A34A';

            return (
              <React.Fragment key={feed.id}>
                {/* Heat Circle */}
                <Circle
                  center={feed.coordinates}
                  radius={isCritical ? 450 : 250}
                  pathOptions={{
                    color: radiusColor,
                    fillColor: radiusColor,
                    fillOpacity: 0.25,
                    weight: 2,
                  }}
                />

                {/* Marker */}
                <Marker position={feed.coordinates}>
                  <Popup className="custom-leaflet-popup">
                    <div className="p-1 font-sans text-xs bg-white text-slate-900 rounded">
                      <h4 className="font-bold text-sky-700 mb-1">{feed.name}</h4>
                      <p className="text-[11px] text-slate-600">{feed.location}</p>
                      <div className="mt-2 pt-2 border-t border-slate-100 flex justify-between items-center font-mono text-[10px]">
                        <span className="text-slate-700 font-semibold">Speed: {feed.avgSpeed} km/h</span>
                        <button
                          onClick={() => {
                            setSelectedFeedId(feed.id);
                            setActiveTab('feeds');
                          }}
                          className="px-2 py-1 bg-sky-600 hover:bg-sky-700 text-white font-bold rounded flex items-center space-x-1"
                        >
                          <Video className="w-3 h-3" />
                          <span>View Feed</span>
                        </button>
                      </div>
                    </div>
                  </Popup>
                </Marker>
              </React.Fragment>
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
};
