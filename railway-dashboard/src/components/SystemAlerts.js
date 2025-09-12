import React from 'react';

function SystemAlerts({ alerts }) {
  // Helper: parse alert string to object safely
  const parseAlert = (alertStr) => {
    try {
      return JSON.parse(alertStr);
    } catch {
      // If parsing fails, fallback to raw string
      return { message: alertStr };
    }
  };

  // Helper to get styling from alert level
  const getStyle = (level) => {
    switch (level) {
      case "info":
        return { color: "#007bff", icon: "ℹ️" };
      case "warning":
        return { color: "#f0ad4e", icon: "⚠️" };
      case "high":
      case "error":
        return { color: "#d9534f", icon: "🚨" };
      default:
        return { color: "#6c757d", icon: "🔔" };
    }
  };

  // Helper to format ISO date to readable
  const formatTime = (isoStr) => {
    if (!isoStr) return "";
    const date = new Date(isoStr);
    return date.toLocaleString("en-IN", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <ul style={{ listStyle: "none", paddingLeft: 0, margin: 0 }}>
      {alerts.map((alertStr, i) => {
        const alert = parseAlert(alertStr);
        const { message, level = "", timestamp = "" } = alert;
        const { color, icon } = getStyle(level.toLowerCase());
        const timeStr = formatTime(timestamp);

        return (
          <li
            key={i}
            style={{
              marginBottom: 14,
              display: "flex",
              alignItems: "center",
              color,
              fontSize: 14,
              fontWeight: 500,
              whiteSpace: "pre-wrap",
              justifyContent: "space-between",
            }}
          >
            <span>
              <span style={{ marginRight: 8 }}>{icon}</span>
              {message || "No message"}
            </span>
            <span style={{ fontSize: 12, color: "#555", marginLeft: 12 }}>
              {timeStr}
            </span>
          </li>
        );
      })}
    </ul>
  );
}

export default SystemAlerts;
