"use client";

import { ArrowRightLeft } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

export const ThemeAudienceToggle = () => {
  const [mounted, setMounted] = useState(false);
  const { theme, setTheme } = useTheme();

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  const [mode, audience] = (theme || "light-invanare").split("-") as [
    "light" | "dark",
    "invanare" | "personal"
  ];

  const toggleAudience = () => {
    const newTheme = `${mode}-${
      audience === "personal" ? "invanare" : "personal"
    }`;
    setTheme(newTheme);
  };

  return (
    <div
      onClick={toggleAudience}
      className="flex flex-col items-center justify-center gap-1 cursor-pointer basis-[7rem]"
    >
      <ArrowRightLeft className="h-8 w-8 text-icon" />
      <p className="text-sm text-header-text">
        {audience === "personal" ? "För invånare" : "För vårdpersonal"}
      </p>
    </div>
  );
};
