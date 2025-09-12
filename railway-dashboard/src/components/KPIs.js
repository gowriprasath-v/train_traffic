import React from 'react';

function KPIs({ metrics = {} }) {
  // Defensive check and flatten only primitive values
  const entries = Object.entries(metrics).filter(([key, val]) => 
    typeof val === 'string' || typeof val === 'number'
  );

  const defaultMetrics = [
    ['throughput', '15 trains/hr'],
    ['avg_delay', '5 minutes'],
    ['platform_utilization', '80%'],
    ['punctuality_rate', '90%']
  ];

  const metricLabels = {
    throughput: "Throughput",
    avg_delay: "Avg delay",
    platform_utilization: "Platform utilization",
    punctuality_rate: "Punctuality rate"
  };

  const metricsToShow = entries.length > 0 ? entries : defaultMetrics;

  return (
    <>
      {metricsToShow.map(([key, value]) => (
        <div key={key} style={{
          backgroundColor: '#f8f8fa',
          borderRadius: '10px',
          padding: '14px 20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontWeight: '600',
          fontSize: '1rem',
          marginBottom: 6,
          border: '1px solid #eee'
        }}>
          <span>{metricLabels[key] || key}</span>
          <span>{value.toString()}</span> {/* Ensure value is string */}
        </div>
      ))}
    </>
  );
}

export default KPIs;
