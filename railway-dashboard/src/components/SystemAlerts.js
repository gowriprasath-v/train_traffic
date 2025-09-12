import React from 'react';

function SystemAlerts({ alerts }) {
  return (
    <ul style={{ listStyle: 'none', paddingLeft: 0, margin: 0 }}>
      {alerts.map((alert, i) => (
        <li key={i} style={{ 
          marginBottom: '10px', 
          display: 'flex', 
          alignItems: 'center', 
          color: '#ad5600',
          fontSize: '14px',
          fontWeight: '500'
        }}>
          <span style={{ marginRight: '10px' }}>⚠️</span> 
          {alert}
        </li>
      ))}
    </ul>
  );
}

export default SystemAlerts;
