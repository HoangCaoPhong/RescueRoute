import { useEffect, useMemo, useState } from "react";
import { AppHeader } from "../components/AppHeader";
import { RescueMap } from "../features/map/RescueMap";
import {
  RoutePlanner,
  type PlannerInput,
} from "../features/route-planner/RoutePlanner";
import { aggregateRouteSegments } from "../features/route-planner/routeUtils";
import { useTheme } from "../hooks/useTheme";
import {
  calculateDirectRoute,
  calculateOptimizedRoute,
  getDashboardData,
  updateAmbulanceLocation,
} from "../lib/api/client";
import type {
  AmbulanceLocation,
  HealthStatus,
  PointOfInterest,
  RoadEdge,
  RouteResponse,
  RouteSegment,
} from "../types/api";

function distanceBetween(
  origin: AmbulanceLocation,
  destination: PointOfInterest,
) {
  const toRadians = (value: number) => (value * Math.PI) / 180;
  const earthRadiusMetres = 6_371_000;
  const latitudeDelta = toRadians(destination.lat - origin.lat);
  const longitudeDelta = toRadians(destination.lng - origin.lng);
  const startLatitude = toRadians(origin.lat);
  const endLatitude = toRadians(destination.lat);
  const haversine =
    Math.sin(latitudeDelta / 2) ** 2 +
    Math.cos(startLatitude) *
      Math.cos(endLatitude) *
      Math.sin(longitudeDelta / 2) ** 2;
  return earthRadiusMetres * 2 * Math.atan2(Math.sqrt(haversine), Math.sqrt(1 - haversine));
}

export function DashboardPage() {
  const { isDark, toggleTheme } = useTheme();
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [points, setPoints] = useState<PointOfInterest[]>([]);
  const [edges, setEdges] = useState<RoadEdge[]>([]);
  const [ambulance, setAmbulance] = useState<AmbulanceLocation | null>(null);
  const [selectedHospitalId, setSelectedHospitalId] = useState<number | null>(null);
  const [waypointIds, setWaypointIds] = useState<number[]>([]);
  const [route, setRoute] = useState<RouteResponse | null>(null);
  const [activeTraceStep, setActiveTraceStep] = useState(0);
  const [isLoadingData, setIsLoadingData] = useState(true);
  const [isCalculating, setIsCalculating] = useState(false);
  const [locationBusy, setLocationBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [plannerOpen, setPlannerOpen] = useState(false);
  const [showFacilities, setShowFacilities] = useState(true);
  const [showTraffic, setShowTraffic] = useState(true);

  const hospitals = useMemo(
    () => points.filter((item) => item.is_hospital),
    [points],
  );

  useEffect(() => {
    let mounted = true;
    getDashboardData()
      .then((data) => {
        if (!mounted) return;
        setHealth(data.health);
        setPoints(data.points);
        setEdges(data.edges);
        setAmbulance(data.ambulance);
      })
      .catch((requestError: unknown) => {
        if (mounted) {
          setError(requestError instanceof Error ? requestError.message : "Không thể tải dữ liệu bản đồ.");
        }
      })
      .finally(() => {
        if (mounted) setIsLoadingData(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  async function changeAmbulanceLocation(lat: number, lng: number) {
    setLocationBusy(true);
    setError(null);
    try {
      const location = await updateAmbulanceLocation(lat, lng);
      setAmbulance(location);
      setRoute(null);
      setActiveTraceStep(0);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Không thể cập nhật vị trí xe.");
    } finally {
      setLocationBusy(false);
    }
  }

  function useDeviceLocation() {
    if (!navigator.geolocation) {
      setError("Trình duyệt này không hỗ trợ định vị thiết bị.");
      return;
    }
    setLocationBusy(true);
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => void changeAmbulanceLocation(coords.latitude, coords.longitude),
      () => {
        setLocationBusy(false);
        setError("Không thể lấy vị trí. Hãy cấp quyền định vị hoặc chọn trực tiếp trên bản đồ.");
      },
      { enableHighAccuracy: true, timeout: 10_000, maximumAge: 30_000 },
    );
  }

  function selectNearestHospital() {
    if (!ambulance) return;
    const candidates = hospitals.filter((hospital) => hospital.is_emergency);
    const nearest = candidates.reduce<PointOfInterest | null>((best, hospital) => {
      if (!best) return hospital;
      return distanceBetween(ambulance, hospital) < distanceBetween(ambulance, best)
        ? hospital
        : best;
    }, null);
    if (nearest) selectHospital(nearest.node_id);
  }

  function selectHospital(nodeId: number) {
    setSelectedHospitalId(nodeId);
    setWaypointIds((current) => current.filter((item) => item !== nodeId));
  }

  async function calculateRoute(input: PlannerInput) {
    const startNodeId = ambulance?.mapped_nearest_node.nearest_node_id;
    const goalNodeId = selectedHospitalId;
    if (!startNodeId || !goalNodeId) {
      setError("Hãy xác định điểm xuất phát và chọn cơ sở y tế đích.");
      return;
    }

    setIsCalculating(true);
    setError(null);
    setActiveTraceStep(0);

    try {
      let response: RouteResponse;
      if (!waypointIds.length) {
        response = await calculateDirectRoute(startNodeId, goalNodeId, input.algorithm);
      } else if (input.optimizationMethod !== "input" && waypointIds.length > 1) {
        response = await calculateOptimizedRoute({
          startNodeId,
          waypointIds,
          goalNodeId,
          algorithm: input.algorithm,
          method: input.optimizationMethod,
          criterion: input.criterion,
        });
      } else {
        const visitingOrder = [startNodeId, ...waypointIds, goalNodeId];
        const segments: RouteSegment[] = [];
        for (let index = 0; index < visitingOrder.length - 1; index += 1) {
          const result = await calculateDirectRoute(
            visitingOrder[index],
            visitingOrder[index + 1],
            input.algorithm,
          );
          if (!result.found) {
            throw new Error(result.message || `Không tìm thấy tuyến cho chặng ${index + 1}.`);
          }
          segments.push({
            start: visitingOrder[index],
            goal: visitingOrder[index + 1],
            result,
          });
        }
        response = aggregateRouteSegments(segments, visitingOrder);
      }

      if (!response.found) throw new Error(response.message || "Không tìm thấy tuyến phù hợp.");
      setRoute(response);
      setPlannerOpen(false);
    } catch (requestError) {
      setRoute(null);
      setError(requestError instanceof Error ? requestError.message : "Không thể tính tuyến đường.");
    } finally {
      setIsCalculating(false);
    }
  }

  return (
    <div className="flex h-dvh min-h-[640px] flex-col bg-slate-50 text-slate-950 dark:bg-slate-950 dark:text-slate-100">
      <AppHeader isDark={isDark} onToggleTheme={toggleTheme} onOpenPlanner={() => setPlannerOpen(true)} />

      <main className="relative min-h-0 flex-1 lg:grid lg:grid-cols-[400px_minmax(0,1fr)]">
        <div
          className={`absolute inset-y-0 left-0 z-[700] w-[min(92vw,400px)] border-r border-slate-200 shadow-panel transition-transform duration-200 lg:static lg:z-auto lg:w-auto lg:translate-x-0 lg:shadow-none dark:border-slate-800 ${
            plannerOpen ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          <RoutePlanner
            health={health}
            ambulance={ambulance}
            hospitals={hospitals}
            selectedHospitalId={selectedHospitalId}
            waypointIds={waypointIds}
            route={route}
            trace={route?.search_trace ?? null}
            activeTraceStep={activeTraceStep}
            isLoadingData={isLoadingData}
            isCalculating={isCalculating}
            locationBusy={locationBusy}
            error={error}
            onClose={() => setPlannerOpen(false)}
            onSelectHospital={selectHospital}
            onSelectNearest={selectNearestHospital}
            onAddWaypoint={(nodeId) => setWaypointIds((current) => [...current, nodeId].slice(0, 5))}
            onRemoveWaypoint={(nodeId) => setWaypointIds((current) => current.filter((item) => item !== nodeId))}
            onUseDeviceLocation={useDeviceLocation}
            onCalculate={(input) => void calculateRoute(input)}
            onTraceStepChange={setActiveTraceStep}
          />
        </div>

        {plannerOpen ? (
          <button
            type="button"
            className="absolute inset-0 z-[650] bg-slate-950/25 lg:hidden"
            onClick={() => setPlannerOpen(false)}
            aria-label="Đóng bảng lập tuyến"
          />
        ) : null}

        <RescueMap
          ambulance={ambulance}
          edges={edges}
          hospitals={hospitals}
          route={route}
          trace={route?.search_trace ?? null}
          activeTraceStep={activeTraceStep}
          selectedHospitalId={selectedHospitalId}
          showFacilities={showFacilities}
          showTraffic={showTraffic}
          isDark={isDark}
          onMapClick={(lat, lng) => void changeAmbulanceLocation(lat, lng)}
          onSelectHospital={selectHospital}
          onToggleFacilities={() => setShowFacilities((current) => !current)}
          onToggleTraffic={() => setShowTraffic((current) => !current)}
        />

        {isLoadingData ? (
          <div className="pointer-events-none absolute inset-0 z-[600] flex items-center justify-center bg-white/70 text-sm font-medium text-slate-700 backdrop-blur-sm lg:left-[400px] dark:bg-slate-950/70 dark:text-slate-200">
            Đang tải mạng lưới giao thông…
          </div>
        ) : null}
      </main>
    </div>
  );
}
