import { ThemeChanger } from "@/components/Header/ThemeChanger";

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="grid grid-cols-[minmax(100px,1fr)_auto_minmax(100px,1fr)] items-center h-12 sm:h-16 md:px-4">
        {/* Left Section */}
        <div className="flex items-center h-full px-2 sm:px-4 md:px-0 justify-start">
          <ThemeChanger />
        </div>

        {/* Center Section */}
        <div className="font-semibold text-lg sm:text-xl text-center">
          Fråga 1177
        </div>

        {/* Right Section */}
        <div className="flex items-center h-full px-2 sm:px-4 md:px-0 justify-end">
          {/* Empty for now */}
        </div>
      </div>
    </header>
  );
}
