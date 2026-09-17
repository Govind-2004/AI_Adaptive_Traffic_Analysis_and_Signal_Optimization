import React, { createContext, useContext, useState, useEffect } from 'react';
import { mockTrafficService } from '../services/mockTrafficService';
import { trafficApi } from '../services/api';
import { CAMERA_FEEDS } from '../utils/constants';

const TrafficContext = createContext(null);

export const TrafficProvider = ({ children }) => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [telemetry, setTelemetry] = useState(mockTrafficService.systemState);
  const [feeds, setFeeds] = useState(CAMERA_FEEDS);
  const [selectedFeedId, setSelectedFeedId] = useState('cam-01');
  const [isMockMode, setIsMockMode] = useState(true);
  const [showDetections, setShowDetections] = useState(true);
  const [emergencyModalOpen, setEmergencyModalOpen] = useState(false);
  const [selectedIntersection, setSelectedIntersection] = useState(null);
  const [notifications, setNotifications] = useState([
    { id: 1, type: 'alert', text: 'Critical congestion on Junction 14 (5th Ave)', time: '2 mins ago' },
    { id: 2, type: 'info', text: 'AI Adaptive Mode auto-optimized Signal 03 timing', time: '10 mins ago' },
  ]);

  useEffect(() => {
    const unsubscribe = mockTrafficService.subscribe((newState) => {
      setTelemetry({ ...newState });
    });
    return () => unsubscribe();
  }, []);

  const toggleMockMode = (value) => {
    setIsMockMode(value);
    trafficApi.setMockMode(value);
  };

  const handleUpdateSignal = async (signalId, status, mode = 'AI_ADAPTIVE') => {
    await trafficApi.updateSignalState(signalId, status, mode);
  };

  const handleEmergencyOverride = async (intersectionId) => {
    await trafficApi.triggerEmergencyOverride(intersectionId);
    setNotifications((prev) => [
      {
        id: Date.now(),
        type: 'emergency',
        text: `EMERGENCY Priority Override activated for ${intersectionId}!`,
        time: 'Just now',
      },
      ...prev,
    ]);
  };

  const addNotification = (text, type = 'info') => {
    setNotifications((prev) => [{ id: Date.now(), text, type, time: 'Just now' }, ...prev]);
  };

  const dismissNotification = (id) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  return (
    <TrafficContext.Provider
      value={{
        activeTab,
        setActiveTab,
        telemetry,
        feeds,
        selectedFeedId,
        setSelectedFeedId,
        isMockMode,
        toggleMockMode,
        showDetections,
        setShowDetections,
        handleUpdateSignal,
        handleEmergencyOverride,
        emergencyModalOpen,
        setEmergencyModalOpen,
        selectedIntersection,
        setSelectedIntersection,
        notifications,
        addNotification,
        dismissNotification,
      }}
    >
      {children}
    </TrafficContext.Provider>
  );
};

export const useTraffic = () => {
  const context = useContext(TrafficContext);
  if (!context) throw new Error('useTraffic must be used within TrafficProvider');
  return context;
};
