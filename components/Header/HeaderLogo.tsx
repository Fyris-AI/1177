"use client";

import Image from "next/image";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

export const HeaderLogo = () => {
  const [mounted, setMounted] = useState(false);
  const { theme } = useTheme();

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted)
    return (
      <div className="h-full w-[280px] animate-pulse bg-gray-200 rounded" />
    );

  const audience =
    theme?.split("-")[1] === "personal" ? "personal" : "invanare";
  const logoSource =
    audience === "personal"
      ? "/1177_vardpersonal.png"
      : "/1177_region_uppsala.png";

  return (
    <Image
      src={logoSource}
      alt={
        audience === "personal"
          ? "1177 Vårdpersonal Logo"
          : "1177 Region Uppsala Logo"
      }
      width={280}
      height={32}
      priority
      className="h-full w-auto object-contain"
    />
  );
};
