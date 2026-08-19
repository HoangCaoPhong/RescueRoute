import { useEffect, useState } from "react";

export function useTheme() {
  // Mỗi lần mở trang đều bắt đầu ở giao diện sáng; lựa chọn tối chỉ tồn tại trong phiên.
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDark);
    document.documentElement.style.colorScheme = isDark ? "dark" : "light";
  }, [isDark]);

  return {
    isDark,
    toggleTheme: () => setIsDark((current) => !current),
  };
}
