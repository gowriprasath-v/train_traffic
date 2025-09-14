import React from 'react';

function DashboardLayout({ 
  // Remove stationName here as text will be handled outside
  dateTime,
  trackOverview,
  trainSchedule,
  systemAlerts,
  controlMode,
  kpis,
  alertsBottom
}) {
  return (
    <div className="dashboard-grid">
      {/* Header */}
      <header className="dashboard-header">
        {/* Station selector dropdown or buttons should be rendered here externally */}
        <div className="station-selector-placeholder" />
        <div className="date-time">{dateTime}</div>
      </header>

      {/* Track Overview */}
      <section className="track-overview card">
        <h2>Track Overview</h2>
        {trackOverview}
      </section>

      {/* System Alerts */}
      <section className="system-alerts card">
        <h2>System alerts</h2>
        {systemAlerts}
      </section>

      {/* Train Schedule */}
      <section className="train-schedule card">
        <h2>Train Schedule</h2>
        {trainSchedule}
      </section>

      {/* Control Mode */}
      <section className="control-mode card">
        {controlMode}
      </section>

      {/* KPIs */}
      <section className="kpi-cards">
        {kpis}
      </section>

      {/* Bottom Alerts (optional) */}
      {alertsBottom && <section className="alerts-bottom">{alertsBottom}</section>}
    </div>
  );
}

export default DashboardLayout;
