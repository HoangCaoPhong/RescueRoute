import { useMemo, useState } from "react";
import type {
  Algorithm,
  AmbulanceLocation,
  Criterion,
  HealthStatus,
  OptimizationMethod,
  PointOfInterest,
  RouteResponse,
  SearchTrace,
} from "../../types/api";
import { SearchPlayback } from "../search-visualizer/SearchPlayback";
import { formatDistance, formatDuration } from "./routeUtils";

export interface PlannerInput {
  algorithm: Algorithm;
  criterion: Criterion;
  optimizationMethod: OptimizationMethod;
}

interface RoutePlannerProps {
  health: HealthStatus | null;
  ambulance: AmbulanceLocation | null;
  hospitals: PointOfInterest[];
  selectedHospitalId: number | null;
  waypointIds: number[];
  route: RouteResponse | null;
  trace: SearchTrace | null;
  activeTraceStep: number;
  isLoadingData: boolean;
  isCalculating: boolean;
  locationBusy: boolean;
  error: string | null;
  onClose: () => void;
  onSelectHospital: (nodeId: number) => void;
  onSelectNearest: () => void;
  onAddWaypoint: (nodeId: number) => void;
  onRemoveWaypoint: (nodeId: number) => void;
  onUseDeviceLocation: () => void;
  onCalculate: (input: PlannerInput) => void;
  onTraceStepChange: (step: number) => void;
}

const algorithms: { value: Algorithm; label: string; note: string }[] = [
  { value: "astar", label: "A* Search", note: "Cân bằng tốc độ và chất lượng tuyến" },
  { value: "ucs", label: "Uniform Cost Search", note: "Tối ưu chi phí tổng hợp" },
  { value: "dijkstra", label: "Dijkstra", note: "Tối ưu quãng đường" },
  { value: "bfs", label: "Breadth-First Search", note: "Ít chặng nhất" },
  { value: "dfs", label: "Depth-First Search", note: "Minh họa duyệt sâu" },
  { value: "hill_climbing", label: "Hill Climbing", note: "Xấp xỉ theo heuristic" },
];

function normalize(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

export function RoutePlanner({
  health,
  ambulance,
  hospitals,
  selectedHospitalId,
  waypointIds,
  route,
  trace,
  activeTraceStep,
  isLoadingData,
  isCalculating,
  locationBusy,
  error,
  onClose,
  onSelectHospital,
  onSelectNearest,
  onAddWaypoint,
  onRemoveWaypoint,
  onUseDeviceLocation,
  onCalculate,
  onTraceStepChange,
}: RoutePlannerProps) {
  const [query, setQuery] = useState("");
  const [emergencyOnly, setEmergencyOnly] = useState(true);
  const [algorithm, setAlgorithm] = useState<Algorithm>("astar");
  const [criterion, setCriterion] = useState<Criterion>("cost");
  const [optimizationMethod, setOptimizationMethod] = useState<OptimizationMethod>("input");
  const [waypointCandidate, setWaypointCandidate] = useState<number | null>(null);

  const visibleHospitals = useMemo(() => {
    const normalizedQuery = normalize(query.trim());
    return hospitals
      .filter((hospital) => !emergencyOnly || hospital.is_emergency)
      .filter((hospital) => !normalizedQuery || normalize(hospital.name || "").includes(normalizedQuery))
      .sort((left, right) => (left.name || "").localeCompare(right.name || "", "vi"))
      .slice(0, 500);
  }, [emergencyOnly, hospitals, query]);

  const selectedHospital = hospitals.find((item) => item.node_id === selectedHospitalId);
  const selectedAlgorithm = algorithms.find((item) => item.value === algorithm);
  const dataStatus = isLoadingData
    ? "Đang tải"
    : health?.status === "ok"
      ? "Sẵn sàng"
      : "Chưa kết nối";
  const dataStatusClass = isLoadingData
    ? "bg-traffic-amber/10 text-[#8a5a00] dark:text-[#fdd663]"
    : health?.status === "ok"
      ? "bg-traffic-green/10 text-[#188038] dark:text-[#81c995]"
      : "bg-traffic-red/10 text-[#b3261e] dark:text-[#f28b82]";
  const dataDotClass = isLoadingData
    ? "bg-traffic-amber"
    : health?.status === "ok"
      ? "bg-traffic-green"
      : "bg-traffic-red";
  const waypointOptions = visibleHospitals.filter(
    (item) => item.node_id !== selectedHospitalId && !waypointIds.includes(item.node_id),
  );

  return (
    <aside className="h-full overflow-y-auto bg-white px-6 pb-10 pt-6 dark:bg-slate-950" aria-label="Bảng lập tuyến">
      <div className="flex items-start justify-between gap-5">
        <div>
          <p className="eyebrow">Điều phối</p>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
            Lập tuyến cấp cứu
          </h1>
          <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
            Chọn điểm đến và phương pháp tìm kiếm. Nhấp trực tiếp lên bản đồ để đổi vị trí xe.
          </p>
        </div>
        <button
          type="button"
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-slate-200 text-xl text-slate-600 lg:hidden dark:border-slate-700 dark:text-slate-300"
          onClick={onClose}
          aria-label="Đóng bảng lập tuyến"
        >
          ×
        </button>
      </div>

      <section className="mt-7 rounded-xl border border-route-100 bg-route-50/45 p-4 dark:border-slate-800 dark:bg-route-600/10" aria-labelledby="data-heading">
        <div className="flex items-center justify-between gap-3">
          <h2 id="data-heading" className="text-sm font-semibold text-slate-900 dark:text-white">Dữ liệu bản đồ</h2>
          <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${dataStatusClass}`}>
            <span className={`h-1.5 w-1.5 rounded-full ${dataDotClass}`} aria-hidden="true" />
            {dataStatus}
          </span>
        </div>
        <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-3">
          <div>
            <dt className="metric-label">Nút giao thông</dt>
            <dd className="metric-value">{health?.nodes_count.toLocaleString("vi-VN") ?? "—"}</dd>
          </div>
          <div>
            <dt className="metric-label">Cạnh có hướng</dt>
            <dd className="metric-value">{health?.edges_count.toLocaleString("vi-VN") ?? "—"}</dd>
          </div>
        </dl>
      </section>

      <section className="planner-section" aria-labelledby="origin-heading">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="section-number">01</p>
            <h2 id="origin-heading" className="section-title">Điểm xuất phát</h2>
          </div>
          <button type="button" className="text-button" onClick={onUseDeviceLocation} disabled={locationBusy}>
            {locationBusy ? "Đang định vị" : "Dùng vị trí thiết bị"}
          </button>
        </div>
        <div className="mt-4 rounded-xl border-l-2 border-route-600 bg-route-50/70 p-4 dark:bg-route-600/10">
          <p className="text-sm font-medium text-slate-900 dark:text-white">
            {ambulance?.mapped_nearest_node.nearest_node_name || "Chưa xác định node gần nhất"}
          </p>
          <p className="mt-1 font-mono text-xs text-slate-500 dark:text-slate-400">
            {ambulance ? `${ambulance.lat.toFixed(5)}, ${ambulance.lng.toFixed(5)}` : "Đang tải tọa độ"}
          </p>
        </div>
      </section>

      <section className="planner-section" aria-labelledby="destination-heading">
        <div className="flex items-end justify-between gap-3">
          <div>
            <p className="section-number">02</p>
            <h2 id="destination-heading" className="section-title">Điểm đến</h2>
          </div>
          <button type="button" className="text-button" onClick={onSelectNearest} disabled={!hospitals.length}>
            Chọn gần nhất
          </button>
        </div>

        <label className="field-label mt-4" htmlFor="hospital-search">Tìm cơ sở y tế</label>
        <input
          id="hospital-search"
          className="field"
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Tên bệnh viện hoặc cơ sở y tế"
        />

        <div className="mt-3 flex gap-2" role="group" aria-label="Bộ lọc cơ sở y tế">
          <button
            type="button"
            className={emergencyOnly ? "segmented-active" : "segmented"}
            onClick={() => setEmergencyOnly(true)}
          >
            Có cấp cứu
          </button>
          <button
            type="button"
            className={!emergencyOnly ? "segmented-active" : "segmented"}
            onClick={() => setEmergencyOnly(false)}
          >
            Tất cả
          </button>
        </div>

        <label className="field-label mt-4" htmlFor="hospital-select">Cơ sở được chọn</label>
        <select
          id="hospital-select"
          className="field"
          value={selectedHospitalId ?? ""}
          onChange={(event) => onSelectHospital(Number(event.target.value))}
          disabled={!visibleHospitals.length}
        >
          <option value="">Chọn điểm đến</option>
          {visibleHospitals.map((hospital) => (
            <option key={hospital.node_id} value={hospital.node_id}>
              {hospital.name || `Cơ sở #${hospital.node_id}`}
            </option>
          ))}
        </select>
        {selectedHospital ? (
          <p className="mt-3 rounded-lg border-l-2 border-traffic-red bg-red-50 px-3 py-2 text-xs leading-5 text-slate-600 dark:bg-red-950/20 dark:text-slate-300">
            {selectedHospital.category || selectedHospital.type || "Cơ sở y tế"}
          </p>
        ) : null}
      </section>

      <details className="planner-section group">
        <summary className="cursor-pointer list-none text-sm font-semibold text-slate-900 dark:text-white">
          Điểm ghé trung gian <span className="font-normal text-slate-500">({waypointIds.length}/5)</span>
        </summary>
        <div className="mt-4">
          <div className="flex gap-2">
            <select
              className="field min-w-0"
              value={waypointCandidate ?? ""}
              onChange={(event) => setWaypointCandidate(Number(event.target.value) || null)}
              aria-label="Chọn điểm ghé"
            >
              <option value="">Chọn cơ sở</option>
              {waypointOptions.map((hospital) => (
                <option key={hospital.node_id} value={hospital.node_id}>{hospital.name}</option>
              ))}
            </select>
            <button
              type="button"
              className="btn-secondary shrink-0"
              disabled={!waypointCandidate || waypointIds.length >= 5}
              onClick={() => {
                if (waypointCandidate) onAddWaypoint(waypointCandidate);
                setWaypointCandidate(null);
              }}
            >
              Thêm
            </button>
          </div>
          <div className="mt-3 space-y-2">
            {waypointIds.map((nodeId, index) => (
              <div key={nodeId} className="flex items-center justify-between gap-3 rounded-lg border-l-2 border-traffic-amber bg-amber-50/70 px-3 py-2 text-sm dark:bg-amber-950/15">
                <span className="min-w-0 truncate text-slate-700 dark:text-slate-300">
                  {index + 1}. {hospitals.find((item) => item.node_id === nodeId)?.name || `Node ${nodeId}`}
                </span>
                <button type="button" className="text-button" onClick={() => onRemoveWaypoint(nodeId)}>Xóa</button>
              </div>
            ))}
            {!waypointIds.length ? <p className="text-xs text-slate-500">Không bắt buộc. Tối đa 5 điểm ghé.</p> : null}
          </div>
        </div>
      </details>

      <section className="planner-section" aria-labelledby="method-heading">
        <p className="section-number">03</p>
        <h2 id="method-heading" className="section-title">Phương pháp tìm kiếm</h2>

        <label className="field-label mt-4" htmlFor="algorithm-select">Thuật toán</label>
        <select id="algorithm-select" className="field" value={algorithm} onChange={(event) => setAlgorithm(event.target.value as Algorithm)}>
          {algorithms.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
        </select>
        <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">{selectedAlgorithm?.note}</p>

        <div className="mt-4 grid grid-cols-2 gap-3">
          <div>
            <label className="field-label" htmlFor="criterion-select">Tiêu chí</label>
            <select id="criterion-select" className="field" value={criterion} onChange={(event) => setCriterion(event.target.value as Criterion)}>
              <option value="cost">Chi phí</option>
              <option value="time">Thời gian</option>
              <option value="distance">Khoảng cách</option>
              <option value="hops">Số chặng</option>
            </select>
          </div>
          <div>
            <label className="field-label" htmlFor="optimization-select">Thứ tự điểm ghé</label>
            <select
              id="optimization-select"
              className="field"
              value={optimizationMethod}
              onChange={(event) => setOptimizationMethod(event.target.value as OptimizationMethod)}
              disabled={waypointIds.length < 2}
            >
              <option value="input">Giữ thứ tự</option>
              <option value="nearest_neighbor">Nearest Neighbor</option>
              <option value="held_karp">Held–Karp</option>
              <option value="genetic_algorithm">Genetic Algorithm</option>
              <option value="simulated_annealing">Simulated Annealing</option>
            </select>
          </div>
        </div>

        {error ? <p className="mt-4 rounded-lg border-l-2 border-traffic-red bg-red-50 px-3 py-2 text-sm text-red-800 dark:bg-red-950/20 dark:text-red-200" role="alert">{error}</p> : null}

        <button
          type="button"
          className="btn-primary mt-5 w-full justify-center"
          disabled={isCalculating || !selectedHospitalId || !ambulance?.mapped_nearest_node.nearest_node_id}
          onClick={() => onCalculate({ algorithm, criterion, optimizationMethod })}
        >
          {isCalculating ? "Đang tính tuyến" : "Tìm tuyến phù hợp"}
        </button>
      </section>

      {route?.found ? (
        <section className="mt-7 rounded-xl border border-green-200 bg-green-50/65 p-5 dark:border-green-900/70 dark:bg-green-950/20" aria-labelledby="result-heading">
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#188038] dark:text-[#81c995]">Kết quả</p>
          <h2 id="result-heading" className="mt-1 text-lg font-semibold text-slate-950 dark:text-white">
            Tuyến đã sẵn sàng
          </h2>
          <dl className="mt-4 grid grid-cols-2 gap-4">
            <div>
              <dt className="metric-label">Quãng đường</dt>
              <dd className="metric-value">{formatDistance(route.total_distance_m)}</dd>
            </div>
            <div>
              <dt className="metric-label">Thời gian dự kiến</dt>
              <dd className="metric-value">{formatDuration(route.total_distance_m)}</dd>
            </div>
            <div>
              <dt className="metric-label">Node đã mở rộng</dt>
              <dd className="metric-value">{(route.nodes_expanded ?? 0).toLocaleString("vi-VN")}</dd>
            </div>
            <div>
              <dt className="metric-label">Thời gian xử lý</dt>
              <dd className="metric-value">{(route.execution_time_ms ?? 0).toFixed(1)} ms</dd>
            </div>
          </dl>
          <p className="mt-4 text-xs leading-5 text-slate-500 dark:text-slate-400">
            {route.path_nodes?.length ?? 0} node trên tuyến · cost {(route.total_cost ?? 0).toFixed(2)}
          </p>
        </section>
      ) : null}

      <SearchPlayback trace={trace} activeStep={activeTraceStep} onStepChange={onTraceStepChange} />
    </aside>
  );
}
