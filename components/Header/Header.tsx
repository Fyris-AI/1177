import { ThemeAudienceToggle } from "./ThemeAudienceToggle";
import { ThemeModeToggle } from "./ThemeModeToggle";
import { SelectRegion } from "./SelectRegion";
import { HeaderLogo } from "./HeaderLogo";

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full bg-header-background backdrop-blur supports-[backdrop-filter]:bg-header-background/60">
      {/* Absolute positioned logo */}
      <div className="absolute left-0 top-0 h-full flex items-center pl-0">
        <HeaderLogo />
      </div>

      {/* Main header content */}
      <div className="grid grid-cols-[1fr_auto_1fr] items-center h-16 sm:h-20 md:px-4 ml-[280px]">
        {/* Left Section - now just contains SelectRegion */}
        <div className="flex items-center h-full px-2 sm:px-4 md:px-0 justify-start gap-4">
          <SelectRegion />
        </div>

        {/* Center Section */}
        <div className="text-[2rem] font-semibold sm:text-xl text-center text-title">
          {/* Fråga 1177 */}
        </div>

        {/* Right Section */}
        <div className="flex items-center h-full px-2 sm:px-4 md:px-0 justify-end gap-4">
          <ThemeAudienceToggle />
          <ThemeModeToggle />
        </div>
      </div>
    </header>
  );
}
