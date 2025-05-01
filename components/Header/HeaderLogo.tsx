"use client";

import Image from "next/image";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export const HeaderLogo = () => {
  const [mounted, setMounted] = useState(false);
  const { theme } = useTheme();
  const router = useRouter();

  const handleImageClick = () => {
    if (window.location.pathname === "/") {
      // Refresh the page if already on the homepage
      window.location.reload();
    } else {
      // Navigate to homepage without full reload
      router.push("/");
    }
  };

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted)
    return (
      <div className="h-full w-[280px] animate-pulse bg-gray-200 rounded" />
    );

  const audience =
    theme?.split("-")[1] === "personal" ? "personal" : "invanare";
  const logoSource = audience === "personal" ? "/kry.png" : "/kry.png";

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
      className="h-full w-auto object-contain cursor-pointer"
      onClick={handleImageClick}
    />
  );
};
