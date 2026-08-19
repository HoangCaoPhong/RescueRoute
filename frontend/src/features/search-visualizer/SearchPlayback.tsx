import { useEffect, useMemo, useState } from "react";
import type { SearchTrace } from "../../types/api";

interface SearchPlaybackProps {
  trace: SearchTrace | null;
  activeStep: number;
  onStepChange: (step: number) => void;
}

export function SearchPlayback({
  trace,
  activeStep,
  onStepChange,
}: SearchPlaybackProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const stepCount = trace?.steps.length ?? 0;

  useEffect(() => {
    setIsPlaying(false);
    onStepChange(0);
  }, [trace, onStepChange]);

  useEffect(() => {
    if (!isPlaying || stepCount < 2) return;
    const timer = window.setInterval(() => {
      onStepChange(activeStep >= stepCount - 1 ? 0 : activeStep + 1);
    }, 520);
    return () => window.clearInterval(timer);
  }, [activeStep, isPlaying, onStepChange, stepCount]);

  const current = trace?.steps[Math.min(activeStep, Math.max(0, stepCount - 1))];
  const frontierPreview = useMemo(
    () => current?.frontier.slice(0, 6).map((item) => item.node_id).join(", ") ?? "",
    [current],
  );

  if (!trace || !stepCount) return null;

  return (
    <section className="border-t border-slate-200 pt-6 dark:border-slate-800" aria-labelledby="trace-title">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Mô phỏng thuật toán</p>
          <h3 id="trace-title" className="mt-1 text-base font-semibold text-slate-950 dark:text-white">
            Bước {activeStep + 1} trên {stepCount}
          </h3>
        </div>
        <p className="text-right text-xs text-slate-500 dark:text-slate-400">
          {trace.frontier_kind.replaceAll("_", " ")}
        </p>
      </div>

      <input
        className="mt-5 w-full accent-route-600"
        type="range"
        min={0}
        max={Math.max(0, stepCount - 1)}
        value={Math.min(activeStep, stepCount - 1)}
        onChange={(event) => onStepChange(Number(event.target.value))}
        aria-label="Bước mô phỏng"
      />

      <div className="mt-3 grid grid-cols-3 gap-2">
        <button
          type="button"
          className={isPlaying ? "btn-primary justify-center" : "btn-secondary justify-center"}
          disabled={activeStep <= 0}
          onClick={() => onStepChange(Math.max(0, activeStep - 1))}
        >
          Trước
        </button>
        <button
          type="button"
          className="btn-secondary justify-center"
          onClick={() => setIsPlaying((currentValue) => !currentValue)}
        >
          {isPlaying ? "Tạm dừng" : "Phát"}
        </button>
        <button
          type="button"
          className="btn-secondary justify-center"
          disabled={activeStep >= stepCount - 1}
          onClick={() => onStepChange(Math.min(stepCount - 1, activeStep + 1))}
        >
          Sau
        </button>
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-4 rounded-xl bg-slate-50 p-4 text-sm dark:bg-slate-900">
        <div className="border-l-2 border-route-600 pl-3">
          <dt className="text-xs text-slate-500 dark:text-slate-400">Node đang xét</dt>
          <dd className="mt-1 font-medium text-slate-900 dark:text-white">{current?.current_node ?? "—"}</dd>
        </div>
        <div className="border-l-2 border-traffic-green pl-3">
          <dt className="text-xs text-slate-500 dark:text-slate-400">Kích thước frontier</dt>
          <dd className="mt-1 font-medium text-slate-900 dark:text-white">{current?.frontier_size ?? 0}</dd>
        </div>
        <div className="col-span-2 border-l-2 border-traffic-amber pl-3">
          <dt className="text-xs text-slate-500 dark:text-slate-400">Các node tiếp theo</dt>
          <dd className="mt-1 break-words font-mono text-xs text-slate-700 dark:text-slate-300">
            {frontierPreview || "Frontier trống"}
            {(current?.frontier.length ?? 0) > 6 ? " …" : ""}
          </dd>
        </div>
      </dl>
    </section>
  );
}
