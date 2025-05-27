import { ThemeModeToggle } from "./ThemeModeToggle";
import { SelectRegion } from "./SelectRegion";
import { HeaderLogo } from "./HeaderLogo";

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full bg-header-background">
      {/* Left positioned logo */}
      <div className="absolute left-0 top-0 h-full flex items-center pl-0">
        <HeaderLogo />
      </div>

      {/* Center title - absolutely positioned */}
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-0 sm:w-auto invisible sm:visible text-lg sm:text-xl md:text-2xl font-semibold text-center text-title overflow-hidden">
        Lambå Chatlas
      </div>

      {/* Main header content */}
      <div className="flex justify-between items-center h-16 sm:h-20 md:px-4 ml-[225px] sm:ml-[280px]">
        {/* Left Section */}
        <div className="flex items-center h-full px-0 sm:px-2 justify-start gap-0 sm:gap-2 md:gap-4">
          {/* <SelectRegion /> */}
        </div>

        {/* Right Section */}
        <div className="flex items-center h-full px-3 sm:px-4 md:px-0 justify-end gap-0 sm:gap-2 md:gap-4">
          <ThemeModeToggle />
        </div>
      </div>
    </header>
  );
}
