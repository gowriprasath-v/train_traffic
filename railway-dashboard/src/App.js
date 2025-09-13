import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import "./App.css";
import DashboardLayout from "./components/DashboardLayout";
import TrackOverview from "./components/TrackOverview";
import SystemAlerts from "./components/SystemAlerts";
import ControlMode from "./components/ControlMode";
import KPIs from "./components/KPIs";
import TrainSchedule from "./components/TrainSchedule";

// Optional: Simple spinner component
function Spinner() {
  return <span style={{ marginLeft: 10, fontSize: 16 }}>⏳</span>;
}

function App() {
  // State hooks for each section
  const [alerts, setAlerts] = useState([]);
  const [trains, setTrains] = useState([]);
  const [metrics, setMetrics] = useState({});
  const [loadingAlerts, setLoadingAlerts] = useState(false);
  const [loadingTrains, setLoadingTrains] = useState(false);
  const [loadingMetrics, setLoadingMetrics] = useState(false);
  const [error, setError] = useState(null);

  const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

  // Fetch alert data
  const fetchAlerts = useCallback(async () => {
    setLoadingAlerts(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/alerts`);
      const rawAlerts = response.data.alerts || [];
      const safeAlerts = rawAlerts.map((a) =>
        typeof a === "string" ? a : JSON.stringify(a)
      );
      setAlerts(safeAlerts);
    } catch (error) {
      setAlerts([
        "Platform 2 signal failure (fallback)",
        "Train 443 running late (fallback)",
      ]);
    } finally {
      setLoadingAlerts(false);
    }
  }, [API_BASE_URL]);

  // Fetch train schedule
  const fetchSchedule = useCallback(async () => {
    setLoadingTrains(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/schedule`);
      const schedule = response.data.schedule;
      if (schedule && schedule.trains) {
        const safeTrains = schedule.trains.map((train) => ({
          name: train.name || train.train_id,
          scheduled: String(train.scheduled_time || train.arrival || ""),
          arrival: String(train.arrival || ""),
          departure: String(train.departure || ""),
          status: String(train.status || ""),
        }));
        setTrains(safeTrains);
      } else {
        setTrains([]);
      }
    } catch (error) {
      setTrains([
        {
          name: "Indian Express",
          scheduled: "14:30",
          arrival: "14:35",
          departure: "14:40",
          status: "On time",
        },
        {
          name: "Kalanidhi Express",
          scheduled: "14:45",
          arrival: "14:45",
          departure: "—",
          status: "Delayed",
        },
        {
          name: "Kaifiyat Express",
          scheduled: "15:00",
          arrival: "15:00",
          departure: "15:05",
          status: "On time",
        },
        {
          name: "Garib Rath",
          scheduled: "15:15",
          arrival: "—",
          departure: "—",
          status: "Cancelled",
        },
      ]);
    } finally {
      setLoadingTrains(false);
    }
  }, [API_BASE_URL]);

  // Fetch metrics
  const fetchMetrics = useCallback(async () => {
    setLoadingMetrics(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/metrics`);
      const data = response.data.metrics || {};
      const safeMetrics = {};
      for (const key in data) {
        safeMetrics[key] =
          typeof data[key] === "object" ? JSON.stringify(data[key]) : data[key];
      }
      setMetrics(safeMetrics);
    } catch (error) {
      setMetrics({
        throughput: "15 trains/hr",
        avg_delay: "5 minutes",
        platform_utilization: "80%",
        punctuality: "90%",
      });
    } finally {
      setLoadingMetrics(false);
    }
  }, [API_BASE_URL]);

  // Fetch all dashboard data
  const fetchAllData = useCallback(async () => {
    setError(null);
    fetchAlerts();
    fetchSchedule();
    fetchMetrics();
  }, [fetchAlerts, fetchSchedule, fetchMetrics]);

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 30000);
    return () => clearInterval(interval);
  }, [fetchAllData]);

  // Button actions
  const addAlert = async (type, message, severity = "medium") => {
    try {
      await axios.post(`${API_BASE_URL}/alerts`, {
        type,
        message,
        severity,
        timestamp: new Date().toISOString(),
      });
      fetchAlerts();
    } catch (error) {
      setAlerts((old) => [...old, message]);
    }
  };

  // Error message shown at top, but dashboard always visible.
  return (
    <div className="app-gradient" style={{ minHeight: "100vh" }}>
      {error && (
        <div
          style={{
            color: "red",
            textAlign: "center",
            padding: "8px",
            fontWeight: "bold",
            fontSize: 16,
            background: "#fff2f2",
            marginBottom: "8px",
          }}
        >
          Error: {error}
        </div>
      )}
      {/* Simulation Buttons */}
      <div
        style={{
          padding: 20,
          display: "flex",
          gap: 15,
          flexWrap: "wrap",
          justifyContent: "center",
        }}
      >
        <button
          onClick={() =>
            addAlert(
              "emergency",
              "⚡ Disruption: Overhead equipment failure at Track 4. Immediate action required!",
              "high"
            )
          }
          style={buttonStyle("#ff4444")}
        >
          🚨 Simulate Emergency
        </button>
        <button
          onClick={() =>
            addAlert(
              "delay",
              "🚂 Express 205 delayed by 25 minutes - mechanical issue",
              "medium"
            )
          }
          style={buttonStyle("#ff8800")}
        >
          🚂 Add Train Delay
        </button>
        <button
          onClick={() =>
            addAlert(
              "weather",
              "🌧️ Heavy rain warning - reduce speed on all tracks",
              "medium"
            )
          }
          style={buttonStyle("#0088ff")}
        >
          🌧️ Add Weather Alert
        </button>
        <button onClick={fetchAllData} style={buttonStyle("#28a745")}>
          🔄 Refresh Data
        </button>
      </div>
      {/* Render Dashboard with per-section loading indicators */}
      <DashboardLayout
        stationName="Kanpur Central"
        dateTime={new Date().toLocaleString("en-IN", {
          timeZone: "Asia/Kolkata",
          year: "numeric",
          month: "short",
          day: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        })}
        trackOverview={<TrackOverview />}
        systemAlerts={
          <>
            <SystemAlerts alerts={alerts} />
            {loadingAlerts && <Spinner />}
          </>
        }
        controlMode={<ControlMode />}
        kpis={
          <>
            <KPIs metrics={metrics} />
            {loadingMetrics && <Spinner />}
          </>
        }
        trainSchedule={
          <>
            <TrainSchedule trains={trains} />
            {loadingTrains && <Spinner />}
          </>
        }
      />
    </div>
  );
}

const buttonStyle = (bgColor) => ({
  backgroundColor: bgColor,
  color: "white",
  padding: "12px 20px",
  borderRadius: 8,
  fontWeight: "bold",
  fontSize: 14,
  cursor: "pointer",
  border: "none",
});
export default App;