import React from 'react';

function SystemAlerts({ alerts }) {
  // Parse alert string to object safely
  const parseAlert = (alertStr) => {
    try {
      return JSON.parse(alertStr);
    } catch {
      return { message: alertStr };
    }
  };

  // Styling per alert level
  const getStyle = (level) => {
    switch (level) {
      case "info":
        return { color: "#007bff", border: "#007bff30", icon: "ℹ️" };
      case "warning":
        return { color: "#f0ad4e", border: "#f0ad4e30", icon: "⚠️" };
      case "high":
      case "error":
        return { color: "#d9534f", border: "#d9534f30", icon: "🚨" };
      default:
        return { color: "#6c757d", border: "#6c757d30", icon: "⚠️"};
    }
  };

  // Format ISO date
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
    <ul style={{ listStyle: "none", padding:0, margin: 0 }}>
      {alerts.map((alertStr, i) => {
        const alert = parseAlert(alertStr);
        const { message, level = "", timestamp = "" } = alert;
        const { color, border, icon } = getStyle(level.toLowerCase());
        const timeStr = formatTime(timestamp);

        return (
          <li
            key={i}
            style={{
              marginBottom: 6,
              padding: "15px 10px",
              border: `1px solid ${border}`,     // ✅ border color per level
              borderRadius: 10,                  // ✅ rounded corners
              background: "#fff",
              boxShadow: "0 1px 2px rgba(0,0,0,0.08)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span style={{ color, fontWeight: 600, fontSize: 14 }}>
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
