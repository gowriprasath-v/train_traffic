import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import "./App.css";
import DashboardLayout from "./components/DashboardLayout";
import TrackOverview from "./components/TrackOverview";
import SystemAlerts from "./components/SystemAlerts";
import ControlMode from "./components/ControlMode";
import KPIs from "./components/KPIs";
import TrainSchedule from "./components/TrainSchedule";
import 'leaflet/dist/leaflet.css'; // import leaflet CSS once here

// Spinner for loading states
function Spinner() {
  return <span style={{ marginLeft: 10, fontSize: 16 }}>⏳</span>;
}

// StationSelector dropdown component
function StationSelector({ stations, selectedStation, onChange }) {
  return (
    <select
      value={selectedStation}
      onChange={(e) => onChange(e.target.value)}
      style={{
        fontSize: "1.15rem",
        fontWeight: "600",
        padding: "6px 12px",
        borderRadius: 8,
        border: "1.5px solid #555770",
        cursor: "pointer",
        backgroundColor: "#4a3f72",
        color: "#eee",
        userSelect: "none",
      }}
    >
      {stations.map((station) => (
        <option key={station} value={station}>
          {station}
        </option>
      ))}
    </select>
  );
}

function App() {
  const stations = [
    "Kanpur Central",
    "Lucknow",
    "Delhi Junction",
    "Varanasi",
    "Allahabad",
  ];
  const [selectedStation, setSelectedStation] = useState(stations[0]);

  const [alerts, setAlerts] = useState([]);
  const [trains, setTrains] = useState([]);
  const [metrics, setMetrics] = useState({});
  const [loadingAlerts, setLoadingAlerts] = useState(false);
  const [loadingTrains, setLoadingTrains] = useState(false);
  const [loadingMetrics, setLoadingMetrics] = useState(false);
  const [error, setError] = useState(null);

  const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

  const fetchAlerts = useCallback(async () => {
    setLoadingAlerts(true);
    try {
      const response = await axios.get(
        `${API_BASE_URL}/alerts?station=${encodeURIComponent(selectedStation)}`
      );
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
  }, [selectedStation, API_BASE_URL]);

  const fetchSchedule = useCallback(async () => {
    setLoadingTrains(true);
    try {
      const response = await axios.get(
        `${API_BASE_URL}/schedule?station=${encodeURIComponent(selectedStation)}`
      );
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
  }, [selectedStation, API_BASE_URL]);

  const fetchMetrics = useCallback(async () => {
    setLoadingMetrics(true);
    try {
      const response = await axios.get(
        `${API_BASE_URL}/metrics?station=${encodeURIComponent(selectedStation)}`
      );
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
  }, [selectedStation, API_BASE_URL]);

  const fetchAllData = useCallback(() => {
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

  return (
    <div className="app-gradient" style={{ minHeight: "100vh", padding: 20 }}>
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
            borderRadius: 6,
          }}
        >
          Error: {error}
        </div>
      )}

      {/* Header area with Station Selector */}
      <div
        style={{
          display: "flex",
          justifyContent: "flex-start",
          alignItems: "center",
          marginBottom: 14,
        }}
      >
        <StationSelector
          stations={stations}
          selectedStation={selectedStation}
          onChange={setSelectedStation}
        />
      </div>

      {/* Dashboard Layout */}
      <DashboardLayout
        stationName={selectedStation}
        dateTime={new Date().toLocaleString("en-IN", {
          timeZone: "Asia/Kolkata",
          year: "numeric",
          month: "short",
          day: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        })}
        trackOverview={<TrackOverview station={selectedStation} />}
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

export default App;
