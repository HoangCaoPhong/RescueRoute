- **`base_segments.csv`**: From `segments.csv` be enriched with `base_time` and `base_cost` based on average `actual_velocity` from `processed_train.csv`.
  - Columns: `s_node_id` (start node), `e_node_id` (end node), `length`, `base_time`, `base_cost`.
- **`full_processed_train.csv`**: `train.csv` + enriched with additional features like `congestion_factor`, `risk_factor`, and `actual_velocity`.
  - Columns: `df_train.column`, `date_str`, `congestion_factor`, `risk_factor`, `actual_velocity`, `time`.
- **`processed_train.csv`**: A condensed version of the `full_processed_train.csv` dataset focusing on key routing metrics like velocity, time, congestion, and risk.
  - Columns: `segment_id`, `s_node_id`, `e_node_id`, `period`, `actual_velocity`, `time`, `congestion_factor`, `risk_factor`.
- **`train_with_cost.csv`**: Legacy derived `train.csv` snapshot merged from
  `feature/mini-Q5-sample`, with an additional composite `cost` column. The
  current runtime recalculates costs from `processed_train.csv`; do not treat
  this file as the canonical HCMUS sample edge contract.
- **`nodes_with_poi_labels.csv`**: Geospatial data mapping nodes to nearby Points of Interest (POIs).
  - Columns: `_id`, `long`, `lat`, `poi_name`, `poi_label`, `distance_meters`.
