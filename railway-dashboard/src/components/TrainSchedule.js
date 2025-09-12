import React from 'react';

function TrainSchedule() {
  const trains = [
    { name: "Indian Express", scheduled: "14:30", arrival: "14:35", departure: "14:40", status: "On time" },
    { name: "Kalanidhi Express", scheduled: "14:45", arrival: "14:45", departure: "", status: "Delayed" },
    { name: "Kaifiyat Express", scheduled: "15:00", arrival: "15:00", departure: "15:05", status: "On time" },
    { name: "Garib Rath", scheduled: "15:15", arrival: "", departure: "", status: "Cancelled" }
  ];
  const statusColor = status =>
    status === "On time" ? "#27ae60" :
    status === "Delayed" ? "#e67e22" :
    status === "Cancelled" ? "#e74c3c" : "#222";
  return (
    <table style={{ width: "100%", borderCollapse: "collapse" }}>
      <thead>
        <tr>
          <th>Train</th>
          <th>Scheduled</th>
          <th>Arrival</th>
          <th>Departure</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {trains.map((train, i) => (
          <tr key={i}>
            <td>{train.name}</td>
            <td>{train.scheduled}</td>
            <td>{train.arrival}</td>
            <td>{train.departure}</td>
            <td style={{ color: statusColor(train.status), fontWeight: 'bold' }}>{train.status}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
export default TrainSchedule;
