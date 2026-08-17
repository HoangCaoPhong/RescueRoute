import os
import pandas as pd
import numpy as np

def enrich_segments():
    # Paths
    base_dir = os.path.dirname(os.path.dirname(__file__))
    segments_path = os.path.join(base_dir, 'data/raw/segments.csv')
    train_path = os.path.join(base_dir, 'data/processed/processed_train.csv')
    output_path = os.path.join(base_dir, 'data/processed/base_segments.csv')

    print("Loading datasets...")
    df_segments = pd.read_csv(segments_path)
    df_train = pd.read_csv(train_path)

    print("Calculating baseline values...")
    # It is mathematically flawed to average "time" because segments have different lengths!
    # Instead, we calculate the average velocity, congestion, and risk.
    avg_velocity_ms = df_train['actual_velocity'].mean()
    avg_congestion = df_train['congestion_factor'].mean()
    avg_risk = df_train['risk_factor'].mean()

    print(f"Baseline Velocity: {avg_velocity_ms:.2f} m/s")
    print(f"Baseline Congestion: {avg_congestion:.2f}")
    print(f"Baseline Risk: {avg_risk:.2f}")

    print("Enriching unmeasured segments...")
    # Fill missing max_velocity in segments with the average velocity (converted to km/h)
    avg_velocity_kmh = avg_velocity_ms * 3.6
    df_segments['max_velocity'] = df_segments['max_velocity'].fillna(avg_velocity_kmh)

    # Calculate time based on length and velocity (t = d/v)
    df_segments['velocity_ms'] = df_segments['max_velocity'] / 3.6
    df_segments['base_time'] = df_segments['length'] / df_segments['velocity_ms']

    df_segments['base_congestion'] = avg_congestion
    df_segments['base_risk'] = avg_risk

    # Scale time to [0, 5]
    min_time = df_segments['base_time'].min()
    max_time = df_segments['base_time'].max()
    if max_time > min_time:
        df_segments['scaled_time'] = 5.0 * (df_segments['base_time'] - min_time) / (max_time - min_time)
    else:
        df_segments['scaled_time'] = 0.0

    # Calculate the base cost
    def calc_cost(time, congestion, risk, parameters=(0.648, 0.23, 0.122)):
        return parameters[0]*time + parameters[1]*congestion + parameters[2]*risk

    df_segments['base_cost'] = df_segments.apply(
        lambda row: calc_cost(row['scaled_time'], row['base_congestion'], row['base_risk']), axis=1
    )

    # Save only the necessary columns
    df_base = df_segments[['s_node_id', 'e_node_id', 'length', 'base_time', 'base_cost']]
    df_base.to_csv(output_path, index=False)
    
    print(f"Successfully saved {len(df_base)} enriched base segments to {output_path}")

if __name__ == "__main__":
    enrich_segments()
