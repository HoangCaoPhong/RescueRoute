# RescueRoute — 10-Minute Product Demo Video Script

## Recording target

- **Duration:** exactly 10:00, with a safe editing range of 9:50–10:00.
- **Language:** English narration; the current Vietnamese interface may remain on screen.
- **Build used:** `origin/dev` at commit `5ce4110` (18 August 2026).
- **Format:** 1920×1080, 30 fps, clear cursor highlight, large browser zoom, captions enabled.
- **Positioning:** RescueRoute is an academic decision-support prototype, not an operational ambulance dispatch system.

The words under **Narration** are spoken. Text in square brackets is a production instruction and must not be read aloud.

## Suggested speaker allocation

| Speaker | Main responsibility in the video |
|---|---|
| Hoàng Cao Phong | Opening, system model, A*, Hill Climbing, conclusion |
| Võ Mỹ Ngọc | BFS, UCS, dashboard operation |
| Nguyễn Trung Kiên | DFS, search trace, explanation panel, limitations |
| Huỳnh Thái Hòa | Dijkstra, cost model, comparison, traffic experiment, benchmark |
| Lương Thiện Nhân | Multi-location algorithms and demo |

## Assets to prepare before recording

1. A title card with the product name, course, team number, and five members.
2. One team-designed directed graph—not copied from the lab handout—with these edges:
   `S→A:2`, `S→B:1`, `B→A:1`, `A→C:2`, `A→D:5`, `B→D:4`, `C→G:3`, `D→G:1`.
   Show heuristic values `h(S)=5`, `h(A)=4`, `h(B)=4`, `h(C)=3`, `h(D)=1`, `h(G)=0`.
3. One multi-stop matrix animation with locations `S, P, Q, R, G`. It must make the nearest-neighbor order `S–P–Q–R–G` cost 13 and the optimum `S–P–R–Q–G` cost 4.
4. A live dashboard started from the latest `dev` build. Use a map-click or a fictional test position; do not expose a member's real GPS location.
5. Use the validated fixture below, then rehearse it once in the intended recording time window because startup selects nearby traffic periods.
6. Keep a frozen screenshot or short recording of every live result as a fallback. Never invent a value if a live rerun differs.

### Validated live fixture

This fixture was checked on the stated build at 19:57 ICT on 18 August 2026:

- Simulated start: node `411926505` at the dashboard's default ambulance position.
- Destination: **Bệnh viện Nhân dân Gia Định - cơ sở 2**, node `2383425451`.
- Baseline A*: composite cost `29.27`, distance `1,818 m`, 38 path nodes, 769 expanded nodes. Runtime is machine-dependent and must be read live.
- Comparison: A* and UCS both returned cost `29.27`; Dijkstra returned the shorter `1,730 m` path at composite cost `33.27`; BFS happened to match the A*/UCS path; DFS returned a 425,056 m detour; Hill Climbing stopped at a local optimum.
- Multi-stop input order: **Chợ Rẫy** (`4616029234`) → **Quận 2** (`5738009472`) → **Nhi đồng 1** (`5057828618`) → Gia Định 2. Held–Karp changed the waypoint order to Chợ Rẫy → Nhi đồng 1 → Quận 2 and reduced the Dijkstra distance from `37,497 m` to `31,968 m`.
- Traffic edge: `411917839_2663926522`. Raising it to level 4 changed A* to a 40-node, `1,837 m` route with composite cost `30.70` in the validation run.

If any value differs during rehearsal, keep the same sentence structure but replace the value with the observed result.

---

## 0:00–0:25 — Problem and product

**Speaker:** Hoàng Cao Phong

**Screen:** [Title card for three seconds. Cut to an HCMC road map, an ambulance marker, hospitals, and a computed route.]

**Narration:**

> In an emergency, the nearest hospital is not always the fastest destination. One-way streets, congestion, road risk, and search strategy can change the decision. RescueRoute is our ambulance-routing prototype for Ho Chi Minh City. It compares six graph-search algorithms, optimizes multi-stop trips, and reveals how each route was discovered.

**On-screen caption:** `Academic prototype — not for operational dispatch`

## 0:25–0:50 — System and cost model

**Speaker:** Hoàng Cao Phong

**Screen:** [Animate: processed road data → directed weighted graph → FastAPI services → search/optimization algorithms → Leaflet dashboard. Display “52,425 road nodes; 84,629 directed edges” as the report-build runtime graph.]

**Narration:**

> We model roads as a directed graph: intersections are nodes and road segments are weighted edges. Our AHP-derived cost priorities are 0.648 for travel time, 0.230 for congestion, and 0.122 for risk. The current pipeline does not yet unify every term's scale and coverage, so this is a research cost—not a clinically validated score.

**On-screen formula:**

`cost ≈ 0.648 × time + 0.230 × congestion + 0.122 × risk`

## 0:50–3:10 — Step-by-step explanation of all six route algorithms

**Screen throughout:** [Use the prepared graph. Maintain three panels: current node, frontier/open list, and final parent path. Costs are illustrative units, not kilometres or seconds.]

### 0:50–1:15 — BFS

**Speaker:** Võ Mỹ Ngọc

**Narration:**

> Breadth-First Search uses a FIFO queue and minimizes edges, not weighted cost. Expanding S generates A and B. A adds C and D; B adds nothing new; and C generates G. The expansion order is S, A, B, C, D, G. Its parent path is S–A–C–G: three hops, cost seven—hop-optimal, but not cost-optimal.

**Overlay:** `Queue: [S] → [A,B] → [B,C,D] → [C,D] → [D,G] → [G]`

### 1:15–1:40 — DFS

**Speaker:** Nguyễn Trung Kiên

**Narration:**

> Depth-First Search uses a LIFO stack and follows one branch before backtracking. With our neighbour order, S chooses A, A chooses C, and C reaches G. It expands S, A, C, G and returns cost seven. A different order may return a very different route, with no hop or cost guarantee.

**Overlay:** `Stack/top first: [S] → [A,B] → [C,D,B] → [G,D,B]`

### 1:40–2:10 — UCS and Dijkstra

**Speakers:** Võ Mỹ Ngọc, then Huỳnh Thái Hòa

**Narration:**

> Uniform-Cost Search expands the smallest accumulated cost, g. After S, the open list contains B at one and A at two. A later creates C at four; D improves G from seven to six. The final route is S–B–D–G, cost six. With non-negative costs, UCS is cost-optimal.
>
> Dijkstra uses the same relaxation pattern here. In RescueRoute, Dijkstra minimizes distance, while UCS minimizes composite edge cost.

**Overlay:** `Open by g: {B:1,A:2} → {A:2,D:5} → {C:4,D:5} → {D:5,G:7} → {G:6}`

### 2:10–2:50 — A*

**Speaker:** Hoàng Cao Phong

**Narration:**

> A-star orders nodes by f equals g plus h. Expanding S gives B with g one, h four, f five, and A with two, four, six. B is first. After the tie at f six, A is expanded, then D generates G at g six. The order is S, B, A, D, G, and the route is S–B–D–G. It is optimal in this example. We do not claim universal optimality in production because the distance heuristic is not yet proven as a lower bound for composite cost.

**Overlay:** `B: g=1,h=4,f=5 | A: 2,4,6 | D: 5,1,6 | G: 6,0,6`

### 2:50–3:10 — Hill Climbing

**Speaker:** Hoàng Cao Phong

**Narration:**

> Hill Climbing keeps only the neighbour with smallest heuristic. The tie at S selects A, then D, then G. That route costs eight. It is fast and memory-light, but ignores accumulated cost and can reach a dead end or local optimum.

**Overlay:** `h: S(5) → A(4) → D(1) → G(0); route cost = 8`

## 3:10–3:50 — Step-by-step explanation of four multi-location algorithms

**Speaker:** Lương Thiện Nhân

**Screen:** [Replace the graph with the `S, P, Q, R, G` distance matrix. Animate the current permutation and running total.]

**Narration:**

> Multi-location routing first builds a pairwise cost matrix. Nearest Neighbour repeatedly chooses the cheapest unvisited stop; here it returns S–P–Q–R–G, cost thirteen. Held–Karp stores the cheapest partial order for each waypoint subset and last stop, reconstructing the exact matrix optimum S–P–R–Q–G, cost four. The Genetic Algorithm scores a seeded population, then uses selection, ordered crossover, mutation, and elitism. Simulated Annealing swaps stops and sometimes accepts a worse order according to its cooling probability. GA and SA reach four in this toy run, but remain approximate.

**On-screen caption:** `Exact: Held–Karp | Approximate: Nearest Neighbour, GA, SA`

## 3:50–4:10 — Live dashboard orientation

**Speaker:** Võ Mỹ Ngọc

**Screen:** [Full browser capture. Briefly point to start, destination, waypoints, visiting-order method, route algorithm, evaluation criterion, and the two main buttons.]

**Narration:**

> Now to the implementation. The dashboard provides a simulated start, hospital search, five interface waypoints, four visiting-order methods, six route algorithms, and four evaluation criteria. Its main actions are “Find Route” and “Compare Six Algorithms.”

## 4:10–5:10 — Live two-location A* demo and search trace

**Speaker:** Võ Mỹ Ngọc, with Nguyễn Trung Kiên for the final trace sentence

**Screen actions:**

1. [Use simulated start node `411926505`. Select “Bệnh viện Nhân dân Gia Định - cơ sở 2”, node `2383425451`.]
2. [Select `A*`, choose `Cost` as the evaluation criterion, and click **Tìm tuyến đường**.]
3. [Zoom to the route. Point to algorithm, route cost, distance, hop count, expanded nodes, and processing time.]
4. [Open the explanation card and path-node list.]
5. [Switch from final-route view to full search trace. Play slowly for three steps, then faster to completion. Pause once to point out current expansion, explored-tree edges, frontier, and the final path.]

**Narration:**

> We set a test start and hospital, select A-star, and request a route. The result reports objective cost, distance, road segments, expanded nodes, and backend time. We read this run's values from the screen. Dashboard travel time is a frontend estimate and may use a thirty-kilometre-per-hour fallback; it is not API execution time.
>
> The explanation panel separates objective, behaviour, result, and caveats. Full-trace mode shows real adjacent-edge expansions: the current node, generated frontier, explored tree, and final route. The search is inspectable, not a black box.

**Required live callout:** `Read the actual cost, distance, hops, expanded nodes, and execution time visible on screen.`

## 5:10–5:55 — Same-query comparison of six algorithms

**Speaker:** Huỳnh Thái Hòa

**Screen actions:** [Keep the same start and destination. Click **So sánh 6 thuật toán**. Sort or point across the rows without changing the input. Highlight at least one route-shape difference on the map.]

**Narration:**

> We run all six algorithms on the same query. The selected criterion highlights the best displayed value, but does not change each algorithm's objective. In our validated run, A-star and UCS tied at composite cost 29.27. Dijkstra found a shorter 1.730-kilometre route, but its composite cost was 33.27. BFS matched the A-star path only by coincidence, DFS made a huge detour, and Hill Climbing stopped locally. The trade-off comes from optimizing cost, distance, hops, traversal order, or local guidance—not from one algorithm being universally best.

**Rehearsal rule:** [If the live values differ, read the new values and preserve the same objective-versus-trade-off explanation.]

## 5:55–6:55 — Live multi-location optimization

**Speaker:** Lương Thiện Nhân

**Screen actions:**

1. [Keep the same start and destination. Add Chợ Rẫy, Quận 2, and Nhi đồng 1 in that order.]
2. [Select `Dijkstra`, `Distance`, and `Input order`. Run once and capture the visiting order and total distance.]
3. [Change only the visiting-order method to `Held–Karp`. Run again.]
4. [Point to original order, optimized order, objective cost, per-leg routes, and the complete path.]
5. [Briefly open the method selector to show Nearest Neighbour, Genetic Algorithm, and Simulated Annealing.]

**Narration:**

> One ambulance must now visit Chợ Rẫy, Quận 2, and Nhi đồng 1 before the destination. Manual order travels 37.497 kilometres. Changing only the visiting-order method to Held–Karp moves Nhi đồng 1 before Quận 2 and reduces the distance to 31.968 kilometres—a saving of 5.529 kilometres. The backend is exact for this pairwise Dijkstra matrix. Nearest Neighbour is a fast baseline; seeded GA and SA explore approximate alternatives. Matching Held–Karp once would not make them exact.

## 6:55–7:40 — Controlled traffic-condition test

**Speaker:** Huỳnh Thái Hòa

**Screen actions:**

1. [Return to the original two-location test and show the saved baseline route.]
2. [Open FastAPI Swagger at `/docs`. Use `POST /api/edges/congestion` with `edge_id: "411917839_2663926522"` and `congestion_level: 4`.]
3. [Return to the dashboard and rerun the same origin, destination, and algorithm. Show before and after side by side.]

**Narration:**

> To isolate traffic, we keep origin, destination, and A-star fixed. The congestion endpoint raises one preselected baseline edge to level four. This is an in-memory simulation, not live provider data. The route changes from 38 nodes and 1.818 kilometres to 40 nodes and 1.837 kilometres; composite cost rises from 29.27 to 30.70. A slightly longer corridor is now preferable to the congested edge. We start from a fresh server because updates are cumulative in this prototype.

**Rehearsal rule:** [If the time-filtered startup data produces a different result, read the observed before/after values; do not reuse these validation numbers.]

## 7:40–8:30 — Controlled benchmark evidence

**Speaker:** Huỳnh Thái Hòa

**Screen:** [Show a compact benchmark chart. Label it “Frozen HCMUS sample; median of controlled reruns; excludes file loading.”]

**Narration:**

> Live timings vary, so here is our frozen HCMUS benchmark. A-star's median was 1.003 milliseconds and it found the 89.048-second route under the benchmark's speed-bound assumptions. Dijkstra took 1.876 milliseconds and UCS 1.992 for the same value. BFS matched by coincidence, not by guarantee. DFS produced 4924.384 seconds, while Hill Climbing reached a dead end.
>
> On the fixed eight-location matrix, Held–Karp found exact cost 1595.914. Nearest Neighbour had a 9.776-percent gap, GA 11.574 percent, and SA matched the oracle in that seeded run while remaining approximate. Timings exclude file loading and matrix construction.

## 8:30–9:30 — Why the selected route was chosen, and current limits

**Speaker:** Nguyễn Trung Kiên

**Screen:** [Return to the A* result and explanation card. Then show four short limitation captions.]

**Narration:**

> The final route is selected according to the algorithm's objective: composite edge cost for A-star and UCS, distance for Dijkstra, and hops for BFS. We never call a path universally best without naming its objective and assumptions.
>
> Current limits matter. Traffic is sparse and mixed across time; cost terms lack one rigorous normalization; and risk is provisional. Production A-star still needs a composite-cost lower-bound proof. The graph has disconnected regions, while k-shortest alternatives and per-term route-cost breakdowns are not yet implemented. Those are necessary steps before real emergency use.

## 9:30–10:00 — Conclusion

**Speaker:** Hoàng Cao Phong

**Screen:** [Fast montage: graph trace, algorithm comparison, optimized waypoint order, before/after traffic route. Finish on title card with repository/build identifier.]

**Narration:**

> RescueRoute shows that search strategy changes route quality and computational behaviour. It combines explainable graph search, exact and approximate multi-location optimization, controlled comparison, and a visual trace on an HCMC road graph. Our main lesson is simple: a route is meaningful only when its objective, assumptions, and evidence are visible. Thank you.

---

## Final rehearsal checklist

- Record from the stated `dev` commit and show the commit ID once in the end card.
- Confirm `/api/health`, hospital loading, the chosen connected nodes, and all four prepared live runs before recording.
- Rehearse the six-algorithm comparison once and update the spoken values if the time-window data changes them.
- Restart the backend before the traffic scene, update the specified route edge only once, and confirm that the validated before/after route remains reproducible.
- Read values from the current screen; do not repeat the report's historical live-demo numbers as though they came from this run.
- Keep the benchmark slide clearly labelled as a frozen controlled sample, separate from the production dashboard.
- Do not call production A* universally optimal. Its formal guarantee is conditional on an admissible and consistent heuristic in compatible units.
- Do not call frontend travel time a backend metric or claim that the prototype consumes live traffic.
- Keep the custom algorithm example on screen long enough to show start, goal, expansion order, frontier/open list, `g`, `h`, `f`, and final route.
- Target 9:50 in rehearsal to leave ten seconds for natural pauses and editing.

## Technical verification note for the team

This script was aligned with the latest fetched `origin/dev@5ce4110`, not the older commit named in the report. At the time of review, the latest source passed **97 backend tests** and **21 frontend tests**. The current source exposes congestion updates through FastAPI, while the current HTML does not expose the older congestion controls; this is why the traffic scene uses Swagger. The dashboard's selected criterion is a comparison/multi-location criterion and does not change every single-route algorithm's intrinsic objective.
