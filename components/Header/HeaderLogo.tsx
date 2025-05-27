"use client";

import Image from "next/image";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export const HeaderLogo = () => {
  const [mounted, setMounted] = useState(false);
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

  return (
    <Image
      src="/1177_region_uppsala.png"
      alt="1177 Region Uppsala Logo"
      width={280}
      height={32}
      priority
      className="h-full w-auto object-contain cursor-pointer"
      onClick={handleImageClick}
    />
  );
};
