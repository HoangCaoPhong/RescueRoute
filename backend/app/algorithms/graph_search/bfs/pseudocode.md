Algorithm: Breadth-First Search (BFS)

Input:
    graph  - directed graph represented by adjacency list
    start  - starting node
    goal   - destination node

Output:
    path              - path from start to goal
    hop_count         - number of edges in the path
    explored_order    - order of expanded nodes
    explored_count    - number of expanded nodes

BEGIN

    IF start is not in graph OR goal is not in graph THEN
        RETURN no result
    END IF

    CREATE an empty FIFO queue
    ENQUEUE start into queue

    visited ← {start}

    parent[start] ← NULL

    explored_order ← empty list

    WHILE queue is not empty DO

        current ← DEQUEUE queue

        ADD current to explored_order

        IF current = goal THEN

            path ← reconstruct path using parent

            RETURN
                path
                hop_count = length(path) - 1
                explored_order
                explored_count = length(explored_order)

        END IF

        FOR each neighbor of current in graph DO

            IF neighbor is not in visited THEN

                ADD neighbor to visited

                parent[neighbor] ← current

                ENQUEUE neighbor into queue

            END IF

        END FOR

    END WHILE

    RETURN
        path = NULL
        hop_count = NULL
        explored_order
        explored_count

END