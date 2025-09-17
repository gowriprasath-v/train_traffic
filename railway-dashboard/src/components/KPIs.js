import React from "react";

function KPIs({ metrics = {} }) {
  // Defensive check and flatten only primitive values
  const entries = Object.entries(metrics).filter(
    ([, val]) => typeof val === "string" || typeof val === "number"
  );

  const defaultMetrics = [
    ["throughput", "15 trains/hr"],
    ["avg_delay", "5 minutes"],
    ["platform_utilization", "80%"],
    ["punctuality", "90%"],
  ];

  const metricLabels = {
    throughput: "Throughput",
    avg_delay: "Avg delay",
    platform_utilization: "Platform utilization",
    punctuality: "Punctuality",
  };

  // 🔵 Unified blue color theme
  const valueColor = "#2764adff";

  const metricsToShow = entries.length > 0 ? entries : defaultMetrics;

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gap: "12px", // tighter spacing
      }}
    >
      {metricsToShow.map(([key, value]) => {
        const cleanValue =
          typeof value === "string" ? value : value.toString();

        // Extract percentage number if present (for progress bar)
        const percentMatch = cleanValue.match(/(\d+)%/);
        const percent = percentMatch ? parseInt(percentMatch[1], 10) : null;

        return (
          <div
            key={key}
            className="kpi-card"
            style={{
              background: "rgba(255, 255, 255, 0.7)",
              backdropFilter: "blur(10px)",
              WebkitBackdropFilter: "blur(10px)",
              borderRadius: "12px",
              padding: "14px 16px", // smaller padding
              boxShadow: "0 3px 8px rgba(0,0,0,0.08)",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              minHeight: "90px", // smaller height
              transition: "transform 0.2s ease, box-shadow 0.2s ease",
            }}
          >
            <span
              style={{
                fontSize: "1rem",
                color: "#333",
                fontWeight: 600, // bolder label
              }}
            >
              {metricLabels[key] || key}
            </span>

            <span
              style={{
                fontSize: "1.4rem",
                fontWeight: 800, // extra bold value
                color: valueColor,
                marginTop: "4px",
              }}
            >
              {cleanValue}
            </span>

            {/* Show progress bar for metrics with % values */}
            {percent !== null && (
              <div
                style={{
                  width: "100%",
                  height: "5px",
                  borderRadius: "4px",
                  background: "rgba(0,0,0,0.1)",
                  marginTop: "8px",
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    width: `${percent}%`,
                    height: "100%",
                    background: valueColor,
                    borderRadius: "4px",
                  }}
                />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

export default KPIs;
