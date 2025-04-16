import * as React from "react";
import { useState, useEffect } from "react";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Search } from "lucide-react";

export const SelectRegion = () => {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    // Function to check screen width
    const checkScreenWidth = () => {
      setIsMobile(window.innerWidth < 470);
    };

    // Initial check
    checkScreenWidth();

    // Add event listener
    window.addEventListener("resize", checkScreenWidth);

    // Cleanup
    return () => window.removeEventListener("resize", checkScreenWidth);
  }, []);

  return (
    <Select defaultValue="uppsala">
      {isMobile ? (
        <SelectTrigger className="w-[40px] border-none bg-header-background text-header-text text-xs"></SelectTrigger>
      ) : (
        <SelectTrigger className="w-[128px] sm:w-[142px] border-none bg-header-background text-header-text text-xs sm:text-sm">
          <SelectValue placeholder="Uppsala" />
        </SelectTrigger>
      )}
      <SelectContent>
        <SelectGroup>
          <SelectLabel>Välj region</SelectLabel>
          <SelectItem value="blekinge">Blekinge</SelectItem>
          <SelectItem value="dalarna">Dalarna</SelectItem>
          <SelectItem value="gotland">Gotland</SelectItem>
          <SelectItem value="gävleborg">Gävleborg</SelectItem>
          <SelectItem value="halland">Halland</SelectItem>
          <SelectItem value="jamtland">Jämtland</SelectItem>
          <SelectItem value="jonkoping">Jönköping</SelectItem>
          <SelectItem value="kalmar">Kalmar</SelectItem>
          <SelectItem value="kronoberg">Kronoberg</SelectItem>
          <SelectItem value="norrbotten">Norrbotten</SelectItem>
          <SelectItem value="skane">Skåne</SelectItem>
          <SelectItem value="stockholm">Stockholm</SelectItem>
          <SelectItem value="sodermanland">Södermanland</SelectItem>
          <SelectItem value="uppsala">Uppsala</SelectItem>
          <SelectItem value="varmland">Värmland</SelectItem>
          <SelectItem value="vasterbotten">Västerbotten</SelectItem>
          <SelectItem value="vasternorrland">Västernorrland</SelectItem>
          <SelectItem value="vastmanland">Västmanland</SelectItem>
          <SelectItem value="vastra_gotaland">Västra Götaland</SelectItem>
          <SelectItem value="orebro">Örebro</SelectItem>
          <SelectItem value="ostergotland">Östergötland</SelectItem>
        </SelectGroup>
      </SelectContent>
    </Select>
  );
};
