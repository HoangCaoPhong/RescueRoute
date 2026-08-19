interface AppHeaderProps {
  isDark: boolean;
  onToggleTheme: () => void;
  onOpenPlanner: () => void;
}

export function AppHeader({
  isDark,
  onToggleTheme,
  onOpenPlanner,
}: AppHeaderProps) {
  return (
    <header className="flex h-[72px] shrink-0 items-center justify-between border-b border-slate-200 bg-white px-5 dark:border-slate-800 dark:bg-slate-950 sm:px-7">
      <div className="min-w-0">
        <p className="truncate text-lg font-semibold tracking-tight text-slate-950 dark:text-white">
          Rescue<span className="text-route-600 dark:text-[#8ab4f8]">Route</span>
        </p>
        <p className="mt-0.5 hidden text-xs text-slate-500 sm:block dark:text-slate-400">
          Điều phối tuyến cấp cứu · Thành phố Hồ Chí Minh
        </p>
      </div>

      <nav className="flex items-center gap-2" aria-label="Điều hướng chính">
        <button
          type="button"
          className="btn-secondary lg:hidden"
          onClick={onOpenPlanner}
        >
          Lập tuyến
        </button>
        <button
          type="button"
          className="btn-secondary"
          onClick={onToggleTheme}
          aria-label={isDark ? "Chuyển sang giao diện sáng" : "Chuyển sang giao diện tối"}
        >
          {isDark ? "Giao diện sáng" : "Giao diện tối"}
        </button>
        <a className="btn-secondary hidden sm:inline-flex" href="/docs" target="_blank" rel="noreferrer">
          API
        </a>
      </nav>
    </header>
  );
}
