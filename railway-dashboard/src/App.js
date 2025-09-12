import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import "./App.css";
import DashboardLayout from "./components/DashboardLayout";
import TrackOverview from "./components/TrackOverview";
import SystemAlerts from "./components/SystemAlerts";
import ControlMode from "./components/ControlMode";
import KPIs from "./components/KPIs";
import TrainSchedule from "./components/TrainSchedule";

function App() {
  // State hooks
  const [alerts, setAlerts] = useState([]);
  const [trains, setTrains] = useState([]);
  const [metrics, setMetrics] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Backend base URL
  const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

  // Fetch alert data from API
  const fetchAlerts = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/alerts`);
      const rawAlerts = response.data.alerts || [];
      // Convert nested objects to strings to avoid React error
      const safeAlerts = rawAlerts.map((a) =>
        typeof a === "string" ? a : JSON.stringify(a)
      );
      setAlerts(safeAlerts);
    } catch (error) {
      console.error("Fetch alerts failed:", error);
      setAlerts([
        "Platform 2 signal failure (fallback)",
        "Train 443 running late (fallback)",
      ]);
    }
  }, [API_BASE_URL]);

  // Fetch train schedule from API
  const fetchSchedule = useCallback(async () => {
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
      console.error("Fetch schedule failed:", error);
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
    }
  }, [API_BASE_URL]);

  // Fetch performance metrics from API
  const fetchMetrics = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/metrics`);
      const data = response.data.metrics || {};
      // Sanitize to only string or numbers inside metrics
      const safeMetrics = {};
      for (const key in data) {
        safeMetrics[key] =
          typeof data[key] === "object" ? JSON.stringify(data[key]) : data[key];
      }
      setMetrics(safeMetrics);
    } catch (error) {
      console.error("Fetch metrics failed:", error);
      setMetrics({
        throughput: "15 trains/hr",
        avg_delay: "5 minutes",
        platform_utilization: "80%",
        punctuality: "90%",
      });
    }
  }, [API_BASE_URL]);

  // Combined fetch function
  const fetchAllData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await Promise.all([fetchAlerts(), fetchSchedule(), fetchMetrics()]);
    } catch (e) {
      setError("Failed to fetch dashboard data");
    } finally {
      setLoading(false);
    }
  }, [fetchAlerts, fetchSchedule, fetchMetrics]);

  useEffect(() => {
    fetchAllData();
    // Auto refresh every 30 seconds
    const interval = setInterval(fetchAllData, 30000);
    return () => clearInterval(interval);
  }, [fetchAllData]);

  // Simulate buttons calling backend or fallback locally
  const addAlert = async (type, message, severity = "medium") => {
    try {
      await axios.post(`${API_BASE_URL}/alerts`, {
        type,
        message,
        severity,
        timestamp: new Date().toISOString(),
      });
      await fetchAlerts();
    } catch (error) {
      console.error("Simulate alert failed", error);
      // fallback locally
      setAlerts((old) => [...old, message]);
    }
  };

  // UI render logic for loading/error
  if (loading)
    return (
      <div
        style={{
          height: "100vh",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          fontSize: 18,
        }}
      >
        Loading dashboard data...
      </div>
    );

  if (error)
    return (
      <div
        style={{
          height: "100vh",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          color: "red",
        }}
      >
        <h2>{error}</h2>
        <button onClick={fetchAllData}>Retry</button>
      </div>
    );

  // Main dashboard render
  return (
    <div>
      {/* Simulation Buttons */}
      <div
        style={{
          padding: 20,
          display: "flex",
          gap: 15,
          flexWrap: "wrap",
          backgroundColor: "#f0f0f0",
          borderBottom: "1.5px solid #ddd",
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
          style={{
            backgroundColor: "#ff4444",
            color: "white",
            padding: "12px 20px",
            borderRadius: 8,
            fontWeight: "bold",
            fontSize: 14,
            cursor: "pointer",
            border: "none",
          }}
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
          style={{
            backgroundColor: "#ff8800",
            color: "white",
            padding: "12px 20px",
            borderRadius: 8,
            fontWeight: "bold",
            fontSize: 14,
            cursor: "pointer",
            border: "none",
          }}
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
          style={{
            backgroundColor: "#0088ff",
            color: "white",
            padding: "12px 20px",
            borderRadius: 8,
            fontWeight: "bold",
            fontSize: 14,
            cursor: "pointer",
            border: "none",
          }}
        >
          🌧️ Add Weather Alert
        </button>
        <button
          onClick={fetchAllData}
          style={{
            backgroundColor: "#28a745",
            color: "white",
            padding: "12px 20px",
            borderRadius: 8,
            fontWeight: "bold",
            fontSize: 14,
            cursor: "pointer",
            border: "none",
          }}
        >
          🔄 Refresh Data
        </button>
      </div>
      {/* Render Dashboard */}
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
        systemAlerts={<SystemAlerts alerts={alerts} />}
        controlMode={<ControlMode />}
        kpis={<KPIs metrics={metrics} />}
        trainSchedule={<TrainSchedule trains={trains} />}
      />
    </div>
  );
}

export default App;
