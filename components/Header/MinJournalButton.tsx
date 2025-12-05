"use client";

import { FileText, User } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

interface MinJournalButtonProps {
  onClick: () => void;
}

export function MinJournalButton({ onClick }: MinJournalButtonProps) {
  const { isAuthenticated, user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center gap-1 min-w-[2.5rem] md:basis-[5.8rem]">
        <div className="h-6 w-6 sm:h-8 sm:w-8 rounded-full bg-muted animate-pulse" />
        <div className="h-3 w-12 bg-muted rounded animate-pulse hidden md:block" />
      </div>
    );
  }

  return (
    <div
      onClick={onClick}
      className="flex flex-col items-center justify-center gap-1 cursor-pointer min-w-[2.5rem] md:basis-[5.8rem] hover:opacity-80 transition-opacity"
      title={isAuthenticated ? `Inloggad som ${user?.name}` : "Logga in"}
    >
      {isAuthenticated ? (
        <>
          <div className="relative">
            <FileText className="h-6 w-6 sm:h-8 sm:w-8 text-icon" />
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-header-background" />
          </div>
          <p className="text-xs text-header-text hidden md:block">Min Journal</p>
        </>
      ) : (
        <>
          <User className="h-6 w-6 sm:h-8 sm:w-8 text-icon" />
          <p className="text-xs text-header-text hidden md:block">Logga in</p>
        </>
      )}
    </div>
  );
}

