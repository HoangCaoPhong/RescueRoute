"""Generate publication-ready benchmark charts from RescueRoute benchmark artifacts."""

from __future__ import annotations

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def generate_plots(artifact_dir: Path | None = None) -> list[Path]:
    if artifact_dir is None:
        artifact_dir = Path(__file__).resolve().parent.parent / "artifacts" / "benchmarks"

    # Find the most recent CSV results
    gs_files = sorted(artifact_dir.glob("graph-search-*.csv"))
    ms_files = sorted(artifact_dir.glob("multi-stop-*.csv"))

    if not gs_files or not ms_files:
        print(f"No benchmark CSV files found in {artifact_dir}")
        return []

    latest_gs = gs_files[-1]
    latest_ms = ms_files[-1]
    print(f"Reading {latest_gs.name} and {latest_ms.name}...")

    df_gs = pd.read_csv(latest_gs).sort_values("runtime_median_ms")
    df_ms = pd.read_csv(latest_ms).sort_values("runtime_median_ms")

    saved_files: list[Path] = []

    # -------------------------------------------------------------------------
    # 1. Combined 4-panel summary chart
    # -------------------------------------------------------------------------
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 9.5))
    fig.suptitle(
        "RescueRoute — Benchmark Thuật toán (Intel Core i5-9300H @ 2.40GHz, RAM 16GB, Win 11)",
        fontsize=14,
        fontweight="bold",
        y=0.98,
    )

    # Panel 1: Graph Search Runtime
    y_gs = np.arange(len(df_gs))
    colors_gs = ["#3498DB", "#2ECC71", "#1ABC9C", "#F39C12", "#E67E22", "#E74C3C"]
    bars1 = ax1.barh(y_gs, df_gs["runtime_median_ms"], color=colors_gs[:len(df_gs)], alpha=0.85, edgecolor="black", linewidth=0.7)
    for i, r in df_gs.reset_index().iterrows():
        med = r["runtime_median_ms"]
        p95 = r["runtime_p95_ms"]
        ax1.text(med + 0.3, i, f"{med:.2f} ms (p95: {p95:.2f})", va="center", fontsize=8.5, fontweight="bold")
    ax1.set_yticks(y_gs)
    ax1.set_yticklabels(df_gs["algorithm"], fontsize=9.5, fontweight="bold")
    ax1.set_xlabel("Median Wall-clock Time (ms)", fontsize=9.5)
    ax1.set_title("1. Tìm đường hai điểm: Thời gian thực thi (ms)", fontsize=11, fontweight="bold")
    ax1.set_xlim(0, max(df_gs["runtime_p95_ms"]) * 1.25)
    ax1.grid(True, linestyle="--", alpha=0.5)

    # Panel 2: Graph Search Peak Python Heap
    bars2 = ax2.barh(y_gs, df_gs["peak_python_heap_median_mib"], color="#34495E", alpha=0.85, edgecolor="black", linewidth=0.7)
    for i, r in df_gs.reset_index().iterrows():
        mem = r["peak_python_heap_median_mib"]
        ax2.text(mem + 0.03, i, f"{mem:.3f} MiB", va="center", fontsize=8.5)
    ax2.set_yticks(y_gs)
    ax2.set_yticklabels(df_gs["algorithm"], fontsize=9.5)
    ax2.set_xlabel("Peak Python Heap (MiB)", fontsize=9.5)
    ax2.set_title("2. Tìm đường hai điểm: Bộ nhớ đỉnh Python Heap (MiB)", fontsize=11, fontweight="bold")
    ax2.set_xlim(0, max(df_gs["peak_python_heap_median_mib"]) * 1.25)
    ax2.grid(True, linestyle="--", alpha=0.5)

    # Panel 3: Multi-Stop Runtime
    y_ms = np.arange(len(df_ms))
    colors_ms = ["#27AE60", "#2980B9", "#D35400", "#8E44AD"]
    bars3 = ax3.barh(y_ms, df_ms["runtime_median_ms"], color=colors_ms[:len(df_ms)], alpha=0.85, edgecolor="black", linewidth=0.7)
    for i, r in df_ms.reset_index().iterrows():
        med = r["runtime_median_ms"]
        p95 = r["runtime_p95_ms"]
        ax3.text(med + 0.3, i, f"{med:.2f} ms (p95: {p95:.2f})", va="center", fontsize=8.5, fontweight="bold")
    ax3.set_yticks(y_ms)
    ax3.set_yticklabels(df_ms["algorithm"], fontsize=9.5, fontweight="bold")
    ax3.set_xlabel("Median Wall-clock Time (ms)", fontsize=9.5)
    ax3.set_title("3. Tối ưu nhiều điểm dừng (6 WP): Thời gian (ms)", fontsize=11, fontweight="bold")
    ax3.set_xlim(0, max(df_ms["runtime_p95_ms"]) * 1.25)
    ax3.grid(True, linestyle="--", alpha=0.5)

    # Panel 4: Multi-Stop Cost Gap
    gaps = df_ms["cost_gap_to_oracle_pct"].fillna(0.0)
    gap_colors = ["#27AE60" if g == 0 else "#C0392B" for g in gaps]
    bars4 = ax4.barh(y_ms, gaps, color=gap_colors, alpha=0.85, edgecolor="black", linewidth=0.7)
    for i, r in df_ms.reset_index().iterrows():
        gap = r["cost_gap_to_oracle_pct"]
        cost = r["objective_cost"]
        if pd.notna(gap) and gap > 0:
            txt = f"+{gap:.2f}% ({cost:.1f}s)"
        else:
            txt = f"0.0% (Oracle: {cost:.1f}s)"
        ax4.text(max(0, gap) + 0.2, i, txt, va="center", fontsize=8.5, fontweight="bold")
    ax4.set_yticks(y_ms)
    ax4.set_yticklabels(df_ms["algorithm"], fontsize=9.5)
    ax4.set_xlabel("Cost Gap to Oracle (%)", fontsize=9.5)
    ax4.set_title("4. Tối ưu nhiều điểm dừng: Độ lệch chi phí so với Oracle (%)", fontsize=11, fontweight="bold")
    ax4.set_xlim(0, max(gaps) * 1.45 if max(gaps) > 0 else 10)
    ax4.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    summary_path = artifact_dir / "benchmark_summary.png"
    plt.savefig(summary_path, dpi=200, bbox_inches="tight")
    plt.close()
    saved_files.append(summary_path)
    print(f"Saved: {summary_path}")

    # -------------------------------------------------------------------------
    # 2. Graph Search Specific Plot
    # -------------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle("RescueRoute — Graph Search Benchmark (Tìm đường 2 điểm)", fontsize=13, fontweight="bold")

    ax1.barh(y_gs, df_gs["runtime_median_ms"], color=colors_gs[:len(df_gs)], alpha=0.85, edgecolor="black", linewidth=0.7)
    for i, r in df_gs.reset_index().iterrows():
        ax1.text(r["runtime_median_ms"] + 0.2, i, f"{r['runtime_median_ms']:.2f} ms", va="center", fontsize=9, fontweight="bold")
    ax1.set_yticks(y_gs)
    ax1.set_yticklabels(df_gs["algorithm"], fontsize=10, fontweight="bold")
    ax1.set_xlabel("Median Runtime (ms)")
    ax1.set_title("Thời gian thực thi (ms)", fontsize=11, fontweight="bold")
    ax1.set_xlim(0, max(df_gs["runtime_p95_ms"]) * 1.2)
    ax1.grid(True, linestyle="--", alpha=0.5)

    ax2.barh(y_gs, df_gs["peak_python_heap_median_mib"], color="#2C3E50", alpha=0.85, edgecolor="black", linewidth=0.7)
    for i, r in df_gs.reset_index().iterrows():
        ax2.text(r["peak_python_heap_median_mib"] + 0.03, i, f"{r['peak_python_heap_median_mib']:.3f} MiB", va="center", fontsize=9)
    ax2.set_yticks(y_gs)
    ax2.set_yticklabels(df_gs["algorithm"], fontsize=10)
    ax2.set_xlabel("Peak Heap Memory (MiB)")
    ax2.set_title("Bộ nhớ đỉnh Python Heap (MiB)", fontsize=11, fontweight="bold")
    ax2.set_xlim(0, max(df_gs["peak_python_heap_median_mib"]) * 1.25)
    ax2.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    gs_plot_path = artifact_dir / "benchmark_graph_search.png"
    plt.savefig(gs_plot_path, dpi=200, bbox_inches="tight")
    plt.close()
    saved_files.append(gs_plot_path)
    print(f"Saved: {gs_plot_path}")

    # -------------------------------------------------------------------------
    # 3. Multi-Stop Specific Plot
    # -------------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle("RescueRoute — Multi-Stop Optimization Benchmark (Tối ưu nhiều điểm dừng)", fontsize=13, fontweight="bold")

    ax1.barh(y_ms, df_ms["runtime_median_ms"], color=colors_ms[:len(df_ms)], alpha=0.85, edgecolor="black", linewidth=0.7)
    for i, r in df_ms.reset_index().iterrows():
        ax1.text(r["runtime_median_ms"] + 0.3, i, f"{r['runtime_median_ms']:.2f} ms", va="center", fontsize=9, fontweight="bold")
    ax1.set_yticks(y_ms)
    ax1.set_yticklabels(df_ms["algorithm"], fontsize=10, fontweight="bold")
    ax1.set_xlabel("Median Runtime (ms)")
    ax1.set_title("Thời gian thực thi (ms)", fontsize=11, fontweight="bold")
    ax1.set_xlim(0, max(df_ms["runtime_p95_ms"]) * 1.2)
    ax1.grid(True, linestyle="--", alpha=0.5)

    ax2.barh(y_ms, gaps, color=gap_colors, alpha=0.85, edgecolor="black", linewidth=0.7)
    for i, r in df_ms.reset_index().iterrows():
        gap = r["cost_gap_to_oracle_pct"]
        cost = r["objective_cost"]
        txt = f"+{gap:.2f}% ({cost:.1f}s)" if pd.notna(gap) and gap > 0 else f"0.0% ({cost:.1f}s)"
        ax2.text(max(0, gap) + 0.2, i, txt, va="center", fontsize=9, fontweight="bold")
    ax2.set_yticks(y_ms)
    ax2.set_yticklabels(df_ms["algorithm"], fontsize=10)
    ax2.set_xlabel("Cost Gap (%)")
    ax2.set_title("Độ lệch chi phí so với Oracle (%)", fontsize=11, fontweight="bold")
    ax2.set_xlim(0, max(gaps) * 1.45 if max(gaps) > 0 else 10)
    ax2.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    ms_plot_path = artifact_dir / "benchmark_multi_stop.png"
    plt.savefig(ms_plot_path, dpi=200, bbox_inches="tight")
    plt.close()
    saved_files.append(ms_plot_path)
    print(f"Saved: {ms_plot_path}")

    return saved_files


if __name__ == "__main__":
    generate_plots()
