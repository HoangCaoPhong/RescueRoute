const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

function loadDashboardContext() {
    const context = vm.createContext({
        console,
        document: {
            createElement: () => ({}),
            getElementById: () => null
        },
        fetch: async () => {
            throw new Error('Unexpected network call in unit test.');
        },
        navigator: {},
        performance: { now: () => 0 },
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
