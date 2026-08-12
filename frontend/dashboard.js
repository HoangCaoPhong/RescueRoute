let map;
let hospitalsData = [];
let poisData = [];
let edgesData = [];
let currentAmbulanceData = { lat: 10.773, lng: 106.698, mapped_nearest_node: {} };
let ambulanceMarker = null;
let hospitalMarkers = {};
let showPOIIcons = true;
let edgePolylines = {};
let activeRoutePolyline = null;
let routeNodeMarkers = [];
let showTraffic = true;
let searchVisualizationData = null;
let searchStepIndex = 0;
let searchAnimationTimer = null;
let searchVisitedLayer = null;
let searchFrontierLayer = null;
let searchCurrentLayer = null;

function initMap() {
    map = L.map('map', { center: [10.778, 106.692], zoom: 13, zoomControl: false, renderer: L.canvas() });

    // CartoDB Dark/Voyager Tile Layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        maxZoom: 19, attribution: '&copy; OpenStreetMap &copy; CARTO'
    }).addTo(map);

    L.control.zoom({ position: 'topright' }).addTo(map);

    searchVisitedLayer = L.layerGroup().addTo(map);
    searchFrontierLayer = L.layerGroup().addTo(map);
    searchCurrentLayer = L.layerGroup().addTo(map);

    map.on('click', function(e) {
        updateAmbulanceGPS(e.latlng.lat, e.latlng.lng);
    });

    loadInitialData();
}

async function loadInitialData() {
    try {
        const [nodesRes, edgesRes, gpsRes, healthRes] = await Promise.all([
            fetch('/api/nodes?poi_type=all&limit=10000'),
            fetch('/api/edges?limit=2000'),
            fetch('/api/ambulance/location'),
            fetch('/api/health')
        ]);

        poisData = await nodesRes.json();
        hospitalsData = poisData.filter(p => p.is_hospital);
        edgesData = await edgesRes.json();
        currentAmbulanceData = await gpsRes.json();
        const healthData = await healthRes.json();

        // Update UI Stats safely
        const elNodes = document.getElementById('statNodes');
        if (elNodes) elNodes.textContent = healthData.nodes_count.toLocaleString();
        const elEdges = document.getElementById('statEdges');
        if (elEdges) elEdges.textContent = healthData.edges_count.toLocaleString();
        const elHosp = document.getElementById('statHospitals');
        if (elHosp) elHosp.textContent = hospitalsData.length;
        const elLat = document.getElementById('statLatency');
        if (elLat) elLat.textContent = healthData.latency_ms + ' ms';
        const elSummary = document.getElementById('datasetSummary');
        if (elSummary) elSummary.textContent = `Đồ thị RAM: ${healthData.nodes_count.toLocaleString()} nodes, ${healthData.edges_count.toLocaleString()} edges sẵn sàng.`;

        populateHospitalSelect();
        populateEdgeSelect();
        populateStartControls();
        onStartModeChange();
        renderHospitalsOnMap();
        renderEdgesOnMap();
        updateAmbulanceDisplay(currentAmbulanceData);

    } catch (err) {
        console.error('Error in loadInitialData:', err);
        showToast('Lỗi khi kết nối Backend API!');
    }
}

function populateHospitalSelect() {
    const select = document.getElementById('selectHospital');
    if (!select) return;
    select.innerHTML = '';
    hospitalsData.forEach(h => {
        const opt = document.createElement('option');
        opt.value = h.node_id;
        opt.textContent = `${h.name} (${h.type})`;
        select.appendChild(opt);
    });
}

function populateEdgeSelect() {
    const select = document.getElementById('selectEdge');
    if (!select) return;
    select.innerHTML = '';
    edgesData.slice(0, 50).forEach(e => {
        const opt = document.createElement('option');
        opt.value = e.edge_id;
        opt.textContent = `[${e.edge_id}] ${e.name} (${e.distance}m, Lv ${e.congestion_level})`;
        select.appendChild(opt);
    });
}

function populateStartControls() {
    const startInput = document.getElementById('inputStartNode');
    if (startInput && currentAmbulanceData?.mapped_nearest_node?.nearest_node_id) {
        startInput.value = currentAmbulanceData.mapped_nearest_node.nearest_node_id;
    }
}

function onStartModeChange() {
    const mode = document.getElementById('selectStartMode')?.value || 'current';
    const input = document.getElementById('inputStartNode');
    if (!input) return;
    input.style.display = mode === 'custom' ? 'block' : 'none';
}

function parseNodeIdList(rawValue) {
    if (!rawValue) return [];
    const seen = new Set();
    const values = [];
    rawValue
        .split(/[,;\s]+/)
        .map(v => parseInt(v.trim(), 10))
        .filter(v => Number.isInteger(v))
        .forEach(v => {
            if (!seen.has(v)) {
                seen.add(v);
                values.push(v);
            }
        });
    return values;
}

function getNodeLabel(nodeId) {
    if (!Number.isInteger(nodeId)) return '-';
    const ambulanceNode = currentAmbulanceData?.mapped_nearest_node;
    if (ambulanceNode && ambulanceNode.nearest_node_id === nodeId) {
        return ambulanceNode.nearest_node_name || String(nodeId);
    }
    const hospital = hospitalsData.find(h => h.node_id === nodeId || h.poi_node_id === nodeId);
    if (hospital) return hospital.name || String(nodeId);
    const poi = poisData.find(p => p.node_id === nodeId || p.poi_node_id === nodeId);
    if (poi) return poi.name || String(nodeId);
    return String(nodeId);
}

function getCriterionLabel(value) {
    const labels = {
        time: 'Thời gian di chuyển ngắn nhất',
        distance: 'Quãng đường ngắn nhất',
        cost: 'Chi phí lộ trình thấp nhất',
        hops: 'Ít bước nhảy nhất'
    };
    return labels[value] || value || '-';
}

function getCriterionHint(criterion, algorithm) {
    const mapping = {
        time: 'Ưu tiên tuyến đường nhanh nhất theo thời gian/chi phí ước lượng.',
        distance: 'Ưu tiên tổng quãng đường ngắn nhất giữa các điểm.',
        cost: 'Ưu tiên tổng chi phí lộ trình thấp nhất theo trọng số cạnh.',
        hops: 'Ưu tiên số chặng di chuyển ít nhất.'
    };
    const base = mapping[criterion] || 'Tiêu chí được dùng để mô tả hướng tối ưu hóa của tuyến đường.';
    if (algorithm === 'bfs') {
        return `${base} Bản đồ bước tìm kiếm sẽ hiển thị vì BFS có trace visited/frontier sẵn.`;
    }
    return `${base} Với thuật toán hiện tại, phần giải thích sẽ dựa trên kết quả tính được và trace nếu backend cung cấp.`;
}

function stopSearchAnimation() {
    if (searchAnimationTimer) {
        clearInterval(searchAnimationTimer);
        searchAnimationTimer = null;
    }
    const btn = document.getElementById('btnPlaySearch');
    if (btn) btn.textContent = '▶ Play';
}

function clearSearchVisualization() {
    stopSearchAnimation();
    if (searchVisitedLayer) searchVisitedLayer.clearLayers();
    if (searchFrontierLayer) searchFrontierLayer.clearLayers();
    if (searchCurrentLayer) searchCurrentLayer.clearLayers();
    searchVisualizationData = null;
    searchStepIndex = 0;
    const panel = document.getElementById('searchVisualizationPanel');
    if (panel) panel.style.display = 'none';
}

function renderTraceTokens(containerId, items, cssClass) {
    const container = document.getElementById(containerId);
    if (!container) return;
    if (!items || items.length === 0) {
        container.textContent = '-';
        return;
    }
    container.innerHTML = items
        .map(item => `<span class="search-viz-token ${cssClass}">${item}</span>`)
        .join('');
}

function renderSearchStep(stepIndex) {
    if (!searchVisualizationData || !searchVisualizationData.steps || searchVisualizationData.steps.length === 0) return;

    const steps = searchVisualizationData.steps;
    const safeIndex = Math.max(0, Math.min(stepIndex, steps.length - 1));
    searchStepIndex = safeIndex;

    const step = steps[safeIndex];
    const visitedOrder = (searchVisualizationData.visited_order || []).slice(0, safeIndex + 1);
    const frontier = step.frontier || [];
    const currentNode = step.current_node;
    const nodeCoords = searchVisualizationData.node_coords || {};

    if (searchVisitedLayer) searchVisitedLayer.clearLayers();
    if (searchFrontierLayer) searchFrontierLayer.clearLayers();
    if (searchCurrentLayer) searchCurrentLayer.clearLayers();

    visitedOrder.forEach(nodeId => {
        const coords = nodeCoords[String(nodeId)];
        if (!coords) return;
        L.circleMarker(coords, {
            radius: 5,
            color: '#3b82f6',
            fillColor: '#3b82f6',
            fillOpacity: 0.35,
            weight: 1
        }).bindTooltip(String(nodeId), { permanent: false, direction: 'top' }).addTo(searchVisitedLayer);
    });

    frontier.forEach(item => {
        const coords = nodeCoords[String(item.node_id)];
        if (!coords) return;
        L.circleMarker(coords, {
            radius: 6,
            color: '#f59e0b',
            fillColor: '#f59e0b',
            fillOpacity: 0.45,
            weight: 1
        }).bindTooltip(String(item.node_id), { permanent: false, direction: 'top' }).addTo(searchFrontierLayer);
    });

    const currentCoords = nodeCoords[String(currentNode)];
    if (currentCoords) {
        L.circleMarker(currentCoords, {
            radius: 8,
            color: '#10b981',
            fillColor: '#10b981',
            fillOpacity: 0.9,
            weight: 2
        }).bindTooltip(String(currentNode), { permanent: false, direction: 'top' }).addTo(searchCurrentLayer);
    }

    const vizAlgorithm = document.getElementById('vizAlgorithm');
    const vizStep = document.getElementById('vizStep');
    const vizCurrentNode = document.getElementById('vizCurrentNode');
    const vizVisitedCount = document.getElementById('vizVisitedCount');
    const vizFrontierCount = document.getElementById('vizFrontierCount');
    const vizExplanation = document.getElementById('vizExplanation');

    if (vizAlgorithm) vizAlgorithm.textContent = searchVisualizationData.algorithm || '-';
    if (vizStep) vizStep.textContent = `Step ${safeIndex + 1} / ${steps.length}`;
    if (vizCurrentNode) vizCurrentNode.textContent = currentNode ?? '-';
    if (vizVisitedCount) vizVisitedCount.textContent = visitedOrder.length.toLocaleString();
    if (vizFrontierCount) vizFrontierCount.textContent = frontier.length.toLocaleString();
    if (vizExplanation) {
        vizExplanation.textContent = `Mỗi bước cho thấy node hiện tại, danh sách visited tích lũy và frontier tại thời điểm mở rộng node đó.`;
    }

    renderTraceTokens('vizVisitedList', visitedOrder.map(nodeId => String(nodeId)), 'visited');
    renderTraceTokens('vizFrontierList', frontier.map(item => String(item.node_id)), 'frontier');
}

function startSearchVisualization(routeData) {
    if (!routeData?.search_trace?.steps?.length) {
        clearSearchVisualization();
        return;
    }

    searchVisualizationData = routeData.search_trace;
    searchStepIndex = 0;

    const panel = document.getElementById('searchVisualizationPanel');
    if (panel) panel.style.display = 'flex';

    renderSearchStep(0);
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
    const btn = document.getElementById('btnPlaySearch');
    const speed = parseInt(document.getElementById('searchSpeed')?.value || '80', 10);

    if (searchAnimationTimer) {
        stopSearchAnimation();
        return;
    }

    if (btn) btn.textContent = '⏸ Pause';
    searchAnimationTimer = setInterval(() => {
        if (!searchVisualizationData) {
            stopSearchAnimation();
            return;
        }

        if (searchStepIndex >= searchVisualizationData.steps.length - 1) {
            stopSearchAnimation();
            return;
        }

        renderSearchStep(searchStepIndex + 1);
    }, speed);
}

function buildRouteSummary(startId, waypointIds, goalId, algorithm, criterion) {
    const startLabel = getNodeLabel(startId);
    const goalLabel = getNodeLabel(goalId);
    const waypointLabels = waypointIds.map(id => getNodeLabel(id));
    const viaText = waypointLabels.length ? waypointLabels.join(' → ') : 'Không có';

    return `
        <strong>Xuất phát:</strong> ${startLabel} (${startId})<br>
        <strong>Trung gian:</strong> ${viaText}<br>
        <strong>Đích đến:</strong> ${goalLabel} (${goalId})<br>
        <strong>Thuật toán:</strong> ${algorithm.toUpperCase()}<br>
        <strong>Tiêu chí tối ưu:</strong> ${getCriterionLabel(criterion)}
    `;
}

function appendSegmentItem(container, title, response) {
    if (!container) return;
    const item = document.createElement('div');
    item.className = 'route-segment-item';
    item.innerHTML = `
        <strong>${title}</strong><br>
        Path nodes: ${(response.path_nodes || []).join(' → ')}<br>
        Cost: ${(response.total_cost ?? 0).toFixed(2)} | Distance: ${((response.total_distance_m ?? 0) / 1000).toFixed(2)} km | Expanded: ${(response.nodes_expanded ?? 0).toLocaleString()} | Time: ${(response.execution_time_ms ?? 0).toFixed(2)} ms
    `;
    container.appendChild(item);
}

async function runRouteSegment(startId, goalId, algorithm, criterion) {
    const res = await fetch('/api/route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            start_node_id: startId,
            goal_node_id: goalId,
            algorithm: algorithm,
            optimization_criterion: criterion
        })
    });

    const contentType = res.headers.get('content-type') || '';
    const data = contentType.includes('application/json') ? await res.json() : { detail: await res.text() };
    if (!res.ok) {
        throw new Error(data?.detail || data?.message || `HTTP ${res.status}`);
    }
    if (!data.found) {
        throw new Error(data?.message || 'Không tìm thấy đường đi giữa hai điểm trên đồ thị!');
    }
    return data;
}

function renderHospitalsOnMap() {
    // First clear existing hospital markers
    Object.values(hospitalMarkers).forEach(m => map.removeLayer(m));
    hospitalMarkers = {};

    poisData.forEach(h => {
        let marker;
        if (h.is_hospital) {
            if (showPOIIcons) {
                const isHospital = h.type.toLowerCase().includes('hospital') || h.type.toLowerCase().includes('bệnh_viện');
                const iconClass = isHospital ? 'icon-hospital' : 'icon-clinic';
                const emoji = isHospital ? '🏥' : '🩺';

                const icon = L.divIcon({
                    className: `custom-div-icon ${iconClass}`,
                    html: `<span>${emoji}</span>`,
                    iconSize: [34, 34], iconAnchor: [17, 17]
                });

                marker = L.marker([h.lat, h.lng], { icon: icon, zIndexOffset: 1000 }).addTo(map);
                marker.bindPopup(`
                    <div style="font-family: Outfit, sans-serif; min-width: 180px;">
                        <b style="color: #38bdf8; font-size: 0.95rem;">${emoji} ${h.name}</b><br>
                        <span style="font-size: 0.8rem; color: #94a3b8;">Loại: ${h.type}</span><br>
                        <span style="font-size: 0.75rem; color: #cbd5e1;">Mã Node: <code>${h.node_id}</code></span><br>
                        <button onclick="setDestination(${h.node_id})" style="margin-top: 6px; width: 100%; padding: 4px; font-size: 0.75rem; font-weight: bold; background: #6366f1; color: white; border: none; border-radius: 4px; cursor: pointer;">
                            🎯 Chọn làm đích đến
                        </button>
                    </div>
                `);
            } else {
                marker = L.circleMarker([h.lat, h.lng], {
                    radius: 4, color: '#ef4444', fillColor: '#ef4444', fillOpacity: 0.9, weight: 1
                }).addTo(map);
                marker.bindPopup(`<b>🏥 ${h.name}</b><br>Loại: ${h.type}<br>Mã Node: ${h.node_id}<br><button onclick="setDestination(${h.node_id})" style="margin-top: 6px; width: 100%; padding: 4px; font-size: 0.75rem; font-weight: bold; background: #6366f1; color: white; border: none; border-radius: 4px; cursor: pointer;">🎯 Chọn làm đích đến</button>`);
            }
        } else {
            marker = L.circleMarker([h.lat, h.lng], {
                radius: 2, color: '#38bdf8', fillColor: '#38bdf8', fillOpacity: 0.8, weight: 0
            }).addTo(map);
            marker.bindPopup(`<b style="color: #38bdf8;">📍 ${h.name || 'POI'}</b><br><span style="font-size: 0.8rem;">Loại: ${h.type || 'N/A'}</span>`);
        }
        hospitalMarkers[h.poi_node_id + '_' + Math.random()] = marker;
    });
}

function togglePOIIcons() {
    showPOIIcons = !showPOIIcons;
    const btn = document.getElementById('btnTogglePOIIcon');
    if (showPOIIcons) {
        btn.textContent = 'Đang Bật 🟢';
        btn.style.background = 'rgba(16, 185, 129, 0.15)';
        btn.style.color = '#34d399';
        btn.style.borderColor = 'rgba(16, 185, 129, 0.3)';
    } else {
        btn.textContent = 'Đang Tắt 🔴';
        btn.style.background = 'rgba(244, 63, 94, 0.15)';
        btn.style.color = '#f43f5e';
        btn.style.borderColor = 'rgba(244, 63, 94, 0.3)';
    }
    renderHospitalsOnMap();
}

function renderEdgesOnMap() {
    // First, remove existing polylines
    Object.values(edgePolylines).forEach(poly => map.removeLayer(poly));
    edgePolylines = {};

    if (!showTraffic) return;

    let multiLines = {
        normal: [], // Level <= 2
        heavy: [],  // Level 3
        severe: [], // Level 4
        level5: [], // Level 5
        level6: []  // Level 6
    };

    // Group edges by congestion level for batch rendering
    edgesData.forEach(edge => {
        let coords = [[edge.u_lat, edge.u_lng], [edge.v_lat, edge.v_lng]];
        if (edge.congestion_level === 6) {
            multiLines.level6.push(coords);
        } else if (edge.congestion_level === 5) {
            multiLines.level5.push(coords);
        } else if (edge.congestion_level >= 4) {
            multiLines.severe.push(coords);
        } else if (edge.congestion_level == 3) {
            multiLines.heavy.push(coords);
        } else {
            multiLines.normal.push(coords);
        }
    });

    // Render as large MultiPolylines (drastically improves Canvas performance)
    if (multiLines.normal.length > 0) {
        edgePolylines['normal'] = L.polyline(multiLines.normal, {
            color: '#38bdf8', weight: 2, opacity: 0.3, interactive: false
        }).addTo(map);
    }
    if (multiLines.heavy.length > 0) {
        edgePolylines['heavy'] = L.polyline(multiLines.heavy, {
            color: '#f59e0b', weight: 3, opacity: 0.85, interactive: false
        }).addTo(map);
    }
    if (multiLines.severe.length > 0) {
        edgePolylines['severe'] = L.polyline(multiLines.severe, {
            color: '#f43f5e', weight: 4, opacity: 0.95, interactive: false
        }).addTo(map);
    }
    if (multiLines.level5.length > 0) {
        edgePolylines['level5'] = L.polyline(multiLines.level5, {
            color: '#eab308', weight: 4, opacity: 0.95, interactive: false
        }).addTo(map);
    }
    if (multiLines.level6.length > 0) {
        edgePolylines['level6'] = L.polyline(multiLines.level6, {
            color: '#ff0000', weight: 5, opacity: 1.0, interactive: false
        }).addTo(map);
    }
}

function toggleTrafficLayer() {
    showTraffic = !showTraffic;
    const btn = document.getElementById('btnToggleTraffic');
    if (showTraffic) {
        btn.textContent = 'Đang Bật 🟢';
        btn.style.background = 'rgba(6, 182, 212, 0.15)';
        btn.style.color = '#22d3ee';
        btn.style.borderColor = 'rgba(6, 182, 212, 0.3)';
    } else {
        btn.textContent = 'Đang Tắt 🔴';
        btn.style.background = 'rgba(244, 63, 94, 0.15)';
        btn.style.color = '#f43f5e';
        btn.style.borderColor = 'rgba(244, 63, 94, 0.3)';
    }
    renderEdgesOnMap();
}

function updateAmbulanceDisplay(data) {
    const lat = data.lat || 10.773;
    const lng = data.lng || 106.698;
    const mapped = data.mapped_nearest_node || {};

    document.getElementById('gpsCodeDisplay').textContent = `GPS: (${lat.toFixed(5)}, ${lng.toFixed(5)})`;
    document.getElementById('nearestDisplay').textContent = `Node gần nhất: [${mapped.nearest_node_id || '-'}] ${mapped.nearest_node_name || 'Nút đường'} (${mapped.distance_meters || 0}m)`;

    const ambIcon = L.divIcon({
        className: 'custom-div-icon icon-ambulance',
        html: `<span>🚑</span>`,
        iconSize: [42, 42], iconAnchor: [21, 21]
    });

    if (!ambulanceMarker) {
        ambulanceMarker = L.marker([lat, lng], { icon: ambIcon, zIndexOffset: 2000 }).addTo(map);
    } else {
        ambulanceMarker.setLatLng([lat, lng]);
    }

    ambulanceMarker.bindPopup(`<b>🚑 Xe Cấp Cứu Đang Trực</b><br>Vị trí GPS: ${lat.toFixed(5)}, ${lng.toFixed(5)}<br>Khớp Node: ${mapped.nearest_node_name || ''} (${mapped.distance_meters || 0}m)`);
}

async function updateAmbulanceGPS(lat, lng) {
    try {
        const res = await fetch('/api/ambulance/location', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lat: lat, lng: lng })
        });
        const data = await res.json();
        currentAmbulanceData = data.current_gps;
        updateAmbulanceDisplay(currentAmbulanceData);
        showToast(`📍 Cập nhật GPS (${lat.toFixed(4)}, ${lng.toFixed(4)}) - Ánh xạ Node trong <3ms!`);
    } catch (err) {
        showToast('Lỗi khi gửi tọa độ GPS!');
    }
}

function getDeviceLocation() {
    if (!navigator.geolocation) { showToast('Trình duyệt không hỗ trợ Geolocation!'); return; }
    showToast('📡 Đang định vị GPS từ thiết bị...');
    navigator.geolocation.getCurrentPosition(
        (pos) => updateAmbulanceGPS(pos.coords.latitude, pos.coords.longitude),
        (err) => showToast('Không thể lấy GPS thiết bị!')
    );
}

function setDestination(nodeId) {
    document.getElementById('selectHospital').value = nodeId;
    calculateRoute();
}

function onHospitalSelectChange() {
    const hId = parseInt(document.getElementById('selectHospital').value);
    const hospital = hospitalsData.find(h => h.node_id === hId);
    if (hospital) {
        map.panTo([hospital.lat, hospital.lng]);
        if (hospitalMarkers[hId]) hospitalMarkers[hId].openPopup();
    }
}

async function calculateRoute() {
    const goalNodeId = parseInt(document.getElementById('selectHospital').value, 10);
    const algorithm = document.getElementById('selectAlgorithm').value;
    const criterion = document.getElementById('selectCriterion')?.value || 'time';
    const startMode = document.getElementById('selectStartMode')?.value || 'current';
    const customStartNode = parseInt(document.getElementById('inputStartNode')?.value, 10);
    const currentStartNode = currentAmbulanceData?.mapped_nearest_node?.nearest_node_id;
    const startNodeId = startMode === 'custom' ? customStartNode : currentStartNode;
    const waypointIds = parseNodeIdList(document.getElementById('inputWaypoints')?.value || '')
        .filter(nodeId => nodeId !== startNodeId && nodeId !== goalNodeId);
    const legs = [startNodeId, ...waypointIds, goalNodeId];

    if (!Number.isInteger(startNodeId)) {
        showToast('Vui lòng chọn hoặc nhập điểm xuất phát hợp lệ.');
        return;
    }

    if (!Number.isInteger(goalNodeId)) {
        showToast('Vui lòng chọn một điểm đến hợp lệ.');
        return;
    }

    showToast(`🧠 Đang chạy ${algorithm.toUpperCase()} với tiêu chí ${criterion.toUpperCase()}...`);

    try {
        const segmentResults = [];
        for (let index = 0; index < legs.length - 1; index += 1) {
            const segmentStart = legs[index];
            const segmentGoal = legs[index + 1];
            const segmentResult = await runRouteSegment(segmentStart, segmentGoal, algorithm, criterion);
            segmentResults.push({ start: segmentStart, goal: segmentGoal, result: segmentResult });
        }

        const totalCost = segmentResults.reduce((sum, item) => sum + (item.result.total_cost || 0), 0);
        const totalDistance = segmentResults.reduce((sum, item) => sum + (item.result.total_distance_m || 0), 0);
        const totalExpanded = segmentResults.reduce((sum, item) => sum + (item.result.nodes_expanded || 0), 0);
        const totalTime = segmentResults.reduce((sum, item) => sum + (item.result.execution_time_ms || 0), 0);
        const mergedCoords = [];
        const mergedNodes = [];

        segmentResults.forEach(({ result }, index) => {
            const coords = result.path_coords || [];
            const nodes = result.path_nodes || [];
            const coordSlice = index === 0 ? coords : coords.slice(1);
            const nodeSlice = index === 0 ? nodes : nodes.slice(1);
            mergedCoords.push(...coordSlice);
            mergedNodes.push(...nodeSlice);
        });

        const summaryPanel = document.getElementById('routeResultPanel');
        const summaryBox = document.getElementById('routeSummary');
        const explanationBox = document.getElementById('routeExplanation');
        const segmentBox = document.getElementById('routeSegmentList');
        if (summaryPanel) summaryPanel.style.display = 'block';
        if (summaryBox) summaryBox.innerHTML = buildRouteSummary(startNodeId, waypointIds, goalNodeId, algorithm, criterion);
        if (explanationBox) explanationBox.textContent = getCriterionHint(criterion, algorithm);
        if (segmentBox) segmentBox.innerHTML = '';

        segmentResults.forEach((segment, index) => {
            appendSegmentItem(
                segmentBox,
                `Chặng ${index + 1}: ${getNodeLabel(segment.start)} → ${getNodeLabel(segment.goal)}`,
                segment.result
            );
        });

        document.getElementById('routeResultPanel').style.display = 'block';
        document.getElementById('resCost').textContent = totalCost.toFixed(2);
        document.getElementById('resDistance').textContent = `${(totalDistance / 1000).toFixed(2)} km`;
        document.getElementById('resExpanded').textContent = totalExpanded.toLocaleString();
        document.getElementById('resTime').textContent = `${totalTime.toFixed(2)} ms`;

        // Draw glowing route on map
        if (activeRoutePolyline) { map.removeLayer(activeRoutePolyline); }
        routeNodeMarkers.forEach(m => map.removeLayer(m));
        routeNodeMarkers = [];

        activeRoutePolyline = L.polyline(mergedCoords, {
            color: '#a855f7', weight: 6, opacity: 0.9, lineJoin: 'round',
            dashArray: algorithm === 'astar' ? null : '8, 8'
        }).addTo(map);

        map.fitBounds(activeRoutePolyline.getBounds(), { padding: [50, 50] });

        if (segmentResults.length === 1 && segmentResults[0].result.search_trace) {
            startSearchVisualization(segmentResults[0].result);
        } else {
            clearSearchVisualization();
            const explanationBox = document.getElementById('routeExplanation');
            if (explanationBox) {
                explanationBox.textContent = `${explanationBox.textContent} Tuyến đi nhiều chặng được ghép từ ${segmentResults.length} lần tính riêng biệt.`;
            }
        }

        showToast(`✅ Tuyến đường tìm thấy bằng ${algorithm.toUpperCase()} (${totalExpanded.toLocaleString()} nodes, ${totalTime.toFixed(1)}ms)!`);

    } catch (err) {
        console.error('Error in calculateRoute:', err);
        showToast(`Lỗi khi tính toán lộ trình: ${err?.message || err}`);
    }
}

async function updateEdgeCongestion() {
    const edgeId = document.getElementById('selectEdge').value;
    const level = parseInt(document.getElementById('selectCongestion').value);

    try {
        const res = await fetch('/api/edges/congestion', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ edge_id: edgeId, congestion_level: level })
        });
        const data = await res.json();
        showToast(`🚦 Đã cập nhật mức kẹt xe Level ${level} cho đoạn đường ${edgeId}`);
        
        // Refresh edges
        const edgesRes = await fetch('/api/edges?limit=600');
        edgesData = await edgesRes.json();
        renderEdgesOnMap();

        // Recalculate route if active
        if (document.getElementById('routeResultPanel').style.display === 'block') {
            calculateRoute();
        }
    } catch (err) {
        showToast('Lỗi khi cập nhật kẹt xe!');
    }
}

async function checkSystemHealth() {
    try {
        const res = await fetch('/api/health');
        const data = await res.json();
        showToast(`⚡ Health OK: Status ${data.status} | Đồ thị RAM: ${data.nodes_count.toLocaleString()} nodes | Latency: ${data.latency_ms}ms`);
    } catch (err) {
        showToast('Lỗi khi ping Health API!');
    }
}

function showToast(msg) {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.style.display = 'block';
    setTimeout(() => { toast.style.display = 'none'; }, 3500);
}

window.onload = initMap;
