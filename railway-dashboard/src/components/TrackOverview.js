import React from "react";
import stationMap from "../assets/station-map.png"; // use your image from assets

// Example: Demo “track alerts” to show on map
const trackAlerts = [
  { track: "Track 2", status: "Maintenance", color: "#f4b402", position: { top: 45, left: 120 } },
  { track: "Track 4", status: "Reroute", color: "#e45859", position: { top: 105, left: 220 } }
];

export default function TrackOverview() {
  return (
    <div style={{ position: "relative", width: "100%", minHeight: "230px" }}>
      <img
        src={stationMap}
        alt="Track overview"
        style={{
          width: "100%",
          borderRadius: "12px",
          boxShadow: "0 2px 8px rgba(40,40,50,0.07)",
          objectFit: "cover",
          minHeight: "200px"
        }}
      />
      {/* Overlay colored badges on the map */}
      {trackAlerts.map((alert) => (
        <span
          key={alert.track}
          style={{
            position: "absolute",
            top: alert.position.top,
            left: alert.position.left,
            background: alert.color,
            color: "#fff",
            padding: "6px 14px",
            borderRadius: 9,
            fontWeight: 700,
            fontSize: "0.95rem",
            boxShadow: "0 1px 6px rgba(40,40,50,0.1)",
            border: "2px solid #fff"
          }}
        >
          {alert.track}: {alert.status}
        </span>
      ))}
    </div>
  );
}
