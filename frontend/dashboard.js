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

function initMap() {
    map = L.map('map', { center: [10.778, 106.692], zoom: 13, zoomControl: false, renderer: L.canvas() });

    // CartoDB Dark/Voyager Tile Layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        maxZoom: 19, attribution: '&copy; OpenStreetMap &copy; CARTO'
    }).addTo(map);

    L.control.zoom({ position: 'topright' }).addTo(map);

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
    const goalNodeId = parseInt(document.getElementById('selectHospital').value);
    const algorithm = document.getElementById('selectAlgorithm').value;
    const startNodeId = currentAmbulanceData.mapped_nearest_node ? currentAmbulanceData.mapped_nearest_node.nearest_node_id : null;

    showToast(`🧠 Đang chạy thuật toán ${algorithm.toUpperCase()} trên đồ thị thực tế...`);

    try {
        const res = await fetch('/api/route', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                start_node_id: startNodeId,
                goal_node_id: goalNodeId,
                algorithm: algorithm
            })
        });

        const data = await res.json();
        if (!data.found) {
            showToast('⚠️ Không tìm thấy đường đi giữa hai điểm trên đồ thị!');
            return;
        }

        // Display metrics
        document.getElementById('routeResultPanel').style.display = 'block';
        document.getElementById('resCost').textContent = data.total_cost.toFixed(2);
        document.getElementById('resDistance').textContent = `${(data.total_distance_m / 1000).toFixed(2)} km`;
        document.getElementById('resExpanded').textContent = data.nodes_expanded.toLocaleString();
        document.getElementById('resTime').textContent = `${data.execution_time_ms.toFixed(2)} ms`;

        // Draw glowing route on map
        if (activeRoutePolyline) { map.removeLayer(activeRoutePolyline); }
        routeNodeMarkers.forEach(m => map.removeLayer(m));
        routeNodeMarkers = [];

        activeRoutePolyline = L.polyline(data.path_coords, {
            color: '#a855f7', weight: 6, opacity: 0.9, lineJoin: 'round',
            dashArray: algorithm === 'astar' ? null : '8, 8'
        }).addTo(map);

        map.fitBounds(activeRoutePolyline.getBounds(), { padding: [50, 50] });
        showToast(`✅ Tuyến đường tìm thấy bằng ${algorithm.toUpperCase()} (${data.nodes_expanded} nodes, ${data.execution_time_ms.toFixed(1)}ms)!`);

    } catch (err) {
        showToast('Lỗi khi tính toán lộ trình!');
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
