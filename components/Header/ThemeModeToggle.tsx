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

  const [mode, audience] = (theme || "light-invanare").split("-") as [
    "light" | "dark",
    "invanare" | "personal"
  ];

  const toggleMode = () => {
    const newTheme = `${mode === "dark" ? "light" : "dark"}-${audience}`;
    setTheme(newTheme);
  };

  return (
    <div
      onClick={toggleMode}
      className="flex flex-col items-center justify-center gap-1 cursor-pointer w-24"
    >
      {mode === "dark" ? (
        <Sun className="h-8 w-8 text-icon" />
      ) : (
        <Moon className="h-8 w-8 text-icon" />
      )}
      <p className="text-sm text-header-text">
        {mode === "dark" ? "Ljust läge" : "Mörkt läge"}
      </p>
    </div>
  );
};
