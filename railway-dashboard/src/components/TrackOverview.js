import React from "react";
import { MapContainer, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";

export default function TrackOverview({ station }) {
  const stationsCoords = {
    "Kanpur Central": [26.4499, 80.3319],
    Lucknow: [26.8467, 80.9462],
    "Delhi Junction": [28.65, 77.23],
    Varanasi: [25.3176, 82.9739],
    Allahabad: [25.4358, 81.8463],
  };

  const position = stationsCoords[station] || [26.4499, 80.3319];

  return (
    <div
      style={{
        borderRadius: 14,
        overflow: "hidden",
        height: "240px",
        border: "2px solid #aeacbdff",
        display: "flex",            // 👈 ensures child fills container
      }}
    >
      <MapContainer
        center={position}
        zoom={15}
        style={{
          flex: 1,                   // 👈 fills all available space
          height: "100%",
          width: "100%",
        }}
      >
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
      </MapContainer>
    </div>
  );
}
