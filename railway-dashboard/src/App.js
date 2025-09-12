import React, { useState } from 'react';
import './App.css';
import DashboardLayout from './components/DashboardLayout';
import TrackOverview from './components/TrackOverview';
import SystemAlerts from './components/SystemAlerts';
import ControlMode from './components/ControlMode';
import KPIs from './components/KPIs';
import TrainSchedule from './components/TrainSchedule';

function App() {
  // Create state for dynamic alerts
  const [alerts, setAlerts] = useState([
    "Platform 2 signal failure - manual control required (High)",
    "Train 443 running 10 minutes late (Medium)"
  ]);

  // Functions to add different alerts
  const addEmergencyAlert = () => {
    setAlerts([
      ...alerts,
      "⚡ Disruption: Overhead equipment failure at Track 4. Immediate action required!"
    ]);
  };

  const addTrainDelay = () => {
    setAlerts([
      ...alerts, 
      "🚂 Express 205 delayed by 25 minutes - mechanical issue"
    ]);
  };

  const addWeatherAlert = () => {
    setAlerts([
      ...alerts, 
      "🌧️ Heavy rain warning - reduce speed on all tracks"
    ]);
  };

  const resetAlerts = () => {
    setAlerts([
      "Platform 2 signal failure - manual control required (High)",
      "Train 443 running 10 minutes late (Medium)"
    ]);
  };

  return (
    <div>
      {/* SIMULATION BUTTONS - These should appear at the top */}
      <div style={{
        display: 'flex',
        gap: '15px',
        padding: '20px',
        justifyContent: 'center',
        flexWrap: 'wrap',
        backgroundColor: '#f0f0f0',
        borderBottom: '2px solid #ddd'
      }}>
        <button onClick={addEmergencyAlert} style={{
          backgroundColor: '#ff4444',
          color: 'white',
          padding: '12px 20px',
          border: 'none',
          borderRadius: '8px',
          cursor: 'pointer',
          fontWeight: 'bold',
          fontSize: '14px'
        }}>
          🚨 Simulate Emergency
        </button>

        <button onClick={addTrainDelay} style={{
          backgroundColor: '#ff8800',
          color: 'white',
          padding: '12px 20px',
          border: 'none',
          borderRadius: '8px',
          cursor: 'pointer',
          fontWeight: 'bold',
          fontSize: '14px'
        }}>
          🚂 Add Train Delay
        </button>

        <button onClick={addWeatherAlert} style={{
          backgroundColor: '#0088ff',
          color: 'white',
          padding: '12px 20px',
          border: 'none',
          borderRadius: '8px',
          cursor: 'pointer',
          fontWeight: 'bold',
          fontSize: '14px'
        }}>
          🌧️ Weather Alert
        </button>

        <button onClick={resetAlerts} style={{
          backgroundColor: '#666666',
          color: 'white',
          padding: '12px 20px',
          border: 'none',
          borderRadius: '8px',
          cursor: 'pointer',
          fontWeight: 'bold',
          fontSize: '14px'
        }}>
          🔄 Reset Alerts
        </button>
      </div>

      {/* MAIN DASHBOARD */}
      <DashboardLayout
        stationName="Kanpur Central"
        dateTime="3rd Sep 2025 | 05:42 pm (IST)"
        trackOverview={<TrackOverview />}
        systemAlerts={<SystemAlerts alerts={alerts} />}
        controlMode={<ControlMode />}
        kpis={<KPIs />}
        trainSchedule={<TrainSchedule />}
      />
    </div>
  );
}

export default App;
