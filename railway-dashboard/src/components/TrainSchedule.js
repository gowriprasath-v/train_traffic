import React from 'react';

function TrainSchedule({ trains = [] }) {
  // If no trains provided, use default data
  const defaultTrains = [
    { name: "Indian Express", scheduled: "14:30", arrival: "14:35", departure: "14:40", status: "On time" },
    { name: "Kalanidhi Express", scheduled: "14:45", arrival: "14:45", departure: "", status: "Delayed" },
    { name: "Kaifiyat Express", scheduled: "15:00", arrival: "15:00", departure: "15:05", status: "On time" },
    { name: "Garib Rath", scheduled: "15:15", arrival: "", departure: "", status: "Cancelled" }
  ];

  const trainsToShow = trains.length > 0 ? trains : defaultTrains;

  const statusClass = status =>
    status === "On time" ? "status-on" :
    status === "Delayed" ? "status-delayed" :
    status === "Cancelled" ? "status-cancelled" : "";

  return (
    <table>
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
        {trainsToShow.map((train, i) => (
          <tr key={i}>
            <td>{train.name}</td>
            <td>{train.scheduled}</td>
            <td>{train.arrival}</td>
            <td>{train.departure}</td>
            <td className={statusClass(train.status)}>{train.status}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default TrainSchedule;
