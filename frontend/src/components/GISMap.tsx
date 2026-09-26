import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Intervention } from '../types/api';
import { Layers, MapPin, ZoomIn, ZoomOut, Compass } from 'lucide-react';

// Fix default Leaflet icon paths
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

interface GISMapProps {
  center?: [number, number];
  zoom?: number;
  interventions?: Intervention[];
  selectedInterventionId?: string | null;
  onSelectIntervention?: (id: string) => void;
  bufferDistances?: number[];
  showBuffers?: boolean;
  activeBufferDistance?: number;
  height?: string;
  className?: string;
}

export const GISMap: React.FC<GISMapProps> = ({
  center = [20.7002, 77.0082], // Default Akola, Maharashtra
  zoom = 13,
  interventions = [],
  selectedInterventionId,
  onSelectIntervention,
  bufferDistances = [100, 250, 500, 1000],
  showBuffers = true,
  activeBufferDistance = 250,
  height = '500px',
  className = '',
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersLayerRef = useRef<L.LayerGroup | null>(null);
  const bufferLayerRef = useRef<L.LayerGroup | null>(null);
  const [activeBaseLayer, setActiveBaseLayer] = useState<'satellite' | 'streets' | 'topo'>('satellite');

  // Tile layers definition
  const tileLayers = {
    satellite: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    streets: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    topo: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
  };

  const tileLayerRef = useRef<L.TileLayer | null>(null);

  // Initialize map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: center,
      zoom: zoom,
      zoomControl: false,
    });

    tileLayerRef.current = L.tileLayer(tileLayers.satellite, {
      attribution: '&copy; Esri, Maxar, Earthstar Geographics',
      maxZoom: 19,
    }).addTo(map);

    markersLayerRef.current = L.layerGroup().addTo(map);
    bufferLayerRef.current = L.layerGroup().addTo(map);

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update base tile layer
  useEffect(() => {
    if (!mapInstanceRef.current || !tileLayerRef.current) return;
    mapInstanceRef.current.removeLayer(tileLayerRef.current);

    const attributions = {
      satellite: '&copy; Esri, Maxar, Earthstar Geographics',
      streets: '&copy; OpenStreetMap contributors',
      topo: '&copy; OpenTopoMap (CC-BY-SA)',
    };

    tileLayerRef.current = L.tileLayer(tileLayers[activeBaseLayer], {
      attribution: attributions[activeBaseLayer],
      maxZoom: 19,
    }).addTo(mapInstanceRef.current);
  }, [activeBaseLayer]);

  // Update center & zoom when prop changes
  useEffect(() => {
    if (mapInstanceRef.current && center) {
      mapInstanceRef.current.setView(center, zoom, { animate: true });
    }
  }, [center[0], center[1], zoom]);

  // Render markers & circular buffer rings
  useEffect(() => {
    if (!mapInstanceRef.current || !markersLayerRef.current || !bufferLayerRef.current) return;

    markersLayerRef.current.clearLayers();
    bufferLayerRef.current.clearLayers();

    interventions.forEach((item) => {
      const lat = item.latitude;
      const lng = item.longitude;
      if (!lat || !lng) return;

      const isSelected = item.id === selectedInterventionId;

      // Custom marker styling
      const markerColor = isSelected ? '#047857' : '#0284c7';
      const markerHtml = `
        <div style="
          background-color: ${markerColor};
          width: ${isSelected ? '24px' : '18px'};
          height: ${isSelected ? '24px' : '18px'};
          border-radius: 50%;
          border: 2px solid white;
          box-shadow: 0 2px 6px rgba(0,0,0,0.4);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: bold;
          font-size: 10px;
        ">
          ${isSelected ? '★' : ''}
        </div>
      `;

      const customIcon = L.divIcon({
        className: 'custom-gis-pin',
        html: markerHtml,
        iconSize: [24, 24],
        iconAnchor: [12, 12],
      });

      const marker = L.marker([lat, lng], { icon: customIcon });

      marker.bindPopup(`
        <div style="font-family: sans-serif; font-size: 12px; line-height: 1.4;">
          <strong style="color: #0f172a; font-size: 13px;">${item.name}</strong><br/>
          <span style="color: #64748b;">${item.village}, ${item.district}</span><br/>
          <span style="display:inline-block; margin-top:4px; padding: 2px 6px; background:#f1f5f9; border-radius: 4px; font-weight:600; font-size:10px; text-transform:uppercase;">
            ${item.type.replace('_', ' ')}
          </span><br/>
          <span style="color: #047857; font-size: 11px;">Status: ${item.status}</span>
        </div>
      `);

      marker.on('click', () => {
        if (onSelectIntervention) {
          onSelectIntervention(item.id);
        }
        mapInstanceRef.current?.flyTo([lat, lng], Math.max(mapInstanceRef.current.getZoom(), 14), {
          duration: 0.8,
        });
      });

      markersLayerRef.current?.addLayer(marker);

      // Render GIS Buffers for selected item
      if (isSelected && showBuffers) {
        const bufferColors: Record<number, string> = {
          100: '#ef4444',
          250: '#f59e0b',
          500: '#10b981',
          1000: '#3b82f6',
        };

        bufferDistances.forEach((dist) => {
          const isBufferActive = dist === activeBufferDistance;
          const circle = L.circle([lat, lng], {
            radius: dist,
            color: bufferColors[dist] || '#059669',
            weight: isBufferActive ? 2.5 : 1.2,
            dashArray: isBufferActive ? undefined : '4, 4',
            fillColor: bufferColors[dist] || '#059669',
            fillOpacity: isBufferActive ? 0.15 : 0.05,
          });

          circle.bindTooltip(`Buffer: ${dist}m radius`, {
            permanent: false,
            direction: 'top',
          });

          bufferLayerRef.current?.addLayer(circle);
        });
      }
    });
  }, [interventions, selectedInterventionId, showBuffers, activeBufferDistance]);

  const handleFitAll = () => {
    if (!mapInstanceRef.current || interventions.length === 0) return;
    const validCoords = interventions
      .filter((i) => i.latitude && i.longitude)
      .map((i) => [i.latitude, i.longitude] as [number, number]);
    if (validCoords.length === 0) return;
    const bounds = L.latLngBounds(validCoords);
    mapInstanceRef.current.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 });
  };

  return (
    <div className={`relative w-full rounded-lg overflow-hidden border border-slate-200 dark:border-slate-800 shadow-sm transition-colors duration-200 ${className}`} style={{ height }}>
      {/* Map DOM Container */}
      <div ref={mapContainerRef} className="w-full h-full z-0" />

      {/* Basemap Switcher & Fit Controls */}
      <div className="absolute top-3 right-3 z-10 bg-white/95 dark:bg-slate-900/95 backdrop-blur rounded-md shadow-md border border-slate-200 dark:border-slate-700 p-1 flex items-center space-x-1 text-xs">
        <button
          onClick={handleFitAll}
          className="px-2 py-1 rounded font-semibold text-emerald-800 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/70 hover:bg-emerald-100 dark:hover:bg-emerald-900 border border-emerald-300 dark:border-emerald-800 transition-colors flex items-center space-x-1"
          title="Fit all markers in view"
        >
          <MapPin className="w-3 h-3" />
          <span>Fit All ({interventions.length})</span>
        </button>
        <span className="text-slate-300 dark:text-slate-700">|</span>
        <button
          onClick={() => setActiveBaseLayer('satellite')}
          className={`px-2.5 py-1 rounded font-medium transition-colors ${
            activeBaseLayer === 'satellite'
              ? 'bg-slate-800 dark:bg-emerald-700 text-white'
              : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          Satellite
        </button>
        <button
          onClick={() => setActiveBaseLayer('streets')}
          className={`px-2.5 py-1 rounded font-medium transition-colors ${
            activeBaseLayer === 'streets'
              ? 'bg-slate-800 dark:bg-emerald-700 text-white'
              : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          Streets
        </button>
        <button
          onClick={() => setActiveBaseLayer('topo')}
          className={`px-2.5 py-1 rounded font-medium transition-colors ${
            activeBaseLayer === 'topo'
              ? 'bg-slate-800 dark:bg-emerald-700 text-white'
              : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          Topo
        </button>
      </div>

      {/* Map Info Legend */}
      <div className="absolute bottom-3 left-3 z-10 bg-white/95 dark:bg-slate-900/95 backdrop-blur rounded-md shadow-md border border-slate-200 dark:border-slate-700 px-3 py-2 text-[11px] text-slate-700 dark:text-slate-300">
        <div className="font-semibold text-slate-800 dark:text-white mb-1 flex items-center space-x-1.5">
          <Compass className="w-3.5 h-3.5 text-emerald-700 dark:text-emerald-400" />
          <span>GIS Buffer Rings</span>
        </div>
        <div className="grid grid-cols-2 gap-x-3 gap-y-0.5">
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block"></span>
            <span>100m (Pond direct)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block"></span>
            <span>250m (Immediate)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block"></span>
            <span>500m (Catchment)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block"></span>
            <span>1000m (Watershed)</span>
          </div>
        </div>
      </div>
    </div>
  );
};
