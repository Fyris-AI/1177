"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export const HeaderLogo = () => {
  const [mounted, setMounted] = useState(false);
  const { theme } = useTheme();
  const router = useRouter();

  const handleClick = () => {
    if (window.location.pathname === "/") {
      window.location.reload();
    } else {
      router.push("/");
    }
  };

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted)
    return (
      <div className="h-full w-[200px] animate-pulse bg-gray-200 rounded" />
    );

  const audience =
    theme?.split("-")[1] === "personal" ? "personal" : "invanare";
  const isPersonal = audience === "personal";

  return (
    <div
      onClick={handleClick}
      className={`
        flex items-center gap-3 px-5 py-2 h-full cursor-pointer
        rounded-r-full transition-all duration-200
        ${isPersonal 
          ? "bg-[hsl(var(--blue))] hover:bg-[hsl(212,44%,35%)]" 
          : "bg-[hsl(var(--red))] hover:bg-[hsl(347,71%,38%)]"
        }
      `}
    >
      {/* Robot Doctor Icon */}
      <div className="relative flex-shrink-0">
        <svg
          viewBox="0 0 40 40"
          className="w-10 h-10 text-white"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
        >
          {/* Robot head */}
          <rect x="8" y="10" width="24" height="22" rx="4" fill="currentColor" opacity="0.2" stroke="currentColor" />
          {/* Eyes */}
          <circle cx="15" cy="19" r="3" fill="currentColor" />
          <circle cx="25" cy="19" r="3" fill="currentColor" />
          {/* Mouth/speaker */}
          <rect x="13" y="25" width="14" height="3" rx="1" fill="currentColor" opacity="0.6" />
          {/* Antenna */}
          <line x1="20" y1="10" x2="20" y2="5" stroke="currentColor" strokeWidth="2" />
          <circle cx="20" cy="4" r="2" fill="currentColor" />
          {/* Stethoscope cross */}
          <rect x="18" y="16" width="4" height="10" rx="1" fill="white" opacity="0.3" />
          <rect x="14" y="19" width="12" height="4" rx="1" fill="white" opacity="0.3" />
        </svg>
      </div>

      {/* Text */}
      <div className="flex items-center">
        <span className="text-white font-bold text-xl tracking-tight">
          Doctor Bot
        </span>
      </div>
    </div>
  );
};
