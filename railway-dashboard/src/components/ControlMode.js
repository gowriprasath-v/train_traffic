import React, { useState } from "react";

function ControlMode() {
  const [mode, setMode] = useState("Manual");
  const [showModal, setShowModal] = useState(false);

  // Dummy corrected schedule data
  const dummySchedule = [
    { train: "Indian Express", scheduled: "14:30", arrival: "14:35", departure: "14:40", platform: "1A" },
    { train: "Kalanidhi Express", scheduled: "14:45", arrival: "14:45", departure: "—", platform: "2B" },
    { train: "Kaifiyat Express", scheduled: "15:00", arrival: "15:00", departure: "15:05", platform: "3" },
    { train: "Garib Rath", scheduled: "15:15", arrival: "—", departure: "—", platform: "1" },
  ];

  const handleAIControl = () => {
    setMode("AI Control");
    setShowModal(true);
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "20px",
        padding: "24px",
        maxWidth: "400px",
        margin: "0 auto",
        border: "1px solid #ccc",
        borderRadius: "12px",
        boxSizing: "border-box",
      }}
    >
      <h2 style={{ margin: 0 }}>Control Mode</h2>
      <p style={{ textAlign: "center", margin: 0 }}>
        Do you want to hold the train manually or let AI decide?
      </p>

      <div
        style={{
          display: "flex",
          justifyContent: "center",
          gap: "40px",
          marginTop: "10px",
        }}
      >
        <button
          onClick={() => setMode("Manual")}
          style={{
            backgroundColor: mode === "Manual" ? "#000" : "#fff",
            color: mode === "Manual" ? "#fff" : "#000",
            borderRadius: "25px",
            padding: "10px 28px",
            cursor: "pointer",
            border: "1px solid #000",
            fontWeight: 600,
            transition: "all 0.2s ease",
          }}
        >
          Manually
        </button>

        <button
          onClick={handleAIControl}
          style={{
            backgroundColor: mode === "AI Control" ? "#000" : "#fff",
            color: mode === "AI Control" ? "#fff" : "#000",
            borderRadius: "25px",
            padding: "10px 28px",
            cursor: "pointer",
            border: "1px solid #000",
            fontWeight: 600,
            transition: "all 0.2s ease",
          }}
        >
          AI Control
        </button>
      </div>

      {/* Modal */}
      {showModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0,0,0,0.4)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
          }}
        >
          <div
            style={{
              background: "#fff",
              borderRadius: "12px",
              padding: "20px",
              maxWidth: "700px",
              width: "90%",
              boxShadow: "0 4px 20px rgba(0,0,0,0.2)",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "16px",
              }}
            >
              <h3 style={{ margin: 0 }}>Corrected Schedule</h3>
              <button
                onClick={() => setShowModal(false)}
                style={{
                  background: "transparent",
                  border: "none",
                  fontSize: "20px",
                  cursor: "pointer",
                }}
              >
                ×
              </button>
            </div>

            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ background: "#f5f5f5" }}>
                  <th style={thStyle}>Train</th>
                  <th style={thStyle}>Scheduled</th>
                  <th style={thStyle}>Arrival</th>
                  <th style={thStyle}>Departure</th>
                  <th style={thStyle}>Platform</th>
                </tr>
              </thead>
              <tbody>
                {dummySchedule.map((row, idx) => (
                  <tr
                    key={idx}
                    style={{
                      background: idx % 2 === 0 ? "#fff" : "#f9f9f9",
                    }}
                  >
                    <td style={tdStyle}>{row.train}</td>
                    <td style={tdStyle}>{row.scheduled}</td>
                    <td style={tdStyle}>{row.arrival}</td>
                    <td style={tdStyle}>{row.departure}</td>
                    <td style={tdStyle}>{row.platform}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div
              style={{
                display: "flex",
                justifyContent: "center",
                gap: "20px",
                marginTop: "20px",
              }}
            >
              <button style={modalButton}>Edit Manually</button>
              <button style={modalButton}>Accept Changes</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Reusable table/button styles
const thStyle = {
  textAlign: "left",
  padding: "8px",
  borderBottom: "1px solid #ddd",
};

const tdStyle = {
  padding: "8px",
  borderBottom: "1px solid #eee",
};

const modalButton = {
  border: "1px solid #000",
  borderRadius: "8px",
  padding: "10px 20px",
  cursor: "pointer",
  fontWeight: 600,
  background: "#fff",
};

export default ControlMode;
