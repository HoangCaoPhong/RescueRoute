const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

function loadDashboardContext({ storedTheme = null } = {}) {
    const themeWrites = [];
    const context = vm.createContext({
        console,
        document: {
            createElement: () => ({}),
            getElementById: () => null
        },
        fetch: async () => {
            throw new Error('Unexpected network call in unit test.');
        },
        localStorage: {
            getItem: () => storedTheme,
            setItem: (key, value) => themeWrites.push([key, value])
        },
        navigator: {},
        performance: { now: () => 0 },
        themeWrites,
        window: {
            addEventListener: () => { },
            clearInterval,
            clearTimeout,
            setInterval,
            setTimeout
        }
    });
    const scriptPath = path.join(__dirname, '..', 'dashboard.js');
    vm.runInContext(fs.readFileSync(scriptPath, 'utf8'), context);
    return context;
}

test('dashboard always opens in light mode and keeps dark mode as a manual toggle', () => {
    const context = loadDashboardContext({ storedTheme: 'dark' });
    const htmlPath = path.join(__dirname, '..', 'dashboard.html');
    const html = fs.readFileSync(htmlPath, 'utf8');

    assert.equal(vm.runInContext('currentTheme', context), 'light');
    assert.deepEqual(context.themeWrites, []);
    assert.match(html, /<html lang="vi" data-theme="light">/);
    assert.match(html, /<span class="theme-label">Sáng<\/span>/);
    assert.doesNotMatch(html, /connectionStatus|Backend trực tuyến/);

    vm.runInContext('toggleTheme()', context);
    assert.equal(vm.runInContext('currentTheme', context), 'dark');
    vm.runInContext('toggleTheme()', context);
    assert.equal(vm.runInContext('currentTheme', context), 'light');
});

test('parseNodeIdList removes invalid and duplicate waypoint IDs', () => {
    const context = loadDashboardContext();
    const values = vm.runInContext("parseNodeIdList('101, 202; 202 invalid 303')", context);
    assert.deepEqual(Array.from(values), [101, 202, 303]);
});

test('annotateResult derives hops and a transparent fallback travel-time estimate', () => {
    const context = loadDashboardContext();
    const result = vm.runInContext(`annotateResult({
        path_nodes: [1, 2, 3],
        total_distance_m: 1000,
        total_cost: 12
    })`, context);
    assert.equal(result.hopCount, 2);
    assert.ok(Math.abs(result.estimatedTimeSeconds - 120) < 0.001);
    assert.equal(result.congestion.knownEdges, 0);
});

test('congestion analysis reports data coverage and average congestion level', () => {
    const context = loadDashboardContext();
    const congestion = vm.runInContext(`(() => {
        edgeIndex = new Map([[
            '1_2',
            {
                edge_id: '1_2',
                distance: 250,
                congestion_level: 5
            }
        ]]);
        return analyzePathCongestion({
            path_nodes: [1, 2],
            total_distance_m: 250
        });
    })()`, context);

    assert.equal(congestion.knownEdges, 1);
    assert.equal(congestion.knownDistance, 250);
    assert.equal(congestion.congestionLevelTotal, 5);
    assert.equal(congestion.averageKnownLevel, 5);
});

test('aggregateSegments joins legs without duplicating shared nodes', () => {
    const context = loadDashboardContext();
    const aggregate = vm.runInContext(`aggregateSegments([
        {
            start: 1,
            goal: 2,
            result: {
                path_coords: [[0, 0], [0, 1]],
                path_nodes: [1, 2],
                total_cost: 2,
                total_distance_m: 1000,
                nodes_expanded: 3,
                execution_time_ms: 4,
                estimatedTimeSeconds: 120,
                hopCount: 1,
                congestion: { knownEdges: 1, totalEdges: 1, highCongestionEdges: [] }
            }
        },
        {
            start: 2,
            goal: 3,
            result: {
                path_coords: [[0, 1], [0, 2]],
                path_nodes: [2, 3],
                total_cost: 3,
                total_distance_m: 2000,
                nodes_expanded: 4,
                execution_time_ms: 5,
                estimatedTimeSeconds: 240,
                hopCount: 1,
                congestion: { knownEdges: 0, totalEdges: 1, highCongestionEdges: [] }
            }
        }
    ], [1, 2, 3])`, context);

    assert.deepEqual(Array.from(aggregate.pathNodes), [1, 2, 3]);
    assert.equal(aggregate.totalCost, 5);
    assert.equal(aggregate.totalDistance, 3000);
    assert.equal(aggregate.totalExpanded, 7);
    assert.equal(aggregate.totalHops, 2);
});

test('zero is retained as a valid route metric', () => {
    const context = loadDashboardContext();
    assert.equal(vm.runInContext('finiteMetric(0)', context), 0);
});

test('map coordinates are normalized and can be recovered from final path data', () => {
    const context = loadDashboardContext();
    assert.deepEqual(
        Array.from(vm.runInContext('normalizeMapCoords([106.66, 10.76])', context)),
        [10.76, 106.66]
    );
    const coords = vm.runInContext(`(() => {
        const index = {};
        mergePathNodeCoords(index, [100, 200], [[10.7, 106.6], [10.8, 106.7]]);
        return index;
    })()`, context);
    assert.deepEqual(Array.from(coords['100']), [10.7, 106.6]);
    assert.deepEqual(Array.from(coords['200']), [10.8, 106.7]);
});

test('misaligned path coordinates never get assigned to the wrong node', () => {
    const context = loadDashboardContext();
    const coords = vm.runInContext(`(() => {
        const index = {};
        mergePathNodeCoords(index, [100, 200, 300], [[10.7, 106.6], [10.8, 106.7]]);
        return index;
    })()`, context);
    assert.deepEqual(JSON.parse(JSON.stringify(coords)), {});
});

test('edge data builds a reusable coordinate index for trace nodes', () => {
    const context = loadDashboardContext();
    const coords = vm.runInContext(`(() => {
        const index = new Map();
        indexEdgeNodeCoords(index, {
            edge_id: '100_200',
            u_lat: 10.7,
            u_lng: 106.6,
            v_lat: 10.8,
            v_lng: 106.7
        });
        return [index.get('100'), index.get('200')];
    })()`, context);
    assert.deepEqual(Array.from(coords[0]), [10.7, 106.6]);
    assert.deepEqual(Array.from(coords[1]), [10.8, 106.7]);
});

test('decimal-form node IDs from Pandas match JavaScript integer IDs', () => {
    const context = loadDashboardContext();
    const result = vm.runInContext(`(() => {
        const nodeId = 1997154435;
        const trace = {
            visited_order: [nodeId],
            steps: [{ current_node: nodeId, frontier: [] }],
            node_coords: {}
        };
        mergeValidNodeCoords(trace.node_coords, {
            '1997154435.0': [10.752692, 106.668041]
        });
        const edgeCoords = new Map();
        indexEdgeNodeCoords(edgeCoords, {
            edge_id: '4631738599.0_1997154435.0',
            u_lat: 10.76,
            u_lng: 106.67,
            v_lat: 10.752692,
            v_lng: 106.668041
        });
        return {
            coordinateKey: normalizeNodeCoordinateKey('1997154435.0'),
            missing: getMissingTraceNodeIds(trace),
            edgeCoords: edgeCoords.get('1997154435')
        };
    })()`, context);

    assert.equal(result.coordinateKey, '1997154435');
    assert.deepEqual(Array.from(result.missing), []);
    assert.deepEqual(Array.from(result.edgeCoords), [10.752692, 106.668041]);
});

test('missing coordinate detection includes visited, current and frontier nodes', () => {
    const context = loadDashboardContext();
    const missing = vm.runInContext(`getMissingTraceNodeIds({
        visited_order: [100, 200],
        steps: [{ current_node: 200, frontier: [{ node_id: 300 }] }],
        node_coords: { '100': [10.7, 106.6] }
    })`, context);
    assert.deepEqual(Array.from(missing), [200, 300]);
});

test('frontend exposes Hill Climbing and both backend visit-order methods', () => {
    const context = loadDashboardContext();
    assert.equal(
        vm.runInContext("ALGORITHM_SPECS.hill_climbing.label", context),
        'Hill Climbing'
    );
    assert.equal(
        vm.runInContext("visitOrderLabel('nearest_neighbor')", context),
        'Nearest Neighbor (xấp xỉ)'
    );
    assert.equal(
        vm.runInContext("visitOrderLabel('held_karp')", context),
        'Held–Karp (tối ưu)'
    );
});

test('frontier formatter includes costs, heuristic and selected candidate', () => {
    const context = loadDashboardContext();
    const label = vm.runInContext(
        "formatFrontierItem({ node_id: 7, g: 2, h: 3, f: 5, selected: true })",
        context
    );
    assert.match(label, /g=2\.00/);
    assert.match(label, /h=3\.00/);
    assert.match(label, /f=5\.00/);
    assert.match(label, /được chọn/);
});

test('missing coordinate detection also repairs every final-route node', () => {
    const context = loadDashboardContext();
    const missing = vm.runInContext(`getMissingTraceNodeIds({
        visited_order: [100],
        steps: [{ current_node: 100, frontier: [] }],
        route_segments: [{ path_nodes: [100, 200] }],
        node_coords: { '100': [10.7, 106.6] }
    })`, context);
    assert.deepEqual(Array.from(missing), [200]);
});

test('route progress only reveals final-path nodes expanded by the current step', () => {
    const context = loadDashboardContext();
    const routeNodes = vm.runInContext(`getRouteNodesAtSearchStep({
        route_segments: [{ path_nodes: [1, 2, 3, 4] }],
        steps: [
            { legIndex: 1, current_node: 1 },
            { legIndex: 1, current_node: 99 },
            { legIndex: 1, current_node: 3 }
        ]
    }, 2)`, context);
    assert.deepEqual(Array.from(routeNodes), [1, 2, 3]);
});

test('route prefix stays visible while a search branch is expanded', () => {
    const context = loadDashboardContext();
    const routeNodes = vm.runInContext(`getRouteNodesAtSearchStep({
        route_segments: [{ path_nodes: [1, 2, 3] }],
        steps: [
            { legIndex: 1, current_node: 1 },
            { legIndex: 1, current_node: 99 }
        ]
    }, 1)`, context);
    assert.deepEqual(Array.from(routeNodes), [1]);
});

test('route line keeps gaps for unresolved coordinates instead of joining across them', () => {
    const context = loadDashboardContext();
    const segments = vm.runInContext(
        'buildCoordinateSegments([[10.7, 106.6], null, [10.8, 106.7]])',
        context,
    );
    assert.deepEqual(
        JSON.parse(JSON.stringify(segments)),
        [[[10.7, 106.6]], [[10.8, 106.7]]],
    );
});

test('missing final-route coordinates are interpolated on the client', () => {
    const context = loadDashboardContext();
    const coords = vm.runInContext(`(() => {
        const trace = {
            route_segments: [{ path_nodes: [100, 200, 300] }],
            node_coords: { '100': [10.7, 106.6], '300': [10.9, 106.8] }
        };
        estimateMissingRouteCoordinates(trace);
        return trace.node_coords['200'];
    })()`, context);
    assert.ok(Math.abs(coords[0] - 10.8) < 1e-12);
    assert.ok(Math.abs(coords[1] - 106.7) < 1e-12);
});

test('renderExplanation populates narrative and all 5 evaluation criteria points', () => {
    const context = loadDashboardContext();
    const elements = vm.runInContext(`(() => {
        const store = {};
        byId = (id) => {
            if (!store[id]) store[id] = { textContent: '', innerHTML: '' };
            return store[id];
        };
        const aggregate = {
            visitingOrder: [101, 202],
            totalCost: 15.5,
            totalDistance: 2500,
            totalTravelTime: 300,
            totalHops: 4,
            segments: [{ result: {} }],
            congestion: {
                highCongestionEdges: [{ edgeId: 'e1', name: 'Đường Nguyễn Huệ', level: 5 }],
                averageKnownLevel: 2.8
            }
        };
        const input = {
            algorithm: 'astar',
            criterion: 'cost',
            visitOrderMode: 'input'
        };
        renderExplanation(aggregate, input, ALGORITHM_SPECS.astar);
        return store;
    })()`, context);

    assert.ok(elements.routeNarrative.innerHTML.includes('A* Search'));
    assert.ok(elements.routeNarrative.innerHTML.includes('15.50'));
    assert.ok(elements.expWhyChosen.textContent.includes('A* Search'));
    assert.ok(elements.expMetricType.textContent.includes('TỔNG CHI PHÍ GIAO THÔNG'));
    assert.ok(elements.expCongestion.textContent.includes('Đường Nguyễn Huệ'));
    assert.ok(elements.expComparison.textContent.includes('Dijkstra'));
    assert.ok(elements.expOptimality.textContent.includes('admissible'));
});

test('normalizeSearchText strips accents and converts to lowercase', () => {
    const context = loadDashboardContext();
    const result = vm.runInContext("normalizeSearchText('Bệnh Viện Chợ Rẫy - Đa Khoa')", context);
    assert.equal(result, 'benh vien cho ray - da khoa');
});

test('findLocationsByName searches hospitals and POIs by name or type', () => {
    const context = loadDashboardContext();
    const results = vm.runInContext(`(() => {
        hospitalsData = [
            { node_id: 101, name: 'Bệnh viện Chợ Rẫy', type: 'Hospital', is_hospital: true, is_emergency: true },
            { node_id: 102, name: 'Bệnh viện Từ Dũ', type: 'Hospital', is_hospital: true, is_emergency: false }
        ];
        poisData = [
            { node_id: 201, name: 'Trường ĐH Sư Phạm', type: 'University', is_hospital: false, is_emergency: false },
            { node_id: 202, name: 'Công viên 23/9', type: 'Park', is_hospital: false, is_emergency: false }
        ];
        return {
            choRay: findLocationsByName('cho ray'),
            tuDu: findLocationsByName('Từ Dũ'),
            suPham: findLocationsByName('su pham'),
            empty: findLocationsByName('không tồn tại 12345')
        };
    })()`, context);

    assert.equal(results.choRay.length, 1);
    assert.equal(results.choRay[0].node_id, 101);
    assert.equal(results.choRay[0].is_emergency, true);

    assert.equal(results.tuDu.length, 1);
    assert.equal(results.tuDu[0].node_id, 102);

    assert.equal(results.suPham.length, 1);
    assert.equal(results.suPham[0].node_id, 201);

    assert.equal(results.empty.length, 0);
});

test('waypoint stops can be added, moved and removed in order', () => {
    const context = loadDashboardContext();
    const state = vm.runInContext(`(() => {
        selectedWaypoints = [];
        byId = () => null;
        showToast = () => {};
        getNodeLabel = (id) => 'Node ' + id;

        addWaypoint(101);
        addWaypoint(202);
        addWaypoint(303);

        const afterAdd = [...selectedWaypoints];
        moveWaypoint(0, 1); // Move 101 down
        const afterMove = [...selectedWaypoints];

        removeWaypoint(101); // Remove 101
        const afterRemove = [...selectedWaypoints];

        clearAllWaypoints();
        const afterClear = [...selectedWaypoints];

        return { afterAdd, afterMove, afterRemove, afterClear };
    })()`, context);

    assert.deepEqual(Array.from(state.afterAdd), [101, 202, 303]);
    assert.deepEqual(Array.from(state.afterMove), [202, 101, 303]);
    assert.deepEqual(Array.from(state.afterRemove), [202, 303]);
    assert.deepEqual(Array.from(state.afterClear), []);
});
