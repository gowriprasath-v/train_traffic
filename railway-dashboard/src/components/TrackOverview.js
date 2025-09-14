import React from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import 'leaflet/dist/leaflet.css';

export default function TrackOverview({ station }) {
  const stationsCoords = {
    "Kanpur Central": [26.4499, 80.3319],
    Lucknow: [26.8467, 80.9462],
    "Delhi Junction": [28.6500, 77.2300],
    Varanasi: [25.3176, 82.9739],
    Allahabad: [25.4358, 81.8463],
  };
  const position = stationsCoords[station] || [26.4499, 80.3319];

  return (
    <div style={{ borderRadius: 14, overflow: "hidden", minHeight: 240 }}>
      <MapContainer center={position} zoom={15} style={{ height: "240px", width: "100%" }}>
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Marker position={position}>
          <Popup>{station} Railway Station</Popup>
        </Marker>
      </MapContainer>
    </div>
  );
}
