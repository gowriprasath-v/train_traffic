import React, { useState } from "react";

function TrainSchedule({ trains = [] }) {
  const [searchText, setSearchText] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const safeTrains = trains.length > 0 ? trains : [];

  // Badge color logic
  const getStatusStyle = (status) => {
    const st = status.toLowerCase().replace(" ", "_");
    if (st === "on_time" || st === "ontime" || st === "on time")
      return { backgroundColor: "#d4edda", color: "#155724", border: "1px solid #c3e6cb" };
    if (st === "delayed")
      return { backgroundColor: "#fff3cd", color: "#856404", border: "1px solid #ffeeba" };
    if (st === "cancelled")
      return { backgroundColor: "#f8d7da", color: "#721c24", border: "1px solid #f5c6cb" };
    if (st === "early")
      return { backgroundColor: "#d1ecf1", color: "#0c5460", border: "1px solid #bee5eb" };
    return { backgroundColor: "#e2e3e5", color: "#383d41", border: "1px solid #d6d8db" };
  };

  // Filtering
  const filteredTrains = safeTrains.filter((t) => {
    const matchesSearch =
      t.name?.toLowerCase().includes(searchText.toLowerCase()) ||
      t.platform?.toString().toLowerCase().includes(searchText.toLowerCase());
    const matchesStatus =
      statusFilter === "all" ||
      (t.status && t.status.toLowerCase().includes(statusFilter));
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="train-schedule-container" style={{ width: "100%" }}>
      {/* === Search + Filter Bar === */}
      <div
        className="search-filter-bar"
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "10px",
          marginBottom: "12px",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <input
          type="text"
          placeholder="Search by train name or platform..."
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          style={{
            flex: "1",
            minWidth: "220px",
            padding: "6px 10px",
            borderRadius: "6px",
            border: "1px solid #ccc",
            fontSize: "0.95rem",
          }}
        />

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          style={{
            padding: "6px 10px",
            borderRadius: "6px",
            border: "1px solid #ccc",
            fontSize: "0.95rem",
            background: "#fff",
          }}
        >
          <option value="all">All Status</option>
          <option value="on time">On Time</option>
          <option value="delayed">Delayed</option>
          <option value="cancelled">Cancelled</option>
          <option value="early">Early</option>
        </select>
      </div>

      {/* === VERTICAL SCROLL CONTAINER === */}
      <div
        style={{
          height: "350px",         // ✅ Fixed vertical size
          overflowY: "auto",       // ✅ Vertical scroll only
          border: "1px solid #ccc",
          borderRadius: "6px",
        }}
      >
        <table
          className="train-schedule-table"
          cellSpacing="0"
          cellPadding="0"
          style={{ width: "100%", tableLayout: "fixed" }} // keeps columns stable
        >
          <thead style={{ position: "sticky", top: 0, background: "#f9f9f9", zIndex: 1 }}>
            <tr>
              {["Train", "Scheduled", "Arrival", "Departure", "Platform", "Status"].map(
                (header) => (
                  <th key={header}>{header}</th>
                )
              )}
            </tr>
          </thead>
          <tbody>
            {filteredTrains.map((train, idx) => {
              const badgeStyle = getStatusStyle(train.status || "");
              return (
                <tr key={idx} className="train-row animate-fadeIn">
                  <td>{train.name || "Unknown"}</td>
                  <td>{train.scheduled || "—"}</td>
                  <td>{train.arrival || "—"}</td>
                  <td>{train.departure || "—"}</td>
                  <td>{train.platform || "—"}</td>
                  <td>
                    <span className="status-badge" style={badgeStyle}>
                      {train.status || "Unknown"}
                    </span>
                  </td>
                </tr>
              );
            })}
            {filteredTrains.length === 0 && (
              <tr>
                <td colSpan="6" style={{ textAlign: "center", padding: "8px" }}>
                  No trains found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* === MOBILE CARDS (unchanged) === */}
      <div className="train-cards">
        {filteredTrains.map((train, idx) => {
          const badgeStyle = getStatusStyle(train.status || "");
          return (
            <div key={idx} className="train-card animate-fadeIn">
              <div className="train-card-header">{train.name || "Unknown"}</div>
              <div><strong>Scheduled:</strong> {train.scheduled || "—"}</div>
              <div><strong>Arrival:</strong> {train.arrival || "—"}</div>
              <div><strong>Departure:</strong> {train.departure || "—"}</div>
              <div><strong>Platform:</strong> {train.platform || "—"}</div>
              <div>
                <span className="status-badge" style={badgeStyle}>
                  {train.status || "Unknown"}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default TrainSchedule;
