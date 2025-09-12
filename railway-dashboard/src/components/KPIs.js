import React from 'react';

function KPIs() {
  const metrics = [
    { label: 'Throughput', value: '15 trains/hr' },
    { label: 'Avg delay', value: ' 11 sakthi' },
    { label: 'Platform utilization', value: '80%' },
    { label: 'Punctuality rate', value: '90%' },
  ];
  return (
    <div>
      {metrics.map((item, i) => (
        <div key={i} style={{
          backgroundColor: '#f3f4f6',
          borderRadius: '10px',
          padding: '12px 16px',
          fontWeight: '600',
          display: 'flex',
          justifyContent: 'space-between',
          marginBottom: 6,
          fontSize: '1rem'
        }}>
          <span>{item.label}</span>
          <span>{item.value}</span>
        </div>
      ))}
    </div>
  );
}
export default KPIs;
