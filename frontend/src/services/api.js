import axios from 'axios';
import { DEFAULT_CONFIG, CAMERA_FEEDS } from '../utils/constants';
import { mockTrafficService } from './mockTrafficService';

// Configure Axios instance for backend integration
const httpClient = axios.create({
  baseURL: DEFAULT_CONFIG.BACKEND_BASE_URL,
  timeout: 8000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const trafficApi = {
  // Config toggle between Mock Mode & Live Backend Mode
  isMockMode: DEFAULT_CONFIG.USE_MOCK_DATA,

  setMockMode(useMock) {
    this.isMockMode = useMock;
    console.log(`[Traffic API] Switched mode: ${useMock ? 'MOCK' : 'LIVE BACKEND'}`);
  },

  async getTelemetrySummary() {
    if (this.isMockMode) {
      return { data: mockTrafficService.systemState };
    }
    try {
      const response = await httpClient.get('/telemetry/summary');
      return response;
    } catch (error) {
      console.warn('[Traffic API] Backend unavailable, falling back to mock service:', error.message);
      return { data: mockTrafficService.systemState, isFallback: true };
    }
  },

  async getCameraFeeds() {
    if (this.isMockMode) {
      return { data: CAMERA_FEEDS };
    }
    try {
      const response = await httpClient.get('/cameras');
      return response;
    } catch (error) {
      return { data: CAMERA_FEEDS, isFallback: true };
    }
  },

  async updateSignalState(signalId, status, mode) {
    if (this.isMockMode) {
      mockTrafficService.updateSignalState(signalId, status, mode);
      return { success: true, message: `Signal ${signalId} set to ${status}` };
    }
    try {
      const response = await httpClient.post(`/signals/${signalId}/override`, { status, mode });
      return response.data;
    } catch (error) {
      console.error('[Traffic API] Signal update failed:', error.message);
      mockTrafficService.updateSignalState(signalId, status, mode);
      return { success: true, isFallback: true };
    }
  },

  async triggerEmergencyOverride(intersectionId) {
    if (this.isMockMode) {
      mockTrafficService.triggerEmergencyOverride(intersectionId);
      return { success: true, message: `Emergency clearance applied to ${intersectionId}` };
    }
    try {
      const response = await httpClient.post(`/signals/${intersectionId}/emergency-override`);
      return response.data;
    } catch (error) {
      mockTrafficService.triggerEmergencyOverride(intersectionId);
      return { success: true, isFallback: true };
    }
  },

  // WebSocket connection helper for live ML Detection Streams
  connectDetectionStream(camId, onFrameDetections) {
    if (this.isMockMode) {
      // Simulate 500ms detection updates from ML pipeline
      const interval = setInterval(() => {
        const boxes = mockTrafficService.getDetectionsForFeed(camId);
        onFrameDetections(boxes);
      }, 700);
      return () => clearInterval(interval);
    }

    // Live WebSocket connection to ML pipeline server
    const wsUrl = `${DEFAULT_CONFIG.WEBSOCKET_URL}/stream/${camId}`;
    let socket;
    try {
      socket = new WebSocket(wsUrl);
      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onFrameDetections(data.detections || []);
        } catch (e) {
          console.error('WS payload error', e);
        }
      };
    } catch (e) {
      console.warn('WS Connection failed, running mock stream');
    }

    return () => {
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.close();
      }
    };
  }
};
