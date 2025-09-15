import React from 'react';

function TrainSchedule({ trains = [] }) {
  const safeTrains = trains.length > 0 ? trains : [];

  // Improved status badge color logic
  const getStatusStyle = (status) => {
    const st = status.toLowerCase().replace(" ", "_");
    if (st === 'on_time' || st === 'ontime' || st === 'on time')
      return { backgroundColor: '#d4edda', color: '#155724', borderColor: '#c3e6cb' }; // green
    if (st === 'delayed')
      return { backgroundColor: '#fff3cd', color: '#856404', borderColor: '#ffeeba' }; // yellow/orange
    if (st === 'cancelled')
      return { backgroundColor: '#f8d7da', color: '#721c24', borderColor: '#f5c6cb' }; // red
    if (st === 'early')
      return { backgroundColor: '#d1ecf1', color: '#0c5460', borderColor: '#bee5eb' }; // blue
    return { backgroundColor: '#e2e3e5', color: '#383d41', borderColor: '#d6d8db' }; // gray
  };

  return (
    <div className="train-schedule-container">
      <table className="train-schedule-table" cellSpacing="0" cellPadding="0">
        <thead>
          <tr>
            {['Train', 'Scheduled', 'Arrival', 'Departure', 'Platform', 'Status'].map((header) => (
              <th key={header}>{header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {safeTrains.map((train, idx) => {
            const badgeStyle = getStatusStyle(train.status || '');
            return (
              <tr key={idx} className="train-row animate-fadeIn">
                <td>{train.name || 'Unknown'}</td>
                <td>{train.scheduled || '—'}</td>
                <td>{train.arrival || '—'}</td>
                <td>{train.departure || '—'}</td>
                <td>{train.platform || '—'}</td>
                <td>
                  <span className="status-badge" style={badgeStyle}>
                    {train.status || 'Unknown'}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {/* Mobile friendly cards */}
      <div className="train-cards">
        {safeTrains.map((train, idx) => {
          const badgeStyle = getStatusStyle(train.status || '');
          return (
            <div key={idx} className="train-card animate-fadeIn">
              <div className="train-card-header">{train.name || 'Unknown'}</div>
              <div><strong>Scheduled:</strong> {train.scheduled || '—'}</div>
              <div><strong>Arrival:</strong> {train.arrival || '—'}</div>
              <div><strong>Departure:</strong> {train.departure || '—'}</div>
              <div><strong>Platform:</strong> {train.platform || '—'}</div>
              <div>
                <span className="status-badge" style={badgeStyle}>
                  {train.status || 'Unknown'}
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
