"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

export const ThemeModeToggle = () => {
  const [mounted, setMounted] = useState(false);
  const { theme, setTheme, resolvedTheme } = useTheme();

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  const toggleMode = () => {
    setTheme(theme === "dark" ? "light" : "dark");
  };

  const isDark = resolvedTheme === "dark";

  return (
    <div
      onClick={toggleMode}
      className="flex flex-col items-center justify-center gap-1 cursor-pointer min-w-[2.5rem] md:basis-[4rem]"
    >
      {isDark ? (
        <Sun className="h-6 w-6 sm:h-8 sm:w-8 text-header-text" />
      ) : (
        <Moon className="h-6 w-6 sm:h-8 sm:w-8 text-header-text" />
      )}
      <p className="text-xs text-header-text hidden md:block">
        {isDark ? "Light mode" : "Dark mode"}
      </p>
    </div>
  );
};
