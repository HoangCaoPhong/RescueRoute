# Raw Data

This directory contains the original, unprocessed data for the RescueRoute project.

> [!NOTE]
> These datasets are pulled directly from the Kaggle dataset "Traffic Flow data in Ho Chi Minh City, Viet Nam", authored by "Thanh Nguyen". This version is raw and has not been cleaned, processed, or modified in any way.

## Files

- **`nodes.csv`**: Contains geographical coordinates for the nodes in the traffic network.
  - Columns: `_id` (node ID), `long` (longitude), `lat` (latitude).
- **`segments.csv`**: Information about the road segments connecting the nodes.
  - Columns: `_id` (segment ID), `created_at`, `updated_at`, `s_node_id` (start node), `e_node_id` (end node), `length`, `street_id`, `max_velocity`, `street_level`, `street_name`, `street_type`.
- **`segment_status.csv`**: Traffic velocity records for specific segments at different times.
  - Columns: `_id`, `updated_at`, `segment_id`, `velocity`.
- **`train.csv`**: Training dataset containing traffic flow and Level of Service (LOS) observations over different periods.
  - Columns: `_id`, `segment_id`, `date`, `weekday`, `period`, `LOS`, `s_node_id`, `e_node_id`, `length`, `street_id`, `max_velocity`, `street_level`, `street_name`, `street_type`, `long_snode`, `lat_snode`, `long_enode`, `lat_enode`.
