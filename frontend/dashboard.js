const API_BASE = "/api";
const MAX_WAYPOINTS = 5;
const DEFAULT_SPEED_KPH = 30;
const MAX_MAP_TRACE_NODES = 1000;
const MAX_TRACE_TOKENS = 192;
const SEARCH_COLORS = {
    visited: "#facc15",
    current: "#f97316",
    frontier: "#38bdf8",
    route: "#9e77ff",
};

const ALGORITHM_SPECS = {
    astar: {
        label: "A* Search",
        objective: "chi phí giao thông tổng hợp với heuristic Haversine",
        compatibleCriteria: ["cost", "time"],
        optimality: "Có điều kiện",
        badgeClass: "neutral",
        explanation:
            "A* ưu tiên tổng chi phí đã đi và ước lượng Haversine tới đích. Tính tối ưu chỉ được bảo đảm khi heuristic là admissible và consistent với cost.",
    },
    ucs: {
        label: "Uniform Cost Search",
        objective: "chi phí giao thông tổng hợp",
        compatibleCriteria: ["cost", "time"],
        optimality: "Tối ưu theo cost",
        badgeClass: "success",
        explanation:
            "UCS luôn mở đường đi có tổng cost nhỏ nhất trước và tối ưu khi mọi chi phí cạnh không âm.",
    },
    dijkstra: {
        label: "Dijkstra",
        objective: "tổng quãng đường",
        compatibleCriteria: ["distance"],
        optimality: "Tối ưu khoảng cách",
        badgeClass: "success",
        explanation:
            "Dijkstra trong backend hiện dùng độ dài cạnh, vì vậy tối ưu tổng quãng đường khi mọi độ dài không âm.",
    },
    bfs: {
        label: "Breadth-First Search",
        objective: "số cạnh / số chặng",
        compatibleCriteria: ["hops"],
        optimality: "Tối ưu số chặng",
        badgeClass: "success",
        explanation:
            "BFS duyệt theo từng lớp và tìm đường có ít cạnh nhất trên đồ thị không trọng số; đường đó không nhất thiết ngắn nhất theo khoảng cách hay cost.",
    },
    dfs: {
        label: "Depth-First Search",
        objective: "thứ tự duyệt sâu",
        compatibleCriteria: [],
        optimality: "Không bảo đảm",
        badgeClass: "warning",
        explanation:
            "DFS đi sâu theo một nhánh trước. Thuật toán phù hợp để minh họa hành vi tìm kiếm nhưng không bảo đảm route tối ưu.",
    },
    hill_climbing: {
        label: "Hill Climbing",
        objective: "heuristic Haversine cục bộ",
        compatibleCriteria: [],
        optimality: "Xấp xỉ cục bộ",
        badgeClass: "warning",
        explanation:
            "Hill Climbing luôn chọn ứng viên có heuristic tốt nhất tại bước hiện tại; thuật toán nhanh nhưng có thể kẹt ở cực trị cục bộ và không bảo đảm tìm được route.",
    },
};

const CRITERION_LABELS = {
    cost: "Chi phí giao thông tổng hợp",
    time: "Thời gian di chuyển ước tính",
    distance: "Tổng quãng đường",
    hops: "Số chặng đường",
};

let map;
let hospitalsData = [];
let poisData = [];
let selectedWaypoints = [];
let edgesData = [];
let edgeIndex = new Map();
let graphEdgeCount = 0;
let fullRoadNodeCoords = new Map();
let fullCoordinateLoadPromise = null;
let allEdgeCoordinatesLoaded = false;
let currentAmbulanceData = {
    lat: 10.773,
    lng: 106.698,
    mapped_nearest_node: {},
};
let ambulanceMarker = null;
let hospitalMarkers = new Map();
let showPOIIcons = true;
let showTraffic = true;
let edgePolylines = {};
let activeRoutePolyline = null;
let backgroundRoutePolyline = null;
let routeNodeMarkers = [];
let routeRequestCache = new Map();
let toastTimer = null;

let searchVisualizationData = null;
let searchStepIndex = 0;
let searchAnimationTimer = null;
let searchVisitedLayer = null;
let searchFrontierLayer = null;
let searchCurrentLayer = null;

// Mỗi lần mở dashboard đều bắt đầu ở giao diện sáng; nút vẫn đổi theme trong phiên hiện tại.
let currentTheme = "light";

function applyTheme(theme) {
    currentTheme = theme === "light" ? "light" : "dark";
    if (typeof document !== "undefined") {
        if (document.documentElement && typeof document.documentElement.setAttribute === "function") {
            document.documentElement.setAttribute("data-theme", currentTheme);
        }
        if (document.body && typeof document.body.setAttribute === "function") {
            document.body.setAttribute("data-theme", currentTheme);
        }
    }
    const btn = byId("themeToggleBtn");
    if (btn) {
        const icon = btn.querySelector(".theme-icon");
        const label = btn.querySelector(".theme-label");
        if (currentTheme === "light") {
            if (icon) icon.textContent = "☀️";
            if (label) label.textContent = "Sáng";
            btn.setAttribute("title", "Đang ở chế độ Sáng. Nhấp để chuyển sang Tối");
            btn.setAttribute("aria-label", "Chuyển sang chế độ Tối");
        } else {
            if (icon) icon.textContent = "🌙";
            if (label) label.textContent = "Tối";
            btn.setAttribute("title", "Đang ở chế độ Tối. Nhấp để chuyển sang Sáng");
            btn.setAttribute("aria-label", "Chuyển sang chế độ Sáng");
        }
    }
}

function toggleTheme() {
    const nextTheme = currentTheme === "dark" ? "light" : "dark";
    applyTheme(nextTheme);
}

function byId(id) {
    return document.getElementById(id);
}

function setText(id, value) {
    const element = byId(id);
    if (element) element.textContent = value;
}

try {
    applyTheme(currentTheme);
} catch (e) {}

function mountSearchPlaybackDock() {
    const dock = byId("searchPlaybackDock");
    const toolbar = byId("searchVisualizationPanel")?.querySelector(
        ".search-viz-toolbar",
    );
    if (!dock || !toolbar || toolbar.parentElement === dock) return;
    dock.append(toolbar);
}

function setSidebarCollapsed(isCollapsed) {
    const workspace = byId("workspace");
    const sidebar = byId("sidebarPanel");
    const button = byId("btnToggleSidebar");
    const icon = byId("sidebarToggleIcon");
    if (!workspace || !sidebar || !button || !icon) return;

    workspace.classList.toggle("is-sidebar-collapsed", isCollapsed);
    sidebar.classList.toggle("is-collapsed", isCollapsed);
    icon.textContent = isCollapsed ? "›" : "‹";

    const label = isCollapsed
        ? "Mở bảng điều khiển"
        : "Thu gọn bảng điều khiển";
    button.setAttribute("aria-expanded", String(!isCollapsed));
    button.setAttribute("aria-label", label);
    button.title = label;

    if (map) {
        window.setTimeout(() => map.invalidateSize({ animate: true }), 280);
    }
}

function toggleSidebar() {
    const sidebar = byId("sidebarPanel");
    if (!sidebar) return;
    setSidebarCollapsed(!sidebar.classList.contains("is-collapsed"));
}

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

async function fetchJson(url, options = {}) {
    const response = await fetch(url, options);
    const contentType = response.headers.get("content-type") || "";
    const data = contentType.includes("application/json")
        ? await response.json()
        : { detail: await response.text() };

    if (!response.ok) {
        let detail =
            typeof data?.detail === "string"
                ? data.detail
                : JSON.stringify(data?.detail || "");
        if (detail.includes("<html") || detail.includes("<!DOCTYPE") || detail.includes("<title>")) {
            detail = `HTTP ${response.status} (${response.statusText || "Lỗi Gateway / Máy chủ"})`;
        }
        throw new Error(detail || data?.message || `HTTP ${response.status}`);
    }
    return data;
}


function setOperationStatus(message = "", isError = false) {
    const status = byId("operationStatus");
    if (!status) return;
    status.textContent = message;
    status.classList.toggle("is-visible", Boolean(message));
    status.classList.toggle("is-error", isError);
}

function setButtonBusy(buttonId, isBusy, busyLabel, idleLabel) {
    const button = byId(buttonId);
    if (!button) return;
    button.disabled = isBusy;
    button.textContent = isBusy ? busyLabel : idleLabel;
    button.setAttribute("aria-busy", String(isBusy));
}

function initMap() {
    applyTheme(currentTheme);
    mountSearchPlaybackDock();
    if (typeof L === "undefined") {
        setOperationStatus(
            "Không thể khởi tạo bản đồ. Hãy kiểm tra kết nối tới thư viện Leaflet.",
            true,
        );
        return;
    }

    map = L.map("map", {
        center: [10.778, 106.692],
        zoom: 13,
        zoomControl: false,
        renderer: L.canvas(),
    });

    L.tileLayer(
        "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
        {
            maxZoom: 19,
            attribution: "&copy; OpenStreetMap &copy; CARTO",
        },
    ).addTo(map);

    L.control.zoom({ position: "topright" }).addTo(map);

    createMapPane("finalRoutePane", 430);
    createMapPane("searchVisitedPane", 440);
    createMapPane("searchFrontierPane", 450);
    createMapPane("searchCurrentPane", 460);

    searchVisitedLayer = L.layerGroup().addTo(map);
    searchFrontierLayer = L.layerGroup().addTo(map);
    searchCurrentLayer = L.layerGroup().addTo(map);

    map.on("click", (event) =>
        updateAmbulanceGPS(event.latlng.lat, event.latlng.lng),
    );
    onAlgorithmChange();
    loadInitialData();
}

function createMapPane(name, zIndex) {
    const pane = map.createPane(name);
    pane.style.zIndex = String(zIndex);
    pane.style.pointerEvents = "none";
}

async function loadInitialData() {
    try {
        const [nodes, edges, gps, health] = await Promise.all([
            fetchJson(`${API_BASE}/nodes?poi_type=all&limit=30000`),
            fetchJson(`${API_BASE}/edges?limit=100000`),
            fetchJson(`${API_BASE}/ambulance/location`),
            fetchJson(`${API_BASE}/health`),
        ]);

        poisData = Array.isArray(nodes) ? nodes : [];
        hospitalsData = poisData.filter((item) => item?.is_hospital);
        edgesData = Array.isArray(edges) ? edges : [];
        currentAmbulanceData = gps || currentAmbulanceData;
        rebuildEdgeIndex();

        setText(
            "statNodes",
            Number(health.nodes_count || 0).toLocaleString("vi-VN"),
        );
        setText(
            "statEdges",
            Number(health.edges_count || 0).toLocaleString("vi-VN"),
        );
        setText("statHospitals", hospitalsData.length.toLocaleString("vi-VN"));
        setText("statLatency", `${Number(health.latency_ms || 0).toFixed(2)} ms`);
        setText(
            "datasetSummary",
            `Đồ thị đã sẵn sàng với ${Number(health.nodes_count || 0).toLocaleString("vi-VN")} nút và ${Number(health.edges_count || 0).toLocaleString("vi-VN")} cạnh có hướng.`,
        );
        setText("datasetBadge", "Sẵn sàng");
        byId("datasetBadge")?.classList.replace("neutral", "success");
        graphEdgeCount = Number(health.edges_count || edgesData.length);

        populateHospitalSelect();
        populateWaypointSelect();
        populateEdgeSelect();
        populateStartControls();
        onStartModeChange();
        renderWaypointStops();
        renderHospitalsOnMap();
        renderEdgesOnMap();
        updateAmbulanceDisplay(currentAmbulanceData);
    } catch (error) {
        console.error("loadInitialData failed:", error);
        setText(
            "datasetSummary",
            "Không thể tải dữ liệu. Hãy chạy backend và mở dashboard từ cùng origin.",
        );
        setText("datasetBadge", "Lỗi kết nối");
        byId("datasetBadge")?.classList.replace("neutral", "warning");
        setOperationStatus(`Không thể tải dữ liệu backend: ${error.message}`, true);
        showToast("Không thể kết nối Backend API.", true);
    }
}

function populateHospitalSelect() {
    const select = byId("selectHospital");
    if (!select) return;
    const category = byId("selectHospitalCategory")?.value || "emergency";
    const query = byId("inputSearchHospital")?.value?.toLowerCase().trim() || "";
    const currentVal = select.value;

    select.replaceChildren();

    if (!hospitalsData.length) {
        const option = document.createElement("option");
        option.textContent = "Không có cơ sở y tế trong dữ liệu";
        option.value = "";
        select.append(option);
        select.disabled = true;
        setText("hospitalCountBadge", "(0 BV)");
        return;
    }

    if (!query) {
        const autoOption = document.createElement("option");
        autoOption.value = "";
        autoOption.textContent = "🌟 [TỰ ĐỘNG DÒ TÌM BV GẦN NHẤT BẰNG THUẬT TOÁN ĐÃ CHỌN]";
        autoOption.style.fontWeight = "bold";
        autoOption.style.color = "#38bdf8";
        select.append(autoOption);
    }

    const filteredHospitals = hospitalsData
        .slice()
        .filter((hospital) => {
            const name = String(hospital.name || "").toLowerCase();
            const type = String(hospital.type || hospital.category || "").toLowerCase();

            if (category === "emergency" && !hospital.is_emergency) {
                return false;
            } else if (category === "clinic") {
                const isClinic = !hospital.is_emergency && (name.includes("phòng khám") || name.includes("clinic") || type.includes("phòng khám") || type.includes("chuyên khoa"));
                if (!isClinic) return false;
            } else if (category === "station") {
                const isStation = !hospital.is_emergency && (name.includes("trạm y tế") || name.includes("trung tâm y tế") || type.includes("trạm y tế"));
                if (!isStation) return false;
            }

            return !query || name.includes(query) || type.includes(query);
        })
        .sort((a, b) =>
            String(a.name || "").localeCompare(String(b.name || ""), "vi"),
        );

    filteredHospitals.forEach((hospital) => {
        const option = document.createElement("option");
        option.value = hospital.node_id;
        const emoji = hospital.is_emergency ? "🚨" : "🏥";
        option.textContent = `${emoji} ${hospital.name || "Cơ sở y tế"} (${hospital.category || hospital.type || "N/A"})`;
        select.append(option);
    });

    setText("hospitalCountBadge", `(${filteredHospitals.length} BV)`);
    select.disabled = false;

    if (currentVal && Array.from(select.options).some((option) => option.value === currentVal)) {
        select.value = currentVal;
    } else if (!filteredHospitals.length) {
        const option = document.createElement("option");
        option.value = "";
        option.textContent = "-- Không tìm thấy bệnh viện phù hợp --";
        select.append(option);
        select.value = "";
    }
}

function haversineDistanceMeters(lat1, lng1, lat2, lng2) {
    const toRadians = (value) => (value * Math.PI) / 180;
    const earthRadius = 6371000;
    const dLat = toRadians(lat2 - lat1);
    const dLng = toRadians(lng2 - lng1);
    const a =
        Math.sin(dLat / 2) ** 2 +
        Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) * Math.sin(dLng / 2) ** 2;
    return 2 * earthRadius * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

async function selectNearestHospital() {
    if (!hospitalsData.length) {
        showToast("Không có bệnh viện nào trong dữ liệu.", true);
        return;
    }

    const category = byId("selectHospitalCategory")?.value || "emergency";
    const emergencyOnly = category === "emergency";
    const query = byId("inputSearchHospital")?.value?.toLowerCase().trim() || "";
    const currentGps = currentAmbulanceData || {};
    const baseLat = Number(currentGps.lat);
    const baseLng = Number(currentGps.lng);

    const candidates = hospitalsData.filter((hospital) => {
        if (emergencyOnly && !hospital.is_emergency) return false;
        const name = String(hospital.name || "").toLowerCase();
        const type = String(hospital.type || hospital.category || "").toLowerCase();
        return !query || name.includes(query) || type.includes(query);
    });

    const referenceLat = Number.isFinite(baseLat) ? baseLat : 10.773;
    const referenceLng = Number.isFinite(baseLng) ? baseLng : 106.698;

    let nearest = null;
    let bestDistance = Number.POSITIVE_INFINITY;
    candidates.forEach((hospital) => {
        const lat = Number(hospital.lat);
        const lng = Number(hospital.lng);
        if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;
        const distance = haversineDistanceMeters(referenceLat, referenceLng, lat, lng);
        if (distance < bestDistance) {
            bestDistance = distance;
            nearest = hospital;
        }
    });

    if (!nearest) {
        showToast("Không tìm thấy bệnh viện phù hợp để dò gần nhất.", true);
        return;
    }

    const select = byId("selectHospital");
    if (select) {
        select.value = String(nearest.node_id);
        if (typeof onHospitalSelectChange === "function") {
            onHospitalSelectChange();
        }
    }
    calculateRoute();
}

function populateEdgeSelect() {
    const select = byId("selectEdge");
    if (!select) return;
    select.replaceChildren();

    edgesData.slice(0, 100).forEach((edge) => {
        const option = document.createElement("option");
        option.value = edge.edge_id;
        option.textContent = `${edge.name || edge.edge_id} · ${Number(edge.distance || 0).toFixed(0)} m · mức ${edge.congestion_level}`;
        select.append(option);
    });
    select.disabled = edgesData.length === 0;
}

function populateStartControls() {
    const nodeId = currentAmbulanceData?.mapped_nearest_node?.nearest_node_id;
    if (Number.isInteger(nodeId) && byId("inputStartNode")) {
        byId("inputStartNode").value = nodeId;
    }
}

function onStartModeChange() {
    const customMode = byId("selectStartMode")?.value === "custom";
    const input = byId("inputStartNode");
    if (!input) return;
    input.hidden = !customMode;
    input.required = customMode;
}

function onAlgorithmChange() {
    updateCriterionNotice();
}

function onCriterionChange() {
    updateCriterionNotice();
}

function updateCriterionNotice() {
    const algorithm = byId("selectAlgorithm")?.value || "astar";
    const criterion = byId("selectCriterion")?.value || "cost";
    const spec = ALGORITHM_SPECS[algorithm];
    const compatible = spec.compatibleCriteria.includes(criterion);
    const compatibilityText = compatible
        ? "Cặp lựa chọn này phù hợp."
        : `Lưu ý: ${spec.label} thực tế tối ưu ${spec.objective}, không trực tiếp tối ưu “${CRITERION_LABELS[criterion]}”.`;
    setText(
        "criterionNotice",
        `${compatibilityText} Tiêu chí được frontend dùng để đánh giá kết quả và tối ưu thứ tự nhiều địa điểm; mục tiêu tìm đường thực tế do thuật toán backend quyết định.`,
    );
}

function normalizeSearchText(str) {
    if (!str) return "";
    return String(str)
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/đ/g, "d")
        .replace(/Đ/g, "D")
        .toLowerCase()
        .trim();
}

function findLocationsByName(query, limit = 8) {
    const cleanQuery = normalizeSearchText(query);
    if (!cleanQuery) return [];

    const allLocations = [];
    const seenNodeIds = new Set();
    const pool = [...hospitalsData, ...poisData];

    for (const item of pool) {
        const nodeId = Number(item.node_id ?? item.poi_node_id);
        if (!Number.isInteger(nodeId) || seenNodeIds.has(nodeId)) continue;

        const name = String(item.name || "");
        const cleanName = normalizeSearchText(name);
        const type = String(item.type || item.category || "");
        const cleanType = normalizeSearchText(type);

        let score = -1;
        if (cleanName.startsWith(cleanQuery)) {
            score = 100 - cleanName.length;
        } else if (cleanName.includes(cleanQuery)) {
            score = 50 - cleanName.length;
        } else if (cleanType.includes(cleanQuery)) {
            score = 20;
        } else if (String(nodeId).includes(cleanQuery)) {
            score = 30;
        }

        if (score >= 0) {
            seenNodeIds.add(nodeId);
            allLocations.push({
                node_id: nodeId,
                name: name || `Node ${nodeId}`,
                type: type || (item.is_hospital ? "Cơ sở Y tế" : "Địa điểm"),
                is_hospital: Boolean(item.is_hospital),
                is_emergency: Boolean(item.is_emergency),
                score,
            });
        }
    }

    allLocations.sort((a, b) => b.score - a.score);
    return allLocations.slice(0, limit);
}

function parseNodeIdList(rawValue) {
    if (!rawValue) return [];
    const uniqueIds = new Set();
    rawValue
        .split(/[,;\s]+/)
        .map((value) => Number.parseInt(value.trim(), 10))
        .filter(Number.isInteger)
        .forEach((value) => uniqueIds.add(value));
    return Array.from(uniqueIds);
}

function renderWaypointStops() {
    const listContainer = byId("waypointStopsList");
    const countBadge = byId("waypointCountBadge");
    const clearBtn = byId("btnClearWaypoints");
    const syncInput = byId("inputWaypoints");

    if (countBadge) {
        countBadge.textContent = `(${selectedWaypoints.length}/${MAX_WAYPOINTS})`;
    }
    if (clearBtn) {
        clearBtn.style.display = selectedWaypoints.length > 0 ? "inline-flex" : "none";
    }
    if (syncInput) {
        syncInput.value = selectedWaypoints.join(", ");
    }

    if (!listContainer) return;
    listContainer.replaceChildren();

    if (selectedWaypoints.length === 0) {
        const emptyHint = document.createElement("div");
        emptyHint.className = "waypoint-empty-hint";
        emptyHint.innerHTML = `<span>Chưa có trạm dừng nào. Gõ tên địa điểm ở trên hoặc bấm <strong>➕ Thêm điểm ghé</strong> trên bản đồ.</span>`;
        listContainer.append(emptyHint);
        return;
    }

    selectedWaypoints.forEach((nodeId, index) => {
        const label = getNodeLabel(nodeId);
        const card = document.createElement("div");
        card.className = "waypoint-stop-card";

        const indexBadge = document.createElement("div");
        indexBadge.className = "stop-index-badge";
        indexBadge.textContent = String(index + 1);

        const content = document.createElement("div");
        content.className = "stop-content";

        const nameEl = document.createElement("div");
        nameEl.className = "stop-name";
        nameEl.textContent = label;
        nameEl.title = `${label} (Node ${nodeId})`;

        const idEl = document.createElement("div");
        idEl.className = "stop-node-id";
        idEl.textContent = `Node: ${nodeId}`;

        content.append(nameEl, idEl);

        const actions = document.createElement("div");
        actions.className = "stop-actions";

        const upBtn = document.createElement("button");
        upBtn.type = "button";
        upBtn.className = "btn-stop-action";
        upBtn.textContent = "▲";
        upBtn.title = "Di chuyển lên trước";
        upBtn.disabled = index === 0;
        upBtn.onclick = () => moveWaypoint(index, -1);

        const downBtn = document.createElement("button");
        downBtn.type = "button";
        downBtn.className = "btn-stop-action";
        downBtn.textContent = "▼";
        downBtn.title = "Di chuyển xuống sau";
        downBtn.disabled = index === selectedWaypoints.length - 1;
        downBtn.onclick = () => moveWaypoint(index, 1);

        const delBtn = document.createElement("button");
        delBtn.type = "button";
        delBtn.className = "btn-stop-action btn-delete";
        delBtn.textContent = "✕";
        delBtn.title = "Xóa trạm dừng này";
        delBtn.onclick = () => removeWaypointAtIndex(index);

        actions.append(upBtn, downBtn, delBtn);
        card.append(indexBadge, content, actions);
        listContainer.append(card);
    });
}

function addWaypoint(nodeId) {
    const numId = Number(nodeId);
    if (!Number.isInteger(numId)) return;

    if (selectedWaypoints.includes(numId)) {
        showToast(`Điểm ${getNodeLabel(numId)} đã có trong danh sách trạm dừng.`, true);
        map?.closePopup();
        return;
    }

    if (selectedWaypoints.length >= MAX_WAYPOINTS) {
        showToast(`Đã đạt tối đa ${MAX_WAYPOINTS} điểm trung gian.`, true);
        map?.closePopup();
        return;
    }

    selectedWaypoints.push(numId);
    renderWaypointStops();
    showToast(`Đã thêm trạm ${selectedWaypoints.length}: ${getNodeLabel(numId)}.`);
    map?.closePopup();
}

function removeWaypointAtIndex(index) {
    if (index >= 0 && index < selectedWaypoints.length) {
        const removed = selectedWaypoints.splice(index, 1)[0];
        renderWaypointStops();
        showToast(`Đã xóa trạm dừng: ${getNodeLabel(removed)}.`);
    }
}

function removeWaypoint(nodeId) {
    const numId = Number(nodeId);
    const index = selectedWaypoints.indexOf(numId);
    if (index !== -1) {
        removeWaypointAtIndex(index);
    }
}

function moveWaypoint(index, direction) {
    const targetIndex = index + direction;
    if (targetIndex < 0 || targetIndex >= selectedWaypoints.length) return;
    const temp = selectedWaypoints[index];
    selectedWaypoints[index] = selectedWaypoints[targetIndex];
    selectedWaypoints[targetIndex] = temp;
    renderWaypointStops();
}

function clearAllWaypoints() {
    selectedWaypoints = [];
    renderWaypointStops();
    showToast("Đã xóa tất cả trạm dừng.");
}

function populateWaypointSelect() {
    const select = byId("selectWaypoint");
    if (!select) return;
    const query = byId("inputSearchWaypoint")?.value?.trim() || "";

    select.replaceChildren();

    const pool = [...hospitalsData, ...poisData];
    if (!pool.length) {
        const option = document.createElement("option");
        option.textContent = "Đang tải danh sách địa điểm…";
        option.value = "";
        select.append(option);
        select.disabled = true;
        return;
    }

    const cleanQuery = normalizeSearchText(query);
    const seenNodeIds = new Set();
    const filtered = [];

    pool.forEach((item) => {
        const nodeId = Number(item.node_id ?? item.poi_node_id);
        if (!Number.isInteger(nodeId) || seenNodeIds.has(nodeId)) return;

        const name = String(item.name || "");
        const type = String(item.type || item.category || "");
        const cleanName = normalizeSearchText(name);
        const cleanType = normalizeSearchText(type);

        if (!cleanQuery || cleanName.includes(cleanQuery) || cleanType.includes(cleanQuery) || String(nodeId).includes(cleanQuery)) {
            seenNodeIds.add(nodeId);
            filtered.push({
                node_id: nodeId,
                name: name || `Node ${nodeId}`,
                type: type || (item.is_hospital ? "Cơ sở Y tế" : "Địa điểm"),
                is_hospital: Boolean(item.is_hospital),
                is_emergency: Boolean(item.is_emergency),
            });
        }
    });

    filtered.sort((a, b) => a.name.localeCompare(b.name, "vi"));

    const defaultOption = document.createElement("option");
    defaultOption.value = "";
    defaultOption.textContent = filtered.length
        ? `-- Chọn địa điểm ghé qua (${filtered.length} địa điểm) --`
        : "-- Không tìm thấy địa điểm phù hợp --";
    select.append(defaultOption);

    filtered.forEach((item) => {
        const option = document.createElement("option");
        option.value = String(item.node_id);
        const emoji = item.is_emergency ? "🚨" : item.is_hospital ? "🏥" : "📍";
        option.textContent = `${emoji} ${item.name} (${item.type})`;
        select.append(option);
    });

    select.disabled = filtered.length === 0;
    select.value = "";
}

function addSelectedWaypointFromDropdown() {
    const select = byId("selectWaypoint");
    const val = select?.value;
    if (!val) {
        showToast("Vui lòng chọn một địa điểm từ danh sách dropdown để thêm.", true);
        return;
    }
    addWaypoint(Number(val));
    select.value = "";
}

function onWaypointSearchInput(event) {
    populateWaypointSelect();
}

function onInputWaypointsManualChange() {
    const syncInput = byId("inputWaypoints");
    if (!syncInput) return;
    const parsed = parseNodeIdList(syncInput.value);
    selectedWaypoints = parsed.slice(0, MAX_WAYPOINTS);
    renderWaypointStops();
}

function getPlannerInput() {
    const goalNodeId = Number.parseInt(byId("selectHospital")?.value, 10);
    const startMode = byId("selectStartMode")?.value || "current";
    const customStart = Number.parseInt(byId("inputStartNode")?.value, 10);
    const currentStart =
        currentAmbulanceData?.mapped_nearest_node?.nearest_node_id;
    const startNodeId = startMode === "custom" ? customStart : currentStart;

    if (!Number.isInteger(startNodeId)) {
        throw new Error("Vui lòng chọn hoặc nhập điểm xuất phát hợp lệ.");
    }
    if (!Number.isInteger(goalNodeId)) {
        throw new Error("Vui lòng chọn một cơ sở y tế đích hợp lệ.");
    }

    const rawWaypoints = selectedWaypoints.length > 0
        ? selectedWaypoints
        : parseNodeIdList(byId("inputWaypoints")?.value || "");

    const waypointIds = rawWaypoints.filter(
        (nodeId) => nodeId !== startNodeId && nodeId !== goalNodeId,
    );
    if (waypointIds.length > MAX_WAYPOINTS) {
        throw new Error(
            `Chỉ nên dùng tối đa ${MAX_WAYPOINTS} điểm trung gian để tránh quá tải khi demo.`,
        );
    }

    return {
        startNodeId,
        goalNodeId,
        waypointIds,
        algorithm: byId("selectAlgorithm")?.value || "astar",
        criterion: byId("selectCriterion")?.value || "cost",
        visitOrderMode: byId("selectVisitOrder")?.value || "input",
    };
}

function getNodeLabel(nodeId) {
    if (!Number.isInteger(Number(nodeId))) return "Không xác định";
    const numericId = Number(nodeId);
    const ambulanceNode = currentAmbulanceData?.mapped_nearest_node;
    if (ambulanceNode?.nearest_node_id === numericId) {
        return ambulanceNode.nearest_node_name || `Node ${numericId}`;
    }
    const point =
        hospitalsData.find(
            (item) => item.node_id === numericId || item.poi_node_id === numericId,
        ) ||
        poisData.find(
            (item) => item.node_id === numericId || item.poi_node_id === numericId,
        );
    return point?.name || `Node ${numericId}`;
}

let roadAdjacency = new Map();

function rebuildEdgeIndex() {
    edgeIndex = new Map();
    roadAdjacency = new Map();
    edgesData.forEach((edge) => {
        edgeIndex.set(normalizeEdgeId(edge.edge_id), edge);
        indexEdgeNodeCoords(fullRoadNodeCoords, edge);

        const [u, v] = String(edge?.edge_id || "").split("_");
        if (u && v) {
            const uKey = normalizeNodeCoordinateKey(u);
            const vKey = normalizeNodeCoordinateKey(v);
            if (!roadAdjacency.has(uKey)) roadAdjacency.set(uKey, new Set());
            if (!roadAdjacency.has(vKey)) roadAdjacency.set(vKey, new Set());
            roadAdjacency.get(uKey).add(vKey);
            roadAdjacency.get(vKey).add(uKey);
        }
    });
}

function indexEdgeNodeCoords(target, edge) {
    const [sourceId, targetId] = String(edge?.edge_id || "").split("_");
    const sourceCoords = normalizeMapCoords([edge?.u_lat, edge?.u_lng]);
    const targetCoords = normalizeMapCoords([edge?.v_lat, edge?.v_lng]);
    if (sourceId && sourceCoords)
        target.set(normalizeNodeCoordinateKey(sourceId), sourceCoords);
    if (targetId && targetCoords)
        target.set(normalizeNodeCoordinateKey(targetId), targetCoords);
}

function getPathEdge(pathNodes, index) {
    return edgeIndex.get(
        normalizeEdgeId(`${pathNodes[index]}_${pathNodes[index + 1]}`),
    );
}

function analyzePathCongestion(response) {
    const pathNodes = Array.isArray(response.path_nodes)
        ? response.path_nodes
        : [];
    const totalDistance = Number(response.total_distance_m || 0);
    let knownDistance = 0;
    let knownTravelSeconds = 0;
    let levelTotal = 0;
    let knownEdges = 0;
    const highCongestionEdges = [];
    const speedByLevel = { 1: 40, 2: 34, 3: 27, 4: 20, 5: 14, 6: 9 };

    for (let index = 0; index < pathNodes.length - 1; index += 1) {
        const edge = getPathEdge(pathNodes, index);
        if (!edge) continue;
        const distance = Math.max(0, Number(edge.distance || 0));
        const level = Math.min(6, Math.max(1, Number(edge.congestion_level || 1)));
        const speed = speedByLevel[level] || DEFAULT_SPEED_KPH;
        knownDistance += distance;
        knownTravelSeconds += distance / ((speed * 1000) / 3600);
        levelTotal += level;
        knownEdges += 1;
        if (level >= 4) {
            highCongestionEdges.push({
                edgeId: edge.edge_id,
                name: edge.name || edge.edge_id,
                level,
                distance,
            });
        }
    }

    const unknownDistance = Math.max(
        0,
        totalDistance - Math.min(totalDistance, knownDistance),
    );
    const estimatedTimeSeconds =
        knownTravelSeconds + unknownDistance / ((DEFAULT_SPEED_KPH * 1000) / 3600);
    return {
        estimatedTimeSeconds,
        highCongestionEdges,
        knownEdges,
        knownDistance,
        congestionLevelTotal: levelTotal,
        totalEdges: Math.max(0, pathNodes.length - 1),
        averageKnownLevel: knownEdges ? levelTotal / knownEdges : null,
    };
}

function annotateResult(response) {
    const pathNodes = Array.isArray(response.path_nodes)
        ? response.path_nodes
        : [];
    const congestion = analyzePathCongestion(response);
    return {
        ...response,
        hopCount: Number.isFinite(Number(response.hop_count))
            ? Number(response.hop_count)
            : Math.max(0, pathNodes.length - 1),
        estimatedTimeSeconds: congestion.estimatedTimeSeconds,
        congestion,
    };
}

function scoreResult(response, criterion) {
    const result =
        response.estimatedTimeSeconds === undefined
            ? annotateResult(response)
            : response;
    if (criterion === "distance") return finiteMetric(result.total_distance_m);
    if (criterion === "hops") return finiteMetric(result.hopCount);
    if (criterion === "time") return finiteMetric(result.estimatedTimeSeconds);
    return finiteMetric(result.total_cost);
}

function finiteMetric(value) {
    const numericValue = Number(value);
    return Number.isFinite(numericValue)
        ? numericValue
        : Number.POSITIVE_INFINITY;
}

async function runRouteSegment(startId, goalId, algorithm) {
    const cacheKey = `${algorithm}:${startId}:${goalId}`;
    if (routeRequestCache.has(cacheKey)) return routeRequestCache.get(cacheKey);

    const request = fetchJson(`${API_BASE}/route`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            start_node_id: startId,
            goal_node_id: goalId,
            algorithm,
        }),
    })
        .then((data) => {
            if (!data?.found) {
                throw new Error(
                    data?.message ||
                    `Không tìm thấy đường từ node ${startId} tới node ${goalId}.`,
                );
            }
            return annotateResult(data);
        })
        .catch((error) => {
            routeRequestCache.delete(cacheKey);
            throw error;
        });

    routeRequestCache.set(cacheKey, request);
    return request;
}

async function runOrderedRoute(
    nodeOrder,
    algorithm,
    progressCallback = () => { },
) {
    const segments = [];
    for (let index = 0; index < nodeOrder.length - 1; index += 1) {
        progressCallback(index + 1, nodeOrder.length - 1);
        const start = nodeOrder[index];
        const goal = nodeOrder[index + 1];
        const result = await runRouteSegment(start, goal, algorithm);
        segments.push({ start, goal, result });
    }
    return segments;
}

async function optimizeWaypointOrderOnBackend(input) {
    const response = await fetchJson(`${API_BASE}/route/multi-location`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            start_node_id: input.startNodeId,
            waypoint_ids: input.waypointIds,
            goal_node_id: input.goalNodeId,
            route_algorithm: input.algorithm,
            optimization_method: input.visitOrderMode,
            criterion: input.criterion,
        }),
    });
    if (!response?.found) {
        throw new Error(response?.message || "Không thể tối ưu thứ tự điểm ghé.");
    }
    return {
        orderedWaypoints: response.ordered_waypoints || [],
        segments: (response.segments || []).map((segment) => ({
            start: segment.start,
            goal: segment.goal,
            result: annotateResult(segment.result),
        })),
        isOptimal: Boolean(response.is_optimal),
    };
}

function aggregateSegments(segments, visitingOrder) {
    const pathCoords = [];
    const pathNodes = [];
    const highCongestionEdges = [];
    let totalCost = 0;
    let totalDistance = 0;
    let totalExpanded = 0;
    let totalProcessingTime = 0;
    let totalTravelTime = 0;
    let totalHops = 0;
    let knownEdges = 0;
    let knownCongestionDistance = 0;
    let congestionLevelTotal = 0;
    let totalEdges = 0;

    segments.forEach(({ result }, index) => {
        const coords = Array.isArray(result.path_coords) ? result.path_coords : [];
        const nodes = Array.isArray(result.path_nodes) ? result.path_nodes : [];
        pathCoords.push(...(index === 0 ? coords : coords.slice(1)));
        pathNodes.push(...(index === 0 ? nodes : nodes.slice(1)));
        totalCost += Number(result.total_cost || 0);
        totalDistance += Number(result.total_distance_m || 0);
        totalExpanded += Number(result.nodes_expanded || 0);
        totalProcessingTime += Number(result.execution_time_ms || 0);
        totalTravelTime += Number(result.estimatedTimeSeconds || 0);
        totalHops += Number(result.hopCount || 0);
        knownEdges += result.congestion?.knownEdges || 0;
        knownCongestionDistance += result.congestion?.knownDistance || 0;
        congestionLevelTotal += result.congestion?.congestionLevelTotal || 0;
        totalEdges += result.congestion?.totalEdges || 0;
        highCongestionEdges.push(...(result.congestion?.highCongestionEdges || []));
    });

    return {
        segments,
        visitingOrder,
        pathCoords,
        pathNodes,
        totalCost,
        totalDistance,
        totalExpanded,
        totalProcessingTime,
        totalTravelTime,
        totalHops,
        congestion: {
            highCongestionEdges,
            knownEdges,
            knownCongestionDistance,
            congestionLevelTotal,
            totalEdges,
            averageKnownLevel: knownEdges
                ? congestionLevelTotal / knownEdges
                : null,
        },
    };
}

async function calculateRoute() {
    let input;
    try {
        input = getPlannerInput();
    } catch (error) {
        setOperationStatus(error.message, true);
        showToast(error.message, true);
        return;
    }

    setButtonBusy(
        "btnCalculateRoute",
        true,
        "Đang tìm tuyến…",
        "Tìm tuyến đường",
    );
    byId("btnCompareAlgorithms").disabled = true;
    setOperationStatus(
        `${ALGORITHM_SPECS[input.algorithm].label} đang xử lý dữ liệu…`,
    );
    byId("routeResultPanel").hidden = true;
    byId("comparisonPanel").hidden = true;
    clearFinalRoute();
    clearSearchVisualization();

    try {
        const originalOrder = [
            input.startNodeId,
            ...input.waypointIds,
            input.goalNodeId,
        ];
        let selectedSegments;
        let selectedOrder = originalOrder;
        let originalAggregate = null;

        if (input.visitOrderMode !== "input" && input.waypointIds.length > 1) {
            const originalSegments = await runOrderedRoute(
                originalOrder,
                input.algorithm,
                (current, total) => {
                    setOperationStatus(
                        `Đang tính thứ tự ban đầu: chặng ${current}/${total}…`,
                    );
                },
            );
            originalAggregate = aggregateSegments(originalSegments, originalOrder);

            setOperationStatus(
                `${visitOrderLabel(input.visitOrderMode)} đang tối ưu thứ tự trên backend…`,
            );
            const optimized = await optimizeWaypointOrderOnBackend(input);
            selectedOrder = [
                input.startNodeId,
                ...optimized.orderedWaypoints,
                input.goalNodeId,
            ];
            selectedSegments = optimized.segments;
        } else {
            selectedSegments = await runOrderedRoute(
                originalOrder,
                input.algorithm,
                (current, total) => {
                    setOperationStatus(`Đang tìm chặng ${current}/${total}…`);
                },
            );
        }

        const aggregate = aggregateSegments(selectedSegments, selectedOrder);
        renderRouteResult(aggregate, input, originalAggregate);

        const combinedTrace = combineSearchTraces(
            selectedSegments,
            input.algorithm,
        );
        if (combinedTrace) {
            const allSegments = buildCoordinateSegments(aggregate.pathCoords);
            drawBackgroundRouteLine(allSegments);
            fitMapToRouteSegments(allSegments);
            await startSearchVisualization(combinedTrace);
            playSearchAnimation();
        } else {
            clearSearchVisualization();
            drawFinalRoute(aggregate);
        }

        setOperationStatus(
            `Hoàn tất ${selectedSegments.length} chặng bằng ${ALGORITHM_SPECS[input.algorithm].label}.`,
        );
        showToast(
            `Đã tìm thấy tuyến: ${aggregate.totalDistance.toFixed(0)} m, ${aggregate.totalExpanded.toLocaleString("vi-VN")} nút mở rộng.`,
        );
    } catch (error) {
        console.error("calculateRoute failed:", error);
        clearSearchVisualization();
        setOperationStatus(`Không thể tính tuyến: ${error.message}`, true);
        showToast(`Không thể tính tuyến: ${error.message}`, true);
    } finally {
        setButtonBusy(
            "btnCalculateRoute",
            false,
            "Đang tìm tuyến…",
            "Tìm tuyến đường",
        );
        byId("btnCompareAlgorithms").disabled = false;
    }
}

function renderRouteResult(aggregate, input, originalAggregate) {
    const spec = ALGORITHM_SPECS[input.algorithm];
    const panel = byId("routeResultPanel");
    panel.hidden = false;

    setText(
        "resultTitle",
        aggregate.segments.length > 1
            ? "Đã tìm thấy tuyến nhiều chặng"
            : "Đã tìm thấy tuyến đường",
    );
    const badge = byId("optimalityBadge");
    badge.textContent = spec.optimality;
    badge.className = `status-badge ${spec.badgeClass}`;

    renderRouteSummary(aggregate, input);
    setText("resCost", aggregate.totalCost.toFixed(2));
    setText("resDistance", formatDistance(aggregate.totalDistance));
    setText("resTravelTime", formatDuration(aggregate.totalTravelTime));
    setText("resHops", aggregate.totalHops.toLocaleString("vi-VN"));
    setText("resExpanded", aggregate.totalExpanded.toLocaleString("vi-VN"));
    setText("resTime", `${aggregate.totalProcessingTime.toFixed(2)} ms`);

    renderPathNodes(aggregate.pathNodes, aggregate.visitingOrder);
    renderVisitingOrder(aggregate.visitingOrder);
    renderOrderComparison(
        aggregate,
        originalAggregate,
        input.criterion,
        input.visitOrderMode,
    );
    renderExplanation(aggregate, input, spec);
    renderCongestionExplanation(aggregate);
    renderSegmentList(aggregate.segments);
}

function renderRouteSummary(aggregate, input) {
    const summary = byId("routeSummary");
    summary.replaceChildren();
    const fields = [
        ["Xuất phát", `${getNodeLabel(input.startNodeId)} (${input.startNodeId})`],
        ["Đích đến", `${getNodeLabel(input.goalNodeId)} (${input.goalNodeId})`],
        ["Thuật toán", ALGORITHM_SPECS[input.algorithm].label],
        ["Tiêu chí đánh giá", CRITERION_LABELS[input.criterion]],
        [
            "Số điểm trung gian",
            String(Math.max(0, aggregate.visitingOrder.length - 2)),
        ],
        [
            "Cách sắp thứ tự",
            visitOrderLabel(input.visitOrderMode),
        ],
    ];

    fields.forEach(([label, value]) => {
        const wrapper = document.createElement("div");
        wrapper.className = "summary-field";
        const labelElement = document.createElement("span");
        labelElement.textContent = label;
        const valueElement = document.createElement("strong");
        valueElement.textContent = value;
        wrapper.append(labelElement, valueElement);
        summary.append(wrapper);
    });
}

function renderPathNodes(pathNodes = [], visitingOrder = []) {
    const container = byId("pathNodesFlow");
    if (!container) return;
    container.replaceChildren();

    const countBadge = byId("pathNodeCountBadge");
    if (countBadge) countBadge.textContent = `${pathNodes.length} nút`;

    if (!pathNodes.length) {
        container.textContent = "Chưa có dữ liệu nút.";
        return;
    }

    const waypoints = visitingOrder.slice(1, -1);

    pathNodes.forEach((nodeId, index) => {
        if (index > 0) {
            const arrow = document.createElement("span");
            arrow.className = "path-arrow";
            arrow.textContent = "→";
            container.append(arrow);
        }

        const chip = document.createElement("span");
        chip.className = "path-node";

        const isStart = index === 0;
        const isGoal = index === pathNodes.length - 1;
        const isWaypoint = waypoints.includes(nodeId);

        if (isStart) {
            chip.classList.add("node-start");
            chip.textContent = `🚩 ${getNodeLabel(nodeId)} (${nodeId})`;
        } else if (isGoal) {
            chip.classList.add("node-goal");
            chip.textContent = `🏁 ${getNodeLabel(nodeId)} (${nodeId})`;
        } else if (isWaypoint) {
            chip.classList.add("node-waypoint");
            chip.textContent = `📍 ${getNodeLabel(nodeId)} (${nodeId})`;
        } else {
            chip.classList.add("node-inter");
            const label = getNodeLabel(nodeId);
            chip.textContent = label.startsWith("Node ") ? String(nodeId) : `${label} (${nodeId})`;
        }

        chip.title = `Nút ${index + 1}/${pathNodes.length}: ID ${nodeId}`;
        container.append(chip);
    });
}

function renderVisitingOrder(order) {
    const block = byId("multiLocationOrderBlock");
    const container = byId("visitingOrder");
    if (!container) return;

    if (order.length <= 2) {
        if (block) block.hidden = true;
        container.replaceChildren();
        return;
    }

    if (block) block.hidden = false;
    container.replaceChildren();
    order.forEach((nodeId, index) => {
        if (index > 0) {
            const arrow = document.createElement("span");
            arrow.className = "path-arrow";
            arrow.textContent = "→";
            container.append(arrow);
        }
        const chip = document.createElement("span");
        chip.className = "path-node";
        if (index === 0) {
            chip.classList.add("node-start");
            chip.textContent = `🚩 ${getNodeLabel(nodeId)}`;
        } else if (index === order.length - 1) {
            chip.classList.add("node-goal");
            chip.textContent = `🏁 ${getNodeLabel(nodeId)}`;
        } else {
            chip.classList.add("node-waypoint");
            chip.textContent = `📍 Trạm ${index}: ${getNodeLabel(nodeId)}`;
        }
        container.append(chip);
    });
}

function renderOrderComparison(optimized, original, criterion, method) {
    const container = byId("orderComparison");
    if (!container) return;
    if (!original || method === "input" || optimized.visitingOrder.length <= 3) {
        if (optimized.visitingOrder.length <= 2) {
            container.innerHTML = `<span style="font-size: 0.65rem; color: var(--text-muted);">💡 <em>Tuyến 2 điểm (Xuất phát ➔ Đích). Nhập thêm các điểm trung gian (hoặc bấm chọn trên bản đồ) để kích hoạt thuật toán tối ưu thứ tự ghé thăm (TSP).</em></span>`;
            container.hidden = false;
        } else {
            container.hidden = true;
            container.textContent = "";
        }
        return;
    }

    const originalScore = scoreAggregate(original, criterion);
    const optimizedScore = scoreAggregate(optimized, criterion);
    const difference = originalScore
        ? ((originalScore - optimizedScore) / originalScore) * 100
        : 0;
    const originalOrder = original.visitingOrder.map(getNodeLabel).join(" → ");
    const optimizedOrder = optimized.visitingOrder.map(getNodeLabel).join(" → ");
    const outcome =
        difference >= 0
            ? `cải thiện ${difference.toFixed(1)}%`
            : `cao hơn ${Math.abs(difference).toFixed(1)}%`;
    const guarantee = method === "held_karp" ? "phương án tối ưu toàn cục" : "phương án xấp xỉ";
    container.textContent = `Thứ tự ban đầu: ${originalOrder}. Thứ tự tối ưu (${visitOrderLabel(method)}): ${optimizedOrder}. Theo “${CRITERION_LABELS[criterion]}”, ${guarantee} ${outcome}.`;
    container.hidden = false;
}

function renderExplanation(aggregate, input, spec) {
    const routeSummaryName = aggregate.visitingOrder.map(getNodeLabel).join(" → ");
    const chosenCost = aggregate.totalCost.toFixed(2);
    const chosenDist = formatDistance(aggregate.totalDistance);
    const chosenTime = formatDuration(aggregate.totalTravelTime);
    const highEdges = aggregate.congestion?.highCongestionEdges || [];
    const highEdgeNames = Array.from(new Set(highEdges.map((e) => e.name))).slice(0, 3);
    const compatible = spec.compatibleCriteria.includes(input.criterion);

    // 1. Human-understandable narrative explanation
    let narrative = "";
    if (input.algorithm === "astar" || input.algorithm === "ucs") {
        narrative = `Tuyến đường <strong>${routeSummaryName}</strong> được chọn bằng <strong>${spec.label}</strong> vì đạt chi phí giao thông tổng hợp thấp nhất (Cost: <strong>${chosenCost}</strong>, thời gian ước tính <strong>${chosenTime}</strong>, quãng đường <strong>${chosenDist}</strong>).`;
        if (highEdges.length > 0) {
            narrative += ` Tuyến có đi qua một số đoạn mật độ cao (${highEdgeNames.join(", ")}), nhưng thuật toán đã cân bằng tối ưu giữa cự ly và độ trễ để tổng chi phí phạt là nhỏ nhất.`;
        } else {
            narrative += ` Tuyến đường tránh được các đoạn ùn tắc nặng (mức 4–6), giúp xe cấp cứu lưu thông nhanh chóng và an toàn nhất.`;
        }
    } else if (input.algorithm === "dijkstra") {
        narrative = `Tuyến đường <strong>${routeSummaryName}</strong> được chọn bằng <strong>Dijkstra</strong> nhằm đạt <strong>tổng quãng đường ngắn nhất (${chosenDist})</strong>.`;
        if (highEdges.length > 0) {
            narrative += ` Lưu ý: Tuyến đường ngắn nhất về khoảng cách này đi qua ${highEdges.length} đoạn có mức ùn tắc cao (${highEdgeNames.join(", ")}), nên thời gian thực tế (${chosenTime}) có thể kéo dài hơn so với phương án né kẹt xe của A* hoặc UCS.`;
        } else {
            narrative += ` Tuyến đường vừa tối ưu tuyệt đối về cự ly (${chosenDist}) vừa không gặp điểm ùn tắc nặng nào trên hành trình.`;
        }
    } else if (input.algorithm === "bfs") {
        narrative = `Tuyến đường <strong>${routeSummaryName}</strong> được chọn bằng <strong>BFS</strong> nhằm tìm lộ trình có <strong>ít chặng rẽ nhất (${aggregate.totalHops} chặng)</strong>. Lộ trình này đơn giản hóa hướng đi cho tài xế nhưng không đảm bảo ngắn nhất về cự ly hay thời gian.`;
    } else if (input.algorithm === "dfs") {
        narrative = `Tuyến đường <strong>${routeSummaryName}</strong> được duyệt theo chiều sâu (<strong>DFS</strong>). Lộ trình duyệt theo nhánh đầu tiên tìm thấy (${chosenDist}, ${aggregate.totalHops} chặng) nhằm mô phỏng cây duyệt và <strong>không đảm bảo tối ưu</strong>.`;
    } else if (input.algorithm === "hill_climbing") {
        narrative = `Tuyến đường <strong>${routeSummaryName}</strong> được tạo bởi <strong>Hill Climbing</strong> dựa trên ước lượng Haversine tốt nhất tại từng nút rẽ cục bộ.`;
    } else {
        narrative = `Tuyến đường <strong>${routeSummaryName}</strong> được lập thành công bằng <strong>${spec.label}</strong> với chi phí ${chosenCost} và cự ly ${chosenDist}.`;
    }

    const narrativeEl = byId("routeNarrative");
    if (narrativeEl) narrativeEl.innerHTML = narrative;

    // 2. Structured evaluation items (5 distinct criteria)
    // Criterion 1: Why the selected route was chosen
    let whyChosenText = "";
    if (input.algorithm === "astar") {
        whyChosenText = `A* Search chọn tuyến này bằng cách liên tục mở rộng nút có tổng f(n) = g(n) + h(n) nhỏ nhất, kết hợp chi phí thực tế với hàm ước lượng khoảng cách Haversine.`;
    } else if (input.algorithm === "ucs") {
        whyChosenText = `Uniform Cost Search (UCS) ưu tiên duyệt các nhánh đường có chi phí tích lũy g(n) thấp nhất từ điểm xuất phát đến đích.`;
    } else if (input.algorithm === "dijkstra") {
        whyChosenText = `Dijkstra chọn tuyến đường này bằng cách tìm đường đi có tổng chiều dài các cạnh tích lũy là nhỏ nhất.`;
    } else if (input.algorithm === "bfs") {
        whyChosenText = `BFS duyệt theo từng tầng lân cận và dừng ngay khi chạm đích, tìm ra lộ trình có ít nút rẽ/chặng chuyển hướng nhất.`;
    } else if (input.algorithm === "dfs") {
        whyChosenText = `DFS chọn nhánh đầu tiên đi sâu đến đích theo ngăn xếp, giúp khảo sát cây tìm kiếm nhưng không tối ưu chi phí.`;
    } else {
        whyChosenText = `Hill Climbing chọn tuyến dựa trên hướng đi có khoảng cách Haversine giảm nhanh nhất tại từng ngã rẽ.`;
    }
    setText("expWhyChosen", whyChosenText);

    // Criterion 2: Shortest by distance, fastest by time, or best by total cost
    let metricTypeText = "";
    if (input.algorithm === "dijkstra") {
        metricTypeText = `🎯 Tuyến đường này là NGẮN NHẤT VỀ QUÃNG ĐƯỜNG (${chosenDist}). Thuật toán tối ưu thuần cự ly hình học, không xét mức độ ùn tắc giao thông.`;
    } else if (input.algorithm === "astar" || input.algorithm === "ucs") {
        metricTypeText = `⚡ Tuyến đường này là TỐI ƯU NHẤT VỀ TỔNG CHI PHÍ GIAO THÔNG (Cost: ${chosenCost}) và NHANH NHẤT VỀ THỜI GIAN (${chosenTime}), vì đã tính toán trọng số phạt theo mức độ ùn tắc đô thị.`;
    } else if (input.algorithm === "bfs") {
        metricTypeText = `🧭 Tuyến đường này là ÍT CHẶNG RẼ NHẤT (${aggregate.totalHops} chặng). Đơn giản hóa đường đi nhưng không đảm bảo ngắn nhất về km hay thời gian.`;
    } else {
        metricTypeText = `🔍 Tuyến đường này là PHƯƠNG ÁN XẤP XỈ CỤC BỘ (${chosenDist}, ${chosenTime}). Không đảm bảo là ngắn nhất hay nhanh nhất toàn cục.`;
    }
    setText("expMetricType", metricTypeText);

    // Criterion 3: Road segments with high congestion
    const uniqueHighCount = new Set(highEdges.map((e) => e.edgeId)).size;
    const congText = uniqueHighCount > 0
        ? `Tuyến đi qua ${uniqueHighCount} đoạn ùn tắc nặng (mức 4–6): ${highEdgeNames.join(", ")}${uniqueHighCount > 3 ? ", …" : ""}. Mức ùn tắc TB: ${aggregate.congestion.averageKnownLevel?.toFixed(1) || "—"}/6.`
        : `Không có đoạn đường nào bị ùn tắc mức 4–6 trên lộ trình quan sát được. Mức ùn tắc TB: ${aggregate.congestion.averageKnownLevel?.toFixed(1) || "1.0"}/6.`;
    setText("expCongestion", congText);

    // Criterion 4: How the result differs from another possible route
    let compText = "";
    if (aggregate.segments.length > 1 && input.visitOrderMode !== "input") {
        compText = `Đã tối ưu thứ tự ghé thăm bằng ${visitOrderLabel(input.visitOrderMode)}, giúp giảm chi phí so với thứ tự ban đầu. Bấm "So sánh 6 thuật toán" để xem chi tiết đối chứng.`;
    } else if (input.algorithm === "dijkstra") {
        compText = `So với A* và UCS (chọn đường né kẹt xe), tuyến Dijkstra có cự ly ngắn hơn (${chosenDist}) nhưng có thể mất nhiều thời gian hơn nếu đi qua các điểm tắc đường.`;
    } else {
        compText = `So với phương án chỉ xét cự ly hình học (Dijkstra) hoặc số chặng rẽ (BFS), thuật toán ${spec.label} mang lại sự cân bằng tối ưu giữa quãng đường (${chosenDist}) và thời gian (${chosenTime}).`;
    }
    setText("expComparison", compText);

    // Criterion 5: Optimality guarantee
    let optText = "";
    if (input.algorithm === "dijkstra") {
        optText = "Đảm bảo tối ưu toàn cục về quãng đường (khi trọng số cạnh không âm).";
    } else if (input.algorithm === "astar") {
        optText = "Đảm bảo tối ưu chi phí tổng hợp khi hàm heuristic Haversine là admissible và consistent.";
    } else if (input.algorithm === "ucs") {
        optText = "Đảm bảo tối ưu chi phí tổng hợp khi mọi chi phí cạnh không âm.";
    } else if (input.algorithm === "bfs") {
        optText = "Đảm bảo tối ưu số chặng rẽ trên đồ thị không trọng số.";
    } else if (input.visitOrderMode === "held_karp") {
        optText = "Held–Karp đảm bảo tối ưu toàn cục cho thứ tự ghé thăm các điểm trung gian.";
    } else {
        optText = "Nghiệm tìm kiếm xấp xỉ/cục bộ, không đảm bảo tính tối ưu toàn cục tuyệt đối.";
    }
    setText("expOptimality", optText);
}

function renderCongestionExplanation(aggregate) {
    const congestion = aggregate.congestion;
    const coverage = congestion.totalEdges
        ? (congestion.knownEdges / congestion.totalEdges) * 100
        : 0;
    const averageLevel = Number.isFinite(congestion.averageKnownLevel)
        ? congestion.averageKnownLevel.toFixed(1)
        : "—";
    const uniqueHighEdges = Array.from(
        new Map(
            congestion.highCongestionEdges.map((edge) => [edge.edgeId, edge]),
        ).values(),
    );

    if (!congestion.knownEdges) {
        setText(
            "congestionExplanation",
            `API route chưa trả chi tiết congestion theo path và mẫu /api/edges hiện không bao phủ cạnh của tuyến. Thời gian di chuyển được ước tính theo tốc độ đô thị mặc định ${DEFAULT_SPEED_KPH} km/h.`,
        );
        return;
    }

    const highText = uniqueHighEdges.length
        ? `Phát hiện ${uniqueHighEdges.length} cạnh ùn tắc mức 4–6 trong phần dữ liệu quan sát: ${uniqueHighEdges
            .slice(0, 4)
            .map((edge) => `${edge.name} (mức ${edge.level})`)
            .join(", ")}${uniqueHighEdges.length > 4 ? ", …" : ""}.`
        : "Không phát hiện cạnh mức ùn tắc 4–6 trong phần dữ liệu quan sát được.";
    setText(
        "congestionExplanation",
        `${highText} Độ phủ dữ liệu cạnh trên path: ${congestion.knownEdges}/${congestion.totalEdges} (${coverage.toFixed(1)}%), tương ứng ${formatDistance(congestion.knownCongestionDistance || 0)}. Mức ùn tắc trung bình của các cạnh có dữ liệu: ${averageLevel}/6. Phần chưa có dữ liệu dùng tốc độ mặc định ${DEFAULT_SPEED_KPH} km/h để ước tính thời gian.`,
    );
}

function renderSegmentList(segments) {
    const container = byId("routeSegmentList");
    container.replaceChildren();
    segments.forEach((segment, index) => {
        const item = document.createElement("div");
        item.className = "route-segment-item";
        const title = document.createElement("strong");
        title.textContent = `Chặng ${index + 1}: ${getNodeLabel(segment.start)} → ${getNodeLabel(segment.goal)}`;
        const metrics = document.createElement("div");
        metrics.textContent = `Cost ${Number(segment.result.total_cost || 0).toFixed(2)} · ${formatDistance(segment.result.total_distance_m)} · ${formatDuration(segment.result.estimatedTimeSeconds)} · ${segment.result.hopCount} cạnh · ${Number(segment.result.nodes_expanded || 0).toLocaleString("vi-VN")} nút mở rộng · ${Number(segment.result.execution_time_ms || 0).toFixed(2)} ms`;
        const path = document.createElement("span");
        path.className = "node-path";
        path.textContent = summarizeNodePath(segment.result.path_nodes || []);
        item.append(title, metrics, path);
        container.append(item);
    });
}

function summarizeNodePath(nodes) {
    if (nodes.length <= 160) return `Path: ${nodes.join(" → ")}`;
    return `Path (${nodes.length} nodes): ${nodes.slice(0, 80).join(" → ")} → … → ${nodes.slice(-80).join(" → ")}`;
}

function drawFinalRoute(aggregate) {
    if (!map) return;
    clearFinalRoute();

    const routeSegments = buildCoordinateSegments(aggregate.pathCoords);
    drawRouteLine(routeSegments);
    fitMapToRouteSegments(routeSegments);

    aggregate.visitingOrder.forEach((nodeId, index) => {
        const pathIndex =
            index === aggregate.visitingOrder.length - 1
                ? aggregate.pathNodes.lastIndexOf(nodeId)
                : aggregate.pathNodes.indexOf(nodeId);
        const coords = normalizeMapCoords(aggregate.pathCoords[pathIndex]);
        if (!coords) return;
        const color =
            index === 0
                ? "#38d996"
                : index === aggregate.visitingOrder.length - 1
                    ? "#ff6684"
                    : "#f5b942";
        const marker = L.circleMarker(coords, {
            pane: "searchCurrentPane",
            radius: 7,
            color,
            fillColor: color,
            fillOpacity: 0.95,
            weight: 2,
        }).bindTooltip(
            `${index === 0 ? "Start" : index === aggregate.visitingOrder.length - 1 ? "Goal" : `Điểm ${index}`}: ${getNodeLabel(nodeId)}`,
        );
        marker.addTo(map);
        routeNodeMarkers.push(marker);
    });
}

function clearFinalRoute() {
    if (!map) return;
    if (activeRoutePolyline) {
        map.removeLayer(activeRoutePolyline);
        activeRoutePolyline = null;
    }
    if (backgroundRoutePolyline) {
        map.removeLayer(backgroundRoutePolyline);
        backgroundRoutePolyline = null;
    }
    routeNodeMarkers.forEach((marker) => map.removeLayer(marker));
    routeNodeMarkers = [];
}

function buildCoordinateSegments(rawCoords = []) {
    const segments = [];
    let segment = [];

    rawCoords.forEach((rawCoords) => {
        const coords = normalizeMapCoords(rawCoords);
        if (coords) {
            segment.push(coords);
            return;
        }
        if (segment.length) segments.push(segment);
        segment = [];
    });
    if (segment.length) segments.push(segment);
    return segments;
}

function drawBackgroundRouteLine(routeSegments) {
    if (!map) return;
    if (backgroundRoutePolyline) {
        map.removeLayer(backgroundRoutePolyline);
        backgroundRoutePolyline = null;
    }
    if (!routeSegments.length) return;

    const latLngs =
        routeSegments.length === 1 ? routeSegments[0] : routeSegments;
    backgroundRoutePolyline = L.polyline(latLngs, {
        pane: "finalRoutePane",
        color: "#a78bfa",
        weight: 5,
        opacity: 0.55,
        dashArray: "6, 8",
        lineJoin: "round",
    }).addTo(map);
}

function drawRouteLine(routeSegments) {
    if (!map) return;
    if (activeRoutePolyline) {
        map.removeLayer(activeRoutePolyline);
        activeRoutePolyline = null;
    }
    if (!routeSegments.length) return;

    const latLngs =
        routeSegments.length === 1 ? routeSegments[0] : routeSegments;
    activeRoutePolyline = L.polyline(latLngs, {
        pane: "finalRoutePane",
        color: SEARCH_COLORS.route,
        weight: 6,
        opacity: 0.95,
        lineJoin: "round",
    }).addTo(map);
}

function fitMapToRouteSegments(routeSegments) {
    if (!map) return;
    const coords = routeSegments.flat();
    if (coords.length >= 2) {
        map.fitBounds(L.latLngBounds(coords), { padding: [46, 46] });
    } else if (coords.length === 1) {
        map.setView(coords[0], 16);
    }
}

function combineSearchTraces(segments, algorithm) {
    const tracedSegments = segments.filter(
        (segment) => segment.result.search_trace?.steps?.length,
    );
    if (!tracedSegments.length) return null;

    const steps = [];
    const visitedOrder = [];
    const nodeCoords = {};
    const routeSegments = [];
    tracedSegments.forEach((segment, segmentIndex) => {
        const trace = segment.result.search_trace;
        mergeValidNodeCoords(nodeCoords, trace.node_coords || {});
        mergePathNodeCoords(
            nodeCoords,
            segment.result.path_nodes,
            segment.result.path_coords,
        );
        routeSegments.push({
            path_nodes: Array.isArray(segment.result.path_nodes)
                ? segment.result.path_nodes
                : [],
        });
        (trace.visited_order || []).forEach((nodeId) => visitedOrder.push(nodeId));
        (trace.steps || []).forEach((step) => {
            steps.push({
                ...step,
                legIndex: segmentIndex + 1,
                legTotal: segments.length,
                routeStart: segment.start,
                routeGoal: segment.goal,
            });
        });
    });

    mergeEdgeNodeCoords(nodeCoords, edgesData);
    fullRoadNodeCoords.forEach((coords, nodeId) => {
        if (!nodeCoords[nodeId]) nodeCoords[nodeId] = coords;
    });

    return {
        algorithm: ALGORITHM_SPECS[algorithm]?.label || algorithm,
        frontier_kind:
            tracedSegments[0].result.search_trace.frontier_kind || "frontier",
        visited_order: visitedOrder,
        steps,
        node_coords: nodeCoords,
        route_segments: routeSegments,
    };
}

function mergeValidNodeCoords(target, source) {
    Object.entries(source || {}).forEach(([nodeId, rawCoords]) => {
        const coords = normalizeMapCoords(rawCoords);
        if (coords) target[normalizeNodeCoordinateKey(nodeId)] = coords;
    });
}

function mergePathNodeCoords(target, pathNodes = [], pathCoords = []) {
    if ((pathNodes?.length || 0) !== (pathCoords?.length || 0)) return;
    const count = Math.min(pathNodes?.length || 0, pathCoords?.length || 0);
    for (let index = 0; index < count; index += 1) {
        const coords = normalizeMapCoords(pathCoords[index]);
        if (coords) target[normalizeNodeCoordinateKey(pathNodes[index])] = coords;
    }
}

function mergeEdgeNodeCoords(target, edges = []) {
    edges.forEach((edge) => {
        const [sourceId, targetId] = String(edge.edge_id || "").split("_");
        const sourceCoords = normalizeMapCoords([edge.u_lat, edge.u_lng]);
        const targetCoords = normalizeMapCoords([edge.v_lat, edge.v_lng]);
        const sourceKey = normalizeNodeCoordinateKey(sourceId);
        const targetKey = normalizeNodeCoordinateKey(targetId);
        if (sourceId && sourceCoords && !target[sourceKey])
            target[sourceKey] = sourceCoords;
        if (targetId && targetCoords && !target[targetKey])
            target[targetKey] = targetCoords;
    });
}

function normalizeNodeCoordinateKey(nodeId) {
    const rawNodeId = String(nodeId ?? "").trim();
    const decimalIntegerMatch = rawNodeId.match(/^(\d+)\.0+$/);
    return decimalIntegerMatch ? decimalIntegerMatch[1] : rawNodeId;
}

function normalizeEdgeId(edgeId) {
    const [sourceId, targetId, ...rest] = String(edgeId ?? "").split("_");
    if (!sourceId || !targetId || rest.length) return String(edgeId ?? "");
    return `${normalizeNodeCoordinateKey(sourceId)}_${normalizeNodeCoordinateKey(targetId)}`;
}

function normalizeMapCoords(rawCoords) {
    if (!Array.isArray(rawCoords) || rawCoords.length < 2) return null;
    let latitude = Number(rawCoords[0]);
    let longitude = Number(rawCoords[1]);
    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return null;

    if (Math.abs(latitude) > 90 && Math.abs(longitude) <= 90) {
        [latitude, longitude] = [longitude, latitude];
    }
    if (Math.abs(latitude) > 90 || Math.abs(longitude) > 180) return null;
    return [latitude, longitude];
}

function stopSearchAnimation() {
    if (searchAnimationTimer) {
        clearInterval(searchAnimationTimer);
        searchAnimationTimer = null;
    }
    setText("btnPlaySearch", "▶ Phát");
}

function clearSearchVisualization() {
    stopSearchAnimation();
    searchVisitedLayer?.clearLayers();
    searchFrontierLayer?.clearLayers();
    searchCurrentLayer?.clearLayers();
    searchVisualizationData = null;
    searchStepIndex = 0;
    const panel = byId("searchVisualizationPanel");
    if (panel) {
        panel.hidden = true;
        panel.classList.remove("is-collapsed");
    }
    const playbackDock = byId("searchPlaybackDock");
    if (playbackDock) playbackDock.hidden = true;
}

function toggleSearchTraceCollapse() {
    const panel = byId("searchVisualizationPanel");
    if (!panel) return;
    const isCollapsed = panel.classList.toggle("is-collapsed");
    const btn = byId("btnToggleSearchTrace");
    if (btn) btn.textContent = isCollapsed ? "▸" : "▾";
}

async function startSearchVisualization(trace) {
    if (!trace?.steps?.length) {
        clearSearchVisualization();
        return;
    }
    stopSearchAnimation();
    searchVisualizationData = trace;
    searchStepIndex = 0;
    byId("searchVisualizationPanel").hidden = false;
    byId("searchPlaybackDock").hidden = false;

    await ensureTraceCoordinates(trace, getMissingTraceNodeIds(trace));
    fitMapToRouteSegments(
        buildCoordinateSegments(getAllTraceRouteCoordinates(trace)),
    );
    renderSearchStep(0);
}

function getMissingTraceNodeIds(trace) {
    const nodeIds = new Set(trace.visited_order || []);
    (trace.steps || []).forEach((step) => {
        if (step.current_node !== null && step.current_node !== undefined)
            nodeIds.add(step.current_node);
        (step.frontier || []).forEach((item) => {
            if (item?.node_id !== null && item?.node_id !== undefined)
                nodeIds.add(item.node_id);
        });
    });
    (trace.route_segments || []).forEach((segment) => {
        (segment.path_nodes || []).forEach((nodeId) => nodeIds.add(nodeId));
    });
    return Array.from(nodeIds).filter(
        (nodeId) =>
            !normalizeMapCoords(
                trace.node_coords?.[normalizeNodeCoordinateKey(nodeId)],
            ),
    );
}

function appendRouteNodes(target, nodes) {
    nodes.forEach((nodeId) => {
        if (
            normalizeNodeCoordinateKey(target[target.length - 1]) !==
            normalizeNodeCoordinateKey(nodeId)
        ) {
            target.push(nodeId);
        }
    });
}

function getAllTraceRouteNodes(trace) {
    const nodes = [];
    (trace.route_segments || []).forEach((segment) => {
        appendRouteNodes(nodes, segment.path_nodes || []);
    });
    return nodes;
}

function getRouteNodesAtSearchStep(trace, stepIndex) {
    const routeSegments = trace.route_segments || [];
    const traceSteps = trace.steps || [];
    if (!routeSegments.length || !traceSteps.length) return [];

    const safeStepIndex = Math.max(
        0,
        Math.min(
            Number(stepIndex) || 0,
            traceSteps.length - 1,
        ),
    );
    const activeStep = traceSteps[safeStepIndex];
    const activeSegmentIndex = Math.max(
        0,
        Math.min(
            Number(activeStep?.legIndex || 1) - 1,
            routeSegments.length - 1,
        ),
    );
    const routeNodes = [];
    routeSegments.forEach((segment, segmentIndex) => {
        const pathNodes = segment.path_nodes || [];
        if (segmentIndex < activeSegmentIndex) {
            appendRouteNodes(routeNodes, pathNodes);
            return;
        }
        if (segmentIndex !== activeSegmentIndex) return;

        const furthestExpandedPathIndex = traceSteps
            .slice(0, safeStepIndex + 1)
            .filter(
                (candidateStep) =>
                    Number(candidateStep?.legIndex || 1) ===
                    activeSegmentIndex + 1,
            )
            .reduce((furthestIndex, candidateStep) => {
                const pathIndex = pathNodes
                    .map(normalizeNodeCoordinateKey)
                    .lastIndexOf(
                        normalizeNodeCoordinateKey(candidateStep.current_node),
                    );
                return Math.max(furthestIndex, pathIndex);
            }, -1);
        if (furthestExpandedPathIndex >= 0) {
            appendRouteNodes(
                routeNodes,
                pathNodes.slice(0, furthestExpandedPathIndex + 1),
            );
        }
    });
    return routeNodes;
}

function getAllTraceRouteCoordinates(trace) {
    const nodeCoords = trace.node_coords || {};
    return getAllTraceRouteNodes(trace).map(
        (nodeId) => nodeCoords[normalizeNodeCoordinateKey(nodeId)],
    );
}

function drawRouteProgress(trace, stepIndex) {
    const routeNodes = getRouteNodesAtSearchStep(trace, stepIndex);
    const routeCoords = routeNodes.map(
        (nodeId) => trace.node_coords?.[normalizeNodeCoordinateKey(nodeId)],
    );
    drawRouteLine(buildCoordinateSegments(routeCoords));
    return {
        revealedNodeCount: routeNodes.length,
        totalNodeCount: getAllTraceRouteNodes(trace).length,
        currentNodeId: routeNodes.at(-1) ?? null,
        routeNodes,
    };
}

function setMapTraceLoadingStatus(missingCount) {
    const status = byId("vizMapStatus");
    if (!status) return;
    status.classList.remove("is-warning");
    status.textContent = `Đang bổ sung tọa độ cho ${missingCount.toLocaleString("vi-VN")} node tìm kiếm từ dữ liệu cạnh…`;
}

async function ensureTraceCoordinates(trace, missingNodeIds) {
    copyIndexedCoordsToTrace(trace, missingNodeIds);
    let unresolved = getMissingTraceNodeIds(trace);
    if (!unresolved.length || allEdgeCoordinatesLoaded) {
        estimateMissingRouteCoordinates(trace);
        return;
    }

    setMapTraceLoadingStatus(unresolved.length);

    try {
        await loadAllEdgeCoordinates();
        copyIndexedCoordsToTrace(trace, unresolved);
    } catch (error) {
        console.warn("Unable to load all road-node coordinates:", error);
        setOperationStatus(
            `Không thể tải đủ tọa độ mô phỏng: ${error.message}`,
            true,
        );
    }
    estimateMissingRouteCoordinates(trace);
}

function copyIndexedCoordsToTrace(trace, nodeIds) {
    trace.node_coords ||= {};
    nodeIds.forEach((nodeId) => {
        const nodeKey = normalizeNodeCoordinateKey(nodeId);
        const coords = fullRoadNodeCoords.get(nodeKey);
        if (coords) trace.node_coords[nodeKey] = coords;
    });
}

function estimateMissingRouteCoordinates(trace) {
    trace.node_coords ||= {};
    (trace.route_segments || []).forEach((segment) => {
        const pathNodes = segment.path_nodes || [];
        for (let index = 0; index < pathNodes.length; index += 1) {
            const nodeKey = normalizeNodeCoordinateKey(pathNodes[index]);
            if (normalizeMapCoords(trace.node_coords[nodeKey]))
                continue;

            let previousIndex = index - 1;
            while (
                previousIndex >= 0 &&
                !normalizeMapCoords(
                    trace.node_coords[
                        normalizeNodeCoordinateKey(pathNodes[previousIndex])
                    ],
                )
            ) {
                previousIndex -= 1;
            }
            let nextIndex = index + 1;
            while (
                nextIndex < pathNodes.length &&
                !normalizeMapCoords(
                    trace.node_coords[
                        normalizeNodeCoordinateKey(pathNodes[nextIndex])
                    ],
                )
            ) {
                nextIndex += 1;
            }
            if (previousIndex < 0 || nextIndex >= pathNodes.length) continue;

            const previousCoords = normalizeMapCoords(
                trace.node_coords[
                    normalizeNodeCoordinateKey(pathNodes[previousIndex])
                ],
            );
            const nextCoords = normalizeMapCoords(
                trace.node_coords[
                    normalizeNodeCoordinateKey(pathNodes[nextIndex])
                ],
            );
            const ratio =
                (index - previousIndex) / (nextIndex - previousIndex);
            trace.node_coords[nodeKey] = [
                previousCoords[0] + (nextCoords[0] - previousCoords[0]) * ratio,
                previousCoords[1] + (nextCoords[1] - previousCoords[1]) * ratio,
            ];
        }
    });
}

async function loadAllEdgeCoordinates() {
    if (allEdgeCoordinatesLoaded) return;
    if (fullCoordinateLoadPromise) return fullCoordinateLoadPromise;

    const limit = Math.max(1, graphEdgeCount || edgesData.length || 2000);
    fullCoordinateLoadPromise = fetchJson(`${API_BASE}/edges?limit=${limit}`)
        .then((allEdges) => {
            if (!Array.isArray(allEdges))
                throw new Error("API edges không trả về danh sách hợp lệ.");
            allEdges.forEach((edge) => indexEdgeNodeCoords(fullRoadNodeCoords, edge));
            allEdgeCoordinatesLoaded =
                allEdges.length >= limit || allEdges.length >= graphEdgeCount;
        })
        .finally(() => {
            fullCoordinateLoadPromise = null;
        });
    return fullCoordinateLoadPromise;
}

function getSearchMapMode() {
    return byId("mapTraceMode")?.value === "full_trace"
        ? "full_trace"
        : "route_frontier";
}

function onMapTraceModeChange() {
    if (searchVisualizationData) renderSearchStep(searchStepIndex);
}

function updateSearchMapModeLabels(mapMode) {
    const isFullTrace = mapMode === "full_trace";
    setText(
        "vizVisitedLegend",
        isFullTrace ? "🟡 Đã duyệt" : "🟡 Tuyến đã hiện",
    );
    setText(
        "vizCurrentLegend",
        isFullTrace ? "🟠 Đang mở" : "🟠 Trên tuyến cuối",
    );
    setText(
        "followSearchLabel",
        isFullTrace
            ? "Tự động đưa node đang mở vào giữa bản đồ"
            : "Tự động đưa node thuộc tuyến cuối vào giữa bản đồ",
    );
}

function renderSearchStep(stepIndex) {
    if (!searchVisualizationData?.steps?.length) return;
    const steps = searchVisualizationData.steps;
    const safeIndex = Math.max(0, Math.min(stepIndex, steps.length - 1));
    searchStepIndex = safeIndex;
    const step = steps[safeIndex];
    const expandedOrder = searchVisualizationData.visited_order.slice(
        0,
        safeIndex + 1,
    );
    const visitedOrder = expandedOrder.filter(
        (nodeId) =>
            normalizeNodeCoordinateKey(nodeId) !==
            normalizeNodeCoordinateKey(step.current_node),
    );
    const rawFrontier = Array.isArray(step.frontier) ? step.frontier : [];
    const frontier = rawFrontier.filter(
        (item) =>
            normalizeNodeCoordinateKey(item.node_id) !==
            normalizeNodeCoordinateKey(step.current_node),
    );
    const currentWasInFrontier = rawFrontier.some(
        (item) => String(item.node_id) === String(step.current_node),
    );
    const fullFrontierCount = Math.max(
        0,
        Number(step.frontier_size ?? rawFrontier.length) -
        (currentWasInFrontier ? 1 : 0),
    );
    const nodeCoords = searchVisualizationData.node_coords || {};
    const routeProgress = drawRouteProgress(
        searchVisualizationData,
        safeIndex,
    );
    const mapMode = getSearchMapMode();
    const isFullTrace = mapMode === "full_trace";
    updateSearchMapModeLabels(mapMode);
    const routeVisitedOrder = routeProgress.routeNodes.slice(0, -1);
    const mapVisitedOrder = isFullTrace ? visitedOrder : routeVisitedOrder;
    const mapCurrentNodeId = isFullTrace
        ? step.current_node
        : routeProgress.currentNodeId;
    let visitedMarkersDrawn = 0;
    let frontierMarkersDrawn = 0;

    searchVisitedLayer?.clearLayers();
    searchFrontierLayer?.clearLayers();
    searchCurrentLayer?.clearLayers();

    const prevNodeId = safeIndex > 0 ? steps[safeIndex - 1]?.current_node : null;
    const nextNodeId = safeIndex < steps.length - 1 ? steps[safeIndex + 1]?.current_node : null;

    const currentCoords = normalizeMapCoords(
        nodeCoords[normalizeNodeCoordinateKey(mapCurrentNodeId)],
    );

    // -------------------------------------------------------------
    // 1. Cạnh đồ thị đã khám phá trong cây tìm kiếm (Explored Search Tree Edges)
    // -------------------------------------------------------------
    if (isFullTrace && mapVisitedOrder.length > 0) {
        const visitedSet = new Set(
            mapVisitedOrder.map(normalizeNodeCoordinateKey),
        );
        if (mapCurrentNodeId) visitedSet.add(normalizeNodeCoordinateKey(mapCurrentNodeId));

        const drawnEdges = new Set();
        const exploredTreeEdges = [];

        visitedSet.forEach((uKey) => {
            const neighbors = roadAdjacency.get(uKey);
            if (!neighbors) return;
            const coordsU = normalizeMapCoords(nodeCoords[uKey]);
            if (!coordsU) return;

            neighbors.forEach((vKey) => {
                if (!visitedSet.has(vKey)) return;
                const edgeKey = uKey < vKey ? `${uKey}__${vKey}` : `${vKey}__${uKey}`;
                if (drawnEdges.has(edgeKey)) return;
                drawnEdges.add(edgeKey);

                const coordsV = normalizeMapCoords(nodeCoords[vKey]);
                if (!coordsV) return;
                exploredTreeEdges.push([coordsU, coordsV]);
            });
        });

        if (exploredTreeEdges.length > 0) {
            // Lớp hào quang cho các cạnh cây tìm kiếm đã duyệt
            L.polyline(exploredTreeEdges, {
                pane: "searchVisitedPane",
                color: "#0284c7",
                weight: 6.5,
                opacity: 0.45,
                lineCap: "round",
                lineJoin: "round",
                interactive: false,
            }).addTo(searchVisitedLayer);

            // Lõi cạnh cây tìm kiếm đã duyệt
            L.polyline(exploredTreeEdges, {
                pane: "searchVisitedPane",
                color: "#38bdf8",
                weight: 3.5,
                opacity: 0.92,
                lineCap: "round",
                lineJoin: "round",
                interactive: false,
            }).addTo(searchVisitedLayer);
        }
    }

    // -------------------------------------------------------------
    // 2. Nhánh mở rộng từ Current Node sang các Frontier kề cận
    // -------------------------------------------------------------
    if (currentCoords && mapCurrentNodeId) {
        const currKey = normalizeNodeCoordinateKey(mapCurrentNodeId);
        const currNeighbors = roadAdjacency.get(currKey) || new Set();

        frontier.forEach((item) => {
            const fKey = normalizeNodeCoordinateKey(item.node_id);
            // Chỉ xét nhánh nếu ngã rẽ này là nút láng giềng kề trực tiếp trên đồ thị
            if (!currNeighbors.has(fKey)) return;

            const fCoords = normalizeMapCoords(nodeCoords[fKey]);
            if (!fCoords) return;

            const isNext = String(item.node_id) === String(nextNodeId);

            if (isNext) {
                // Cạnh mở rộng bước tiếp theo được thuật toán lựa chọn (Next Expansion Edge)
                L.polyline([currentCoords, fCoords], {
                    pane: "searchFrontierPane",
                    color: "#10b981",
                    weight: 4.5,
                    opacity: 0.95,
                    lineCap: "round",
                    lineJoin: "round",
                    interactive: false,
                }).addTo(searchFrontierLayer);
            } else {
                // Các cạnh nối sang các ứng viên Frontier kề cận khác
                L.polyline([currentCoords, fCoords], {
                    pane: "searchFrontierPane",
                    color: "#06b6d4",
                    weight: 2.8,
                    opacity: 0.8,
                    dashArray: "3, 5",
                    lineCap: "round",
                    interactive: false,
                }).addTo(searchFrontierLayer);
            }
        });
    }

    // -------------------------------------------------------------
    // 1. Vẽ các nút đã duyệt (Visited Nodes trên mạng đường)
    // -------------------------------------------------------------
    mapVisitedOrder.slice(-MAX_MAP_TRACE_NODES).forEach((nodeId) => {
        const coords = normalizeMapCoords(
            nodeCoords[normalizeNodeCoordinateKey(nodeId)],
        );
        if (!coords) return;
        L.circleMarker(coords, {
            pane: "searchVisitedPane",
            radius: 5,
            color: SEARCH_COLORS.visited,
            fillColor: SEARCH_COLORS.visited,
            fillOpacity: 0.7,
            opacity: 0.85,
            weight: 1.5,
        })
            .bindTooltip(getNodeLabel(nodeId))
            .addTo(searchVisitedLayer);
        visitedMarkersDrawn += 1;
    });

    // -------------------------------------------------------------
    // 2. Mở rộng các ngã rẽ Frontier (Frontier Nodes trên mạng đường)
    // -------------------------------------------------------------
    let nextCandidateCoords = null;

    frontier.slice(0, MAX_MAP_TRACE_NODES).forEach((item) => {
        const coords = normalizeMapCoords(
            nodeCoords[normalizeNodeCoordinateKey(item.node_id)],
        );
        if (!coords) return;
        const isNextStepTarget = String(item.node_id) === String(nextNodeId);

        if (isNextStepTarget) {
            nextCandidateCoords = coords;
        }

        L.circleMarker(coords, {
            pane: "searchFrontierPane",
            radius: isNextStepTarget ? 8.5 : 6.5,
            color: isNextStepTarget ? "#22c55e" : SEARCH_COLORS.frontier,
            fillColor: isNextStepTarget ? "#4ade80" : SEARCH_COLORS.frontier,
            fillOpacity: isNextStepTarget ? 0.95 : 0.75,
            opacity: 1,
            weight: isNextStepTarget ? 2.8 : 2,
        })
            .bindTooltip(
                isNextStepTarget
                    ? `👉 BƯỚC TIẾP THEO SẼ VÀO ĐÂY: ${formatFrontierItem(item)}`
                    : formatFrontierItem(item),
            )
            .addTo(searchFrontierLayer);
        frontierMarkersDrawn += 1;
    });

    // Marker đặc biệt cho Nút được chọn tiếp theo (Next Candidate Node)
    if (nextCandidateCoords && nextNodeId) {
        const nextIcon = L.divIcon({
            className: "next-candidate-marker",
            html: `<div class="candidate-ring"></div><span class="candidate-label">👉 Tiếp theo: ${escapeHtml(nextNodeId)}</span>`,
            iconSize: [36, 36],
            iconAnchor: [18, 18],
        });
        L.marker(nextCandidateCoords, {
            icon: nextIcon,
            pane: "searchFrontierPane",
            interactive: false,
            keyboard: false,
            zIndexOffset: 4500,
        }).addTo(searchFrontierLayer);
    }

    // -------------------------------------------------------------
    // 3. Highlight Node B đang xét hiện tại (Current Node)
    // -------------------------------------------------------------
    if (currentCoords) {
        L.circleMarker(currentCoords, {
            pane: "searchCurrentPane",
            radius: 15,
            color: SEARCH_COLORS.current,
            fillColor: SEARCH_COLORS.current,
            fillOpacity: 0.15,
            opacity: 0.7,
            weight: 2,
        }).addTo(searchCurrentLayer);
        L.circleMarker(currentCoords, {
            pane: "searchCurrentPane",
            radius: 9,
            color: SEARCH_COLORS.current,
            fillColor: SEARCH_COLORS.current,
            fillOpacity: 0.9,
            opacity: 1,
            weight: 3,
        })
            .bindTooltip(
                isFullTrace
                    ? `📍 Đang xét: ${getNodeLabel(mapCurrentNodeId)}${nextNodeId ? ` ➔ Tiếp theo: ${getNodeLabel(nextNodeId)}` : ""}`
                    : `Tuyến đã hiện: ${getNodeLabel(mapCurrentNodeId)}`,
                {
                    permanent: true,
                    direction: "top",
                },
            )
            .addTo(searchCurrentLayer);
        const currentIcon = L.divIcon({
            className: "search-current-marker",
            html: `<div class="beacon-pulse-ring"></div><span class="current-marker-label">📍 Node ${escapeHtml(mapCurrentNodeId)}</span><span class="current-marker-core">●</span>`,
            iconSize: [36, 36],
            iconAnchor: [18, 18],
        });
        L.marker(currentCoords, {
            icon: currentIcon,
            pane: "markerPane",
            interactive: false,
            keyboard: false,
            zIndexOffset: 5000,
        }).addTo(searchCurrentLayer);
        focusCurrentSearchNode(
            currentCoords,
            safeIndex,
            isFullTrace || Boolean(routeProgress.currentNodeId),
        );
    }

    updateMapTraceStatus(
        step,
        currentCoords,
        visitedMarkersDrawn,
        frontierMarkersDrawn,
        visitedOrder.length,
        fullFrontierCount,
        routeProgress,
        mapMode,
        mapCurrentNodeId,
    );

    setText("vizAlgorithm", searchVisualizationData.algorithm);
    setText("vizStep", `Bước ${safeIndex + 1} / ${steps.length}`);
    setText("vizCurrentNode", step.current_node ?? "—");
    setText("vizVisitedCount", visitedOrder.length.toLocaleString("vi-VN"));
    setText("vizFrontierCount", fullFrontierCount.toLocaleString("vi-VN"));
    setText(
        "vizFrontierLabel",
        frontierKindLabel(searchVisualizationData.frontier_kind),
    );
    renderTraceTokens(
        "vizVisitedList",
        visitedOrder.slice(-MAX_TRACE_TOKENS).map(String),
        "visited",
    );
    renderTraceTokens(
        "vizFrontierList",
        frontier.slice(0, MAX_TRACE_TOKENS).map(formatFrontierItem),
        "frontier",
    );

    const legText =
        step.legTotal > 1
            ? `Chặng ${step.legIndex}/${step.legTotal} (${step.routeStart} → ${step.routeGoal}). `
            : "";
    const transitionText = prevNodeId && mapCurrentNodeId && String(prevNodeId) !== String(mapCurrentNodeId)
        ? `Đã đi từ [${prevNodeId}] ➔ [${mapCurrentNodeId}]. `
        : `Bắt đầu từ [${mapCurrentNodeId}]. `;
    const decisionText = nextNodeId
        ? `Từ [${mapCurrentNodeId}], mở rộng ${frontier.length} nhánh Frontier và quyết định di chuyển tiếp vào Node [${nextNodeId}].`
        : "Đã hoàn thành duyệt / tìm thấy đích!";
    setText("vizExplanation", `${legText}${transitionText}${decisionText}`);
}

function updateMapTraceStatus(
    step,
    currentCoords,
    visitedDrawn,
    frontierDrawn,
    visitedTotal,
    frontierTotal,
    routeProgress,
    mapMode,
    mapCurrentNodeId,
) {
    const status = byId("vizMapStatus");
    if (!status) return;
    const missingCurrent = !currentCoords;
    status.classList.toggle("is-warning", missingCurrent);
    const isFullTrace = mapMode === "full_trace";
    const routeProgressText = ` Tuyến đang hiện dần ${routeProgress.revealedNodeCount}/${routeProgress.totalNodeCount} node.`;
    if (missingCurrent) {
        status.textContent = isFullTrace
            ? `Không có tọa độ cho node đang mở ${step.current_node}.${routeProgressText}`
            : `Chưa có node nào thuộc tuyến cuối để đặt marker ở bước này.${routeProgressText}`;
        return;
    }
    status.textContent = isFullTrace
        ? `Map đã vẽ ${visitedDrawn}/${visitedTotal} visited, ${frontierDrawn}/${frontierTotal} frontier và marker cam cho node ${mapCurrentNodeId}.${routeProgressText}`
        : `Map đã vẽ ${visitedDrawn} node thuộc tuyến cuối, ${frontierDrawn}/${frontierTotal} frontier và marker cam cho node ${mapCurrentNodeId}.${routeProgressText}`;
}

function focusCurrentSearchNode(coords, stepIndex, isOnFinalRoute) {
    if (!map || !isOnFinalRoute || !byId("followSearchNode")?.checked) return;
    const targetZoom = Math.max(map.getZoom(), 15);
    map.setView(coords, targetZoom, {
        animate: stepIndex > 0,
        duration: 0.22,
    });
}

function renderTraceTokens(containerId, values, cssClass) {
    const container = byId(containerId);
    container.replaceChildren();
    if (!values.length) {
        container.textContent = "—";
        return;
    }
    values.forEach((value) => {
        const token = document.createElement("span");
        token.className = `search-viz-token ${cssClass}`;
        token.textContent = value;
        container.append(token);
    });
}

function formatFrontierItem(item) {
    if (!item || typeof item !== "object") return String(item ?? "—");
    const costs = ["g", "h", "f", "cost", "priority"]
        .filter((key) => item[key] !== undefined)
        .map((key) => `${key}=${Number(item[key]).toFixed(2)}`);
    const selection = item.selected ? "✓ được chọn" : null;
    return [getNodeLabel(item.node_id ?? "—"), ...costs, selection]
        .filter(Boolean)
        .join(" · ");
}

function frontierKindLabel(kind) {
    const labels = {
        queue: "Frontier (queue)",
        stack: "Frontier (stack)",
        priority_queue: "Open list (priority queue)",
        candidates: "Ứng viên",
    };
    return labels[kind] || "Frontier";
}

function visitOrderLabel(method) {
    const labels = {
        input: "Theo thứ tự nhập",
        nearest_neighbor: "Nearest Neighbor (xấp xỉ)",
        held_karp: "Held–Karp (tối ưu)",
        genetic_algorithm: "Genetic Algorithm (xấp xỉ)",
        simulated_annealing: "Simulated Annealing (xấp xỉ)",
    };
    return labels[method] || method;
}

function previousSearchStep() {
    if (!searchVisualizationData) return;
    stopSearchAnimation();
    renderSearchStep(searchStepIndex - 1);
}

function nextSearchStep() {
    if (!searchVisualizationData) return;
    stopSearchAnimation();
    renderSearchStep(searchStepIndex + 1);
}

function toggleSearchAnimation() {
    if (!searchVisualizationData) return;
    if (searchAnimationTimer) {
        stopSearchAnimation();
        return;
    }
    playSearchAnimation();
}

function playSearchAnimation() {
    if (!searchVisualizationData || searchAnimationTimer) return;
    if (searchStepIndex >= searchVisualizationData.steps.length - 1)
        renderSearchStep(0);
    setText("btnPlaySearch", "⏸ Tạm dừng");
    const speed = Number.parseInt(byId("searchSpeed")?.value || "350", 10);
    searchAnimationTimer = window.setInterval(() => {
        if (
            !searchVisualizationData ||
            searchStepIndex >= searchVisualizationData.steps.length - 1
        ) {
            stopSearchAnimation();
            return;
        }
        renderSearchStep(searchStepIndex + 1);
    }, speed);
}

async function compareAlgorithms() {
    let input;
    try {
        input = getPlannerInput();
    } catch (error) {
        setOperationStatus(error.message, true);
        showToast(error.message, true);
        return;
    }

    const algorithms = [
        "bfs",
        "dfs",
        "ucs",
        "astar",
        "dijkstra",
        "hill_climbing",
    ];
    const nodeOrder = [input.startNodeId, ...input.waypointIds, input.goalNodeId];
    const results = [];
    setButtonBusy(
        "btnCompareAlgorithms",
        true,
        "Đang so sánh…",
        "So sánh 6 thuật toán",
    );
    byId("btnCalculateRoute").disabled = true;
    byId("comparisonPanel").hidden = true;

    try {
        for (let index = 0; index < algorithms.length; index += 1) {
            const algorithm = algorithms[index];
            setOperationStatus(
                `Đang chạy ${ALGORITHM_SPECS[algorithm].label} (${index + 1}/${algorithms.length})…`,
            );
            try {
                const segments = await runOrderedRoute(nodeOrder, algorithm);
                results.push({
                    algorithm,
                    aggregate: aggregateSegments(segments, nodeOrder),
                    error: null,
                });
            } catch (error) {
                results.push({ algorithm, aggregate: null, error: error.message });
            }
        }
        renderComparison(results, input);
        setOperationStatus("Đã hoàn tất bảng so sánh trên cùng đầu vào.");
        showToast("Đã so sánh xong 6 thuật toán.");
    } finally {
        setButtonBusy(
            "btnCompareAlgorithms",
            false,
            "Đang so sánh…",
            "So sánh 6 thuật toán",
        );
        byId("btnCalculateRoute").disabled = false;
    }
}

function renderComparison(results, input) {
    const body = byId("comparisonBody");
    body.replaceChildren();
    const successful = results.filter((item) => item.aggregate);
    const bestScore = successful.length
        ? Math.min(
            ...successful.map((item) =>
                scoreAggregate(item.aggregate, input.criterion),
            ),
        )
        : null;

    results.forEach((item) => {
        const row = document.createElement("tr");
        if (
            item.aggregate &&
            scoreAggregate(item.aggregate, input.criterion) === bestScore
        ) {
            row.classList.add("best-row");
        }
        const spec = ALGORITHM_SPECS[item.algorithm];
        const cells = item.aggregate
            ? [
                spec.label,
                item.aggregate.totalCost.toFixed(2),
                formatDistance(item.aggregate.totalDistance),
                formatDuration(item.aggregate.totalTravelTime),
                item.aggregate.totalHops.toLocaleString("vi-VN"),
                item.aggregate.totalExpanded.toLocaleString("vi-VN"),
                `${item.aggregate.totalProcessingTime.toFixed(2)} ms`,
                spec.optimality,
            ]
            : [
                spec.label,
                "Không có route",
                "—",
                "—",
                "—",
                "—",
                "—",
                item.error || "Lỗi",
            ];
        cells.forEach((value) => {
            const cell = document.createElement("td");
            cell.textContent = value;
            row.append(cell);
        });
        body.append(row);
    });

    const modeNote =
        input.visitOrderMode !== "input" && input.waypointIds.length > 1
            ? "Bảng so sánh giữ nguyên thứ tự điểm đã nhập để mọi thuật toán nhận cùng điều kiện; không chạy tối ưu thứ tự."
            : "Mọi thuật toán nhận cùng start, destination và thứ tự điểm trung gian.";
    setText(
        "comparisonNote",
        `Hàng màu xanh có metric tốt nhất theo “${CRITERION_LABELS[input.criterion]}”, nhưng mỗi thuật toán vẫn có mục tiêu nội tại khác nhau. Thời gian có dấu * là ước tính frontend. ${modeNote}`,
    );
    byId("comparisonPanel").hidden = false;
    byId("comparisonPanel").scrollIntoView({
        behavior: "smooth",
        block: "nearest",
    });
}

function closeComparison() {
    byId("comparisonPanel").hidden = true;
}

function scoreAggregate(aggregate, criterion) {
    if (criterion === "distance") return aggregate.totalDistance;
    if (criterion === "time") return aggregate.totalTravelTime;
    if (criterion === "hops") return aggregate.totalHops;
    return aggregate.totalCost;
}

function renderHospitalsOnMap() {
    if (!map) return;
    hospitalMarkers.forEach((markers) =>
        markers.forEach((marker) => map.removeLayer(marker)),
    );
    hospitalMarkers = new Map();

    poisData.forEach((poi) => {
        const type = String(poi.type || poi.category || "Cơ sở y tế");
        const isMedical = Boolean(poi.is_hospital);
        
        let marker;
        if (isMedical) {
            const isHospital =
                type.toLowerCase().includes("hospital") ||
                type.toLowerCase().includes("bệnh viện");
            const emoji = isHospital ? "🏥" : "✚";
            const icon = showPOIIcons
                ? L.divIcon({
                      className: `custom-div-icon ${isHospital ? "icon-hospital" : "icon-clinic"}`,
                      html: `<span>${emoji}</span>`,
                      iconSize: [34, 34],
                      iconAnchor: [17, 17],
                  })
                : L.divIcon({
                      className: `poi-dot-icon ${isHospital ? "dot-hospital" : "dot-clinic"}`,
                      html: '<span class="poi-dot-inner"></span>',
                      iconSize: [14, 14],
                      iconAnchor: [7, 7],
                  });
            marker = L.marker([poi.lat, poi.lng], {
                icon,
                zIndexOffset: showPOIIcons ? 1000 : 800,
                title: poi.name || "Cơ sở y tế",
            });
            marker.bindPopup(`
                <div class="popup-content">
                    <strong>${emoji} ${escapeHtml(poi.name || "Cơ sở y tế")}</strong>
                    <span>Loại: ${escapeHtml(type)}</span>
                    <span>Road node: ${Number(poi.node_id)}</span>
                    <div style="display: flex; gap: 5px; margin-top: 6px;">
                        <button type="button" onclick="setDestination(${Number(poi.node_id)})">🎯 Chọn làm đích</button>
                        <button type="button" onclick="addWaypoint(${Number(poi.node_id)})" style="background: rgba(119, 135, 255, 0.2); border-color: rgba(119, 135, 255, 0.4);">➕ Thêm điểm ghé</button>
                    </div>
                </div>
            `);
        } else {
            // Không hiển thị POI thường nếu POI icon đang tắt (tùy chọn)
            if (!showPOIIcons) return;
            marker = L.circleMarker([poi.lat, poi.lng], {
                radius: 4,
                color: '#6b7280',
                fillColor: '#9ca3af',
                fillOpacity: 0.8,
                weight: 1,
            });
            marker.bindPopup(`
                <div class="popup-content">
                    <strong>📍 ${escapeHtml(poi.name || "POI")}</strong>
                    <span>Loại: ${escapeHtml(type)}</span>
                    <span>Road node: ${Number(poi.node_id)}</span>
                    <div style="display: flex; gap: 5px; margin-top: 6px;">
                        <button type="button" onclick="setDestination(${Number(poi.node_id)})">🎯 Chọn làm đích</button>
                        <button type="button" onclick="addWaypoint(${Number(poi.node_id)})" style="background: rgba(119, 135, 255, 0.2); border-color: rgba(119, 135, 255, 0.4);">➕ Thêm điểm ghé</button>
                    </div>
                </div>
            `);
        }
        marker.addTo(map);

        const markers = hospitalMarkers.get(Number(poi.node_id)) || [];
        markers.push(marker);
        hospitalMarkers.set(Number(poi.node_id), markers);
    });
}

function togglePOIIcons() {
    showPOIIcons = !showPOIIcons;
    updateToggleButton("btnTogglePOIIcon", showPOIIcons, "Hiển thị cơ sở y tế");
    renderHospitalsOnMap();
}

function renderEdgesOnMap() {
    if (!map) return;
    Object.values(edgePolylines).forEach((polyline) => map.removeLayer(polyline));
    edgePolylines = {};
    if (!showTraffic) return;

    const groups = { normal: [], heavy: [], severe: [] };
    edgesData.forEach((edge) => {
        const coords = [
            [edge.u_lat, edge.u_lng],
            [edge.v_lat, edge.v_lng],
        ];
        const level = Number(edge.congestion_level || 1);
        if (level >= 4) groups.severe.push(coords);
        else if (level === 3) groups.heavy.push(coords);
        else groups.normal.push(coords);
    });

    if (groups.normal.length) {
        edgePolylines.normal = L.polyline(groups.normal, {
            color: "#0284c7",
            weight: 2.5,
            opacity: 0.65,
            interactive: false,
        }).addTo(map);
    }
    if (groups.heavy.length) {
        edgePolylines.heavy = L.polyline(groups.heavy, {
            color: "#f59e0b",
            weight: 3.5,
            opacity: 0.85,
            interactive: false,
        }).addTo(map);
    }
    if (groups.severe.length) {
        edgePolylines.severe = L.polyline(groups.severe, {
            color: "#ef4444",
            weight: 4.5,
            opacity: 0.95,
            interactive: false,
        }).addTo(map);
    }
}

function toggleTrafficLayer() {
    showTraffic = !showTraffic;
    updateToggleButton("btnToggleTraffic", showTraffic, "Lớp mức độ ùn tắc");
    renderEdgesOnMap();
}

function toggleMapLegend() {
    const legend = byId("mapLegend");
    if (!legend) return;
    const isCollapsed = legend.classList.toggle("is-collapsed");
    const btn = byId("btnToggleLegend");
    if (btn) btn.textContent = isCollapsed ? "▸" : "▾";
}

function updateToggleButton(id, active, label) {
    const button = byId(id);
    if (!button) return;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
    button.replaceChildren();
    const labelSpan = document.createElement("span");
    labelSpan.textContent = label;
    const stateSpan = document.createElement("span");
    stateSpan.textContent = active ? "Bật" : "Tắt";
    button.append(labelSpan, stateSpan);
}

function updateAmbulanceDisplay(data) {
    if (!map) return;
    const lat = Number(data?.lat ?? 10.773);
    const lng = Number(data?.lng ?? 106.698);
    const mapped = data?.mapped_nearest_node || {};
    setText("gpsCodeDisplay", `GPS: (${lat.toFixed(5)}, ${lng.toFixed(5)})`);
    setText(
        "nearestDisplay",
        `Nút gần nhất: [${mapped.nearest_node_id ?? "—"}] ${mapped.nearest_node_name || "Nút đường"} · cách ${Number(mapped.distance_meters || 0).toFixed(1)} m`,
    );

    const icon = L.divIcon({
        className: "custom-div-icon icon-ambulance",
        html: "<span>🚑</span>",
        iconSize: [42, 42],
        iconAnchor: [21, 21],
    });
    if (!ambulanceMarker) {
        ambulanceMarker = L.marker([lat, lng], { icon, zIndexOffset: 2000 }).addTo(
            map,
        );
    } else {
        ambulanceMarker.setLatLng([lat, lng]);
    }
    ambulanceMarker.bindPopup(`
        <div class="popup-content">
            <strong>🚑 Xe cấp cứu đang trực</strong>
            <span>GPS: ${lat.toFixed(5)}, ${lng.toFixed(5)}</span>
            <span>Khớp node: ${escapeHtml(mapped.nearest_node_name || mapped.nearest_node_id || "—")}</span>
        </div>
    `);
    populateStartControls();
}

async function updateAmbulanceGPS(lat, lng) {
    setOperationStatus("Đang ánh xạ GPS sang nút đường gần nhất…");
    try {
        const data = await fetchJson(`${API_BASE}/ambulance/location`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ lat, lng }),
        });
        currentAmbulanceData = data.current_gps;
        routeRequestCache.clear();
        updateAmbulanceDisplay(currentAmbulanceData);
        setOperationStatus("Đã cập nhật vị trí xe cấp cứu.");
        showToast(`Đã cập nhật GPS (${lat.toFixed(4)}, ${lng.toFixed(4)}).`);
    } catch (error) {
        setOperationStatus(`Không thể cập nhật GPS: ${error.message}`, true);
        showToast("Không thể gửi tọa độ GPS tới backend.", true);
    }
}

function getDeviceLocation() {
    if (!navigator.geolocation) {
        showToast("Trình duyệt không hỗ trợ Geolocation.", true);
        return;
    }
    showToast("Đang lấy vị trí từ thiết bị…");
    navigator.geolocation.getCurrentPosition(
        (position) =>
            updateAmbulanceGPS(position.coords.latitude, position.coords.longitude),
        (error) => showToast(`Không thể lấy GPS thiết bị: ${error.message}`, true),
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 },
    );
}

function setDestination(nodeId) {
    const select = byId("selectHospital");
    if (!select) return;
    select.value = String(nodeId);
    onHospitalSelectChange();
    map?.closePopup();
    showToast(`Đã chọn ${getNodeLabel(Number(nodeId))} làm đích đến.`);
}

function onHospitalSelectChange() {
    const nodeId = Number.parseInt(byId("selectHospital")?.value, 10);
    const hospital = hospitalsData.find((item) => item.node_id === nodeId);
    if (!hospital || !map) return;
    map.panTo([hospital.lat, hospital.lng]);
    const markers = hospitalMarkers.get(nodeId);
    if (markers?.length) markers[0].openPopup();
}

async function updateEdgeCongestion() {
    const edgeId = byId("selectEdge")?.value;
    const level = Number.parseInt(byId("selectCongestion")?.value, 10);
    if (!edgeId || !Number.isInteger(level)) {
        showToast("Vui lòng chọn đoạn đường và mức ùn tắc.", true);
        return;
    }

    setButtonBusy("btnUpdateCongestion", true, "Đang cập nhật…", "Cập nhật");
    try {
        await fetchJson(`${API_BASE}/edges/congestion`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ edge_id: edgeId, congestion_level: level }),
        });
        edgesData = await fetchJson(`${API_BASE}/edges?limit=2000`);
        rebuildEdgeIndex();
        populateEdgeSelect();
        renderEdgesOnMap();
        routeRequestCache.clear();
        showToast(`Đã cập nhật ${edgeId} lên mức ùn tắc ${level}.`);

        if (!byId("routeResultPanel").hidden) {
            setOperationStatus(
                "Dữ liệu giao thông đã đổi; đang tính lại tuyến hiện tại…",
            );
            await calculateRoute();
        }
    } catch (error) {
        setOperationStatus(`Không thể cập nhật ùn tắc: ${error.message}`, true);
        showToast(`Không thể cập nhật ùn tắc: ${error.message}`, true);
    } finally {
        setButtonBusy("btnUpdateCongestion", false, "Đang cập nhật…", "Cập nhật");
    }
}

async function checkSystemHealth() {
    setButtonBusy("btnHealth", true, "Đang ping…", "Ping GET /api/health");
    const startedAt = performance.now();
    try {
        const data = await fetchJson(`${API_BASE}/health`);
        const roundTrip = performance.now() - startedAt;
        showToast(
            `Health ${data.status}: ${Number(data.nodes_count || 0).toLocaleString("vi-VN")} nodes · API ${data.latency_ms} ms · round trip ${roundTrip.toFixed(1)} ms.`,
        );
    } catch (error) {
        showToast(`Health check thất bại: ${error.message}`, true);
    } finally {
        setButtonBusy("btnHealth", false, "Đang ping…", "Ping GET /api/health");
    }
}

function formatDistance(distanceMeters) {
    const distance = Number(distanceMeters || 0);
    return distance >= 1000
        ? `${(distance / 1000).toFixed(2)} km`
        : `${distance.toFixed(0)} m`;
}

function formatDuration(seconds) {
    const value = Math.max(0, Number(seconds || 0));
    if (value < 60) return `${value.toFixed(0)} giây`;
    const hours = Math.floor(value / 3600);
    const minutes = Math.round((value % 3600) / 60);
    if (!hours) return `${minutes} phút`;
    return `${hours} giờ ${minutes} phút`;
}

function showToast(message, isError = false) {
    const toast = byId("toast");
    if (!toast) return;
    window.clearTimeout(toastTimer);
    toast.textContent = message;
    toast.classList.toggle("is-error", isError);
    toast.style.display = "block";
    toastTimer = window.setTimeout(() => {
        toast.style.display = "none";
    }, 4200);
}

window.addEventListener("load", initMap);

if (typeof document !== "undefined" && typeof document.addEventListener === "function") {
    document.addEventListener("click", (e) => {
        const container = document.querySelector?.(".waypoint-search-container");
        const dropdown = byId("waypointSuggestionsDropdown");
        if (dropdown && container && !container.contains(e.target)) {
            dropdown.style.display = "none";
        }
    });
}
