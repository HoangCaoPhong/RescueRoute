import { useEffect, useMemo } from "react";
import L, { type LatLngExpression } from "leaflet";
import {
  CircleMarker,
  MapContainer,
  Polyline,
  Popup,
  TileLayer,
  useMap,
  useMapEvents,
} from "react-leaflet";
import type {
  AmbulanceLocation,
  PointOfInterest,
  RoadEdge,
  RouteResponse,
  SearchStep,
  SearchTrace,
} from "../../types/api";

interface RescueMapProps {
  ambulance: AmbulanceLocation | null;
  edges: RoadEdge[];
  hospitals: PointOfInterest[];
  route: RouteResponse | null;
  trace: SearchTrace | null;
  activeTraceStep: number;
  selectedHospitalId: number | null;
  showFacilities: boolean;
  showTraffic: boolean;
  isDark: boolean;
  onMapClick: (lat: number, lng: number) => void;
  onSelectHospital: (nodeId: number) => void;
  onToggleFacilities: () => void;
  onToggleTraffic: () => void;
}

function MapClickHandler({
  onMapClick,
}: Pick<RescueMapProps, "onMapClick">) {
  useMapEvents({
    click: ({ latlng }) => onMapClick(latlng.lat, latlng.lng),
  });
  return null;
}

function FitRoute({ coordinates }: { coordinates: [number, number][] }) {
  const map = useMap();

  useEffect(() => {
    if (coordinates.length < 2) return;
    map.fitBounds(L.latLngBounds(coordinates), { padding: [56, 56], maxZoom: 16 });
  }, [coordinates, map]);

  return null;
}

function TraceLayers({
  trace,
  stepIndex,
}: {
  trace: SearchTrace | null;
  stepIndex: number;
}) {
  if (!trace?.steps.length) return null;
  const safeIndex = Math.min(Math.max(stepIndex, 0), trace.steps.length - 1);
  const step: SearchStep = trace.steps[safeIndex];
  const visited = trace.visited_order.slice(0, safeIndex + 1).slice(-350);
  const frontier = step.frontier.slice(0, 100);
  const coordsFor = (nodeId: number | null) =>
    nodeId === null ? undefined : trace.node_coords[String(nodeId)];

  return (
    <>
      {visited.map((nodeId) => {
        const position = coordsFor(nodeId);
        return position ? (
          <CircleMarker
            key={`visited-${nodeId}`}
            center={position}
            radius={2.5}
            pathOptions={{ color: "#f9ab00", fillColor: "#f9ab00", fillOpacity: 0.62, weight: 0 }}
          />
        ) : null;
      })}
      {frontier.map(({ node_id: nodeId }, index) => {
        const position = coordsFor(nodeId);
        return position ? (
          <CircleMarker
            key={`frontier-${nodeId}-${index}`}
            center={position}
            radius={3.5}
            pathOptions={{ color: "#34a853", fillColor: "#ffffff", fillOpacity: 0.95, weight: 1.5 }}
          />
        ) : null;
      })}
      {coordsFor(step.current_node) ? (
        <CircleMarker
          center={coordsFor(step.current_node) as [number, number]}
          radius={7}
          pathOptions={{ color: "#ffffff", fillColor: "#1a73e8", fillOpacity: 1, weight: 3 }}
        />
      ) : null}
    </>
  );
}

export function RescueMap({
  ambulance,
  edges,
  hospitals,
  route,
  trace,
  activeTraceStep,
  selectedHospitalId,
  showFacilities,
  showTraffic,
  isDark,
  onMapClick,
  onSelectHospital,
  onToggleFacilities,
  onToggleTraffic,
}: RescueMapProps) {
  const freeFlowRoads = useMemo<LatLngExpression[][]>(
    () =>
      edges
        .filter((edge) => edge.congestion_level <= 2)
        .map((edge) => [
          [edge.u_lat, edge.u_lng],
          [edge.v_lat, edge.v_lng],
        ]),
    [edges],
  );
  const moderateRoads = useMemo<LatLngExpression[][]>(
    () =>
      edges
        .filter((edge) => edge.congestion_level === 3)
        .map((edge) => [
          [edge.u_lat, edge.u_lng],
          [edge.v_lat, edge.v_lng],
        ]),
    [edges],
  );
  const heavyRoads = useMemo<LatLngExpression[][]>(
    () =>
      edges
        .filter((edge) => edge.congestion_level >= 4)
        .map((edge) => [
          [edge.u_lat, edge.u_lng],
          [edge.v_lat, edge.v_lng],
        ]),
    [edges],
  );
  const routeCoordinates = route?.path_coords ?? [];

  return (
    <section className="relative h-full min-h-[520px] overflow-hidden bg-slate-100 dark:bg-slate-900" aria-label="Bản đồ điều phối">
      <MapContainer
        center={[10.778, 106.692]}
        zoom={13}
        zoomControl
        renderer={L.canvas({ padding: 0.5 })}
        className="h-full w-full"
      >
        <TileLayer
          key={isDark ? "dark" : "light"}
          attribution="&copy; OpenStreetMap &copy; CARTO"
          url={
            isDark
              ? "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              : "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          }
          maxZoom={19}
        />
        <MapClickHandler onMapClick={onMapClick} />
        <FitRoute coordinates={routeCoordinates} />

        {showTraffic && freeFlowRoads.length > 0 ? (
          <Polyline
            positions={freeFlowRoads}
            pathOptions={{ color: "#34a853", opacity: isDark ? 0.55 : 0.42, weight: 1.4 }}
          />
        ) : null}
        {showTraffic && moderateRoads.length > 0 ? (
          <Polyline
            positions={moderateRoads}
            pathOptions={{ color: "#f9ab00", opacity: 0.78, weight: 1.9 }}
          />
        ) : null}
        {showTraffic && heavyRoads.length > 0 ? (
          <Polyline
            positions={heavyRoads}
            pathOptions={{ color: "#ea4335", opacity: 0.84, weight: 2.3 }}
          />
        ) : null}

        {showFacilities
          ? hospitals.map((hospital) => {
              const selected = hospital.node_id === selectedHospitalId;
              return (
                <CircleMarker
                  key={`hospital-${hospital.node_id}`}
                  center={[hospital.lat, hospital.lng]}
                  radius={selected ? 7 : hospital.is_emergency ? 4.5 : 3.5}
                  eventHandlers={{ click: () => onSelectHospital(hospital.node_id) }}
                  pathOptions={{
                    color: selected ? "#ffffff" : "#b3261e",
                    fillColor: "#ea4335",
                    fillOpacity: hospital.is_emergency ? 0.94 : 0.62,
                    weight: selected ? 3 : 1.2,
                  }}
                >
                  <Popup>
                    <strong>{hospital.name || "Cơ sở y tế"}</strong>
                    <br />
                    {hospital.category || hospital.type || "Cơ sở y tế"}
                  </Popup>
                </CircleMarker>
              );
            })
          : null}

        {routeCoordinates.length > 1 ? (
          <>
            <Polyline positions={routeCoordinates} pathOptions={{ color: "#ffffff", opacity: 0.9, weight: 8 }} />
            <Polyline positions={routeCoordinates} pathOptions={{ color: "#1a73e8", opacity: 1, weight: 4.5 }} />
          </>
        ) : null}

        <TraceLayers trace={trace} stepIndex={activeTraceStep} />

        {ambulance ? (
          <CircleMarker
            center={[ambulance.lat, ambulance.lng]}
            radius={8}
            pathOptions={{ color: "#ffffff", fillColor: "#1a73e8", fillOpacity: 1, weight: 4 }}
          >
            <Popup>
              <strong>Vị trí xe cấp cứu</strong>
              <br />
              Nhấp bản đồ để cập nhật điểm xuất phát.
            </Popup>
          </CircleMarker>
        ) : null}
      </MapContainer>

      <div className="absolute bottom-6 left-5 z-[500] flex gap-2 rounded-xl border border-slate-200 bg-white/95 p-1.5 shadow-panel backdrop-blur dark:border-slate-700 dark:bg-slate-950/95">
        <button
          type="button"
          className={showTraffic ? "map-filter-active" : "map-filter"}
          onClick={onToggleTraffic}
          aria-pressed={showTraffic}
        >
          Mạng đường
        </button>
        <button
          type="button"
          className={showFacilities ? "map-filter-active" : "map-filter"}
          onClick={onToggleFacilities}
          aria-pressed={showFacilities}
        >
          Cơ sở y tế
        </button>
      </div>

      <div className="absolute right-5 top-5 z-[500] hidden w-48 rounded-xl border border-slate-200 bg-white/95 px-4 py-3 text-xs shadow-panel backdrop-blur md:block dark:border-slate-700 dark:bg-slate-950/95">
        <p className="font-semibold text-slate-900 dark:text-white">Chú thích</p>
        <div className="mt-3 space-y-2 text-slate-600 dark:text-slate-300">
          <p className="flex items-center gap-2"><span className="h-0.5 w-5 bg-route-600" /> Tuyến đề xuất</p>
          <p className="flex items-center gap-2"><span className="h-0.5 w-5 bg-traffic-green" /> Thông thoáng</p>
          <p className="flex items-center gap-2"><span className="h-0.5 w-5 bg-traffic-amber" /> Di chuyển chậm</p>
          <p className="flex items-center gap-2"><span className="h-0.5 w-5 bg-traffic-red" /> Ùn tắc nặng</p>
          <p className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-traffic-red" /> Cơ sở y tế</p>
          <p className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-route-600" /> Xe cấp cứu</p>
        </div>
      </div>
    </section>
  );
}
