// Real-time dynamic mock generator for traffic telemetry & ML inference

const VEHICLE_TYPES = ['car', 'bus', 'truck', 'motorcycle', 'pedestrian'];

export class MockTrafficService {
  constructor() {
    this.listeners = new Set();
    this.timer = null;
    this.systemState = {
      totalVehicles: 376,
      avgSpeedKmH: 26.4,
      activeIncidents: 3,
      adaptiveSignalEfficiency: 94.2,
      congestionIndex: 68, // 0 - 100
      signals: [
        { id: 'sig-01', name: '5th Ave & 42nd St', status: 'GREEN', countdown: 18, mode: 'AI_ADAPTIVE', queueLength: 14 },
        { id: 'sig-02', name: 'I-95 Exit 8 Junction', status: 'RED', countdown: 8, mode: 'AI_ADAPTIVE', queueLength: 29 },
        { id: 'sig-03', name: 'Financial Plaza Crossing', status: 'GREEN', countdown: 34, mode: 'AI_ADAPTIVE', queueLength: 5 },
        { id: 'sig-04', name: 'Westside Hwy Ramp', status: 'YELLOW', countdown: 3, mode: 'MANUAL_OVERRIDE', queueLength: 19 },
      ],
      incidents: [
        {
          id: 'inc-101',
          type: 'ACCIDENT',
          location: 'Junction 14 - Northbound',
          timestamp: new Date(Date.now() - 12 * 60000).toISOString(),
          severity: 'CRITICAL',
          status: 'DISPATCHED',
          description: 'Two-vehicle minor collision occupying right lane. Patrol unit assigned.'
        },
        {
          id: 'inc-102',
          type: 'CONGESTION',
          location: 'Expressway Interchange 8B',
          timestamp: new Date(Date.now() - 25 * 60000).toISOString(),
          severity: 'HIGH',
          status: 'MONITORING',
          description: 'Spillback bottleneck due to construction work near exit 8.'
        },
        {
          id: 'inc-103',
          type: 'STALLED_VEHICLE',
          location: 'Harbor Bridge Approach West',
          timestamp: new Date(Date.now() - 4 * 60000).toISOString(),
          severity: 'MODERATE',
          status: 'NEW',
          description: 'Overheated commercial vehicle stranded on inner shoulder.'
        }
      ]
    };
  }

  // Generate dynamic AI bounding box detections over simulated video frames
  getDetectionsForFeed(camId) {
    const baseCount = camId === 'cam-01' ? 8 : camId === 'cam-04' ? 6 : 4;
    const boxes = [];

    for (let i = 0; i < baseCount; i++) {
      const type = VEHICLE_TYPES[Math.floor(Math.random() * (i === 0 ? 3 : 5))];
      const speed = Math.floor(15 + Math.random() * 45);
      const conf = (88 + Math.random() * 11.5).toFixed(1);
      
      // Random coordinates inside camera grid percentage
      const top = 15 + Math.floor(Math.random() * 65);
      const left = 10 + Math.floor(Math.random() * 75);
      const width = type === 'bus' || type === 'truck' ? 18 : 12;
      const height = type === 'bus' || type === 'truck' ? 16 : 10;

      boxes.push({
        id: `box-${camId}-${i}-${Date.now().toString().slice(-4)}`,
        type,
        confidence: conf,
        speedKmH: speed,
        rect: { top: `${top}%`, left: `${left}%`, width: `${width}%`, height: `${height}%` },
        licensePlate: `ABC-${Math.floor(1000 + Math.random() * 9000)}`,
        isViolating: speed > 55 && Math.random() > 0.7
      });
    }
    return boxes;
  }

  // Subscribe to real-time telemetry updates
  subscribe(callback) {
    this.listeners.add(callback);
    if (!this.timer) {
      this.timer = setInterval(() => this._tick(), 2000);
    }
    return () => {
      this.listeners.delete(callback);
      if (this.listeners.size === 0 && this.timer) {
        clearInterval(this.timer);
        this.timer = null;
      }
    };
  }

  _tick() {
    // Tick down countdowns & fluctuate metrics slightly
    this.systemState.signals = this.systemState.signals.map(sig => {
      let nextCd = sig.countdown - 2;
      let nextStatus = sig.status;
      if (nextCd <= 0) {
        if (sig.status === 'GREEN') { nextStatus = 'YELLOW'; nextCd = 4; }
        else if (sig.status === 'YELLOW') { nextStatus = 'RED'; nextCd = 25; }
        else { nextStatus = 'GREEN'; nextCd = 30; }
      }
      return { ...sig, countdown: nextCd, status: nextStatus };
    });

    // Random minor fluctuation in metrics
    const deltaVehicles = Math.floor((Math.random() - 0.48) * 8);
    this.systemState.totalVehicles = Math.max(120, this.systemState.totalVehicles + deltaVehicles);
    this.systemState.avgSpeedKmH = +(Math.max(12, Math.min(65, this.systemState.avgSpeedKmH + (Math.random() - 0.5) * 1.5))).toFixed(1);

    this.listeners.forEach(cb => cb(this.systemState));
  }

  // Action methods (Ready to connect to API backend)
  updateSignalState(signalId, newStatus, mode = 'AI_ADAPTIVE') {
    this.systemState.signals = this.systemState.signals.map(s => 
      s.id === signalId ? { ...s, status: newStatus, countdown: 40, mode } : s
    );
    this._tick();
  }

  triggerEmergencyOverride(intersectionId) {
    this.systemState.signals = this.systemState.signals.map(s => 
      s.id === intersectionId ? { ...s, status: 'GREEN', countdown: 99, mode: 'EMERGENCY_OVERRIDE' } : s
    );
    this.systemState.incidents.unshift({
      id: `inc-emg-${Date.now().toString().slice(-4)}`,
      type: 'EMERGENCY_ROUTING',
      location: `Intersection ${intersectionId}`,
      timestamp: new Date().toISOString(),
      severity: 'CRITICAL',
      status: 'ACTIVE',
      description: 'Emergency priority passage initiated for inbound responder unit.'
    });
    this._tick();
  }
}

export const mockTrafficService = new MockTrafficService();
