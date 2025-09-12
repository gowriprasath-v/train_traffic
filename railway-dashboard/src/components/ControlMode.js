import React, { useState } from 'react';

function ControlMode() {
  const [mode, setMode] = useState('Manual');
  return (
    <div>
      <strong>Control mode</strong>
      <p>Do you want to hold the train manually or let AI decide?</p>
      <div style={{ display: 'flex', gap: '10px' }}>
        <button
          onClick={() => setMode('Manual')}
          style={{
            backgroundColor: mode === 'Manual' ? '#000' : '#fff',
            color: mode === 'Manual' ? '#fff' : '#000',
            borderRadius: '20px',
            padding: '8px 20px',
            cursor: 'pointer',
            border: '1px solid #000',
            fontWeight: '600'
          }}
        >
          Manually
        </button>
        <button
          onClick={() => setMode('AI Control')}
          style={{
            backgroundColor: mode === 'AI Control' ? '#000' : '#fff',
            color: mode === 'AI Control' ? '#fff' : '#000',
            borderRadius: '20px',
            padding: '8px 20px',
            cursor: 'pointer',
            border: '1px solid #000',
            fontWeight: '600'
          }}
        >
          AI Control
        </button>
      </div>
    </div>
  );
}
export default ControlMode;
