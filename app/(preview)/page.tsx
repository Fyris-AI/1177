"use client";
import React, { useState } from "react";
import ChatInterface from "@/components/ChatInterface/ChatInterface";
import { Header } from "@/components/Header/Header";
import { LoginPage } from "@/components/Auth/LoginPage";
import { MinJournalPage } from "@/components/Journal/MinJournalPage";
import { useAuth } from "@/lib/auth-context";
import { useTheme } from "next-themes";

type ViewState = "chat" | "login" | "journal";

export default function Chat() {
  const [currentView, setCurrentView] = useState<ViewState>("chat");
  const { isAuthenticated } = useAuth();
  const { theme } = useTheme();

  // Parse audience from theme
  const [, audience] = (theme || "light-invanare").split("-") as [
    "light" | "dark",
    "invanare" | "personal"
  ];

  // Only show Min Journal button for "invånare" audience
  const showMinJournalButton = audience === "invanare";

  const handleMinJournalClick = () => {
    if (isAuthenticated) {
      setCurrentView("journal");
    } else {
      setCurrentView("login");
    }
  };

  const handleBackToChat = () => {
    setCurrentView("chat");
  };

  const handleLoginSuccess = () => {
    setCurrentView("journal");
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {currentView === "chat" && (
        <>
          <Header onMinJournalClick={showMinJournalButton ? handleMinJournalClick : undefined} />
          <main className="flex-1 min-h-0">
            <ChatInterface />
          </main>
        </>
      )}

      {currentView === "login" && (
        <>
          <Header />
          <main className="flex-1 min-h-0">
            <LoginPage onBack={handleBackToChat} onLoginSuccess={handleLoginSuccess} />
          </main>
        </>
      )}

      {currentView === "journal" && (
        <>
          <Header />
          <main className="flex-1 min-h-0">
            <MinJournalPage onBack={handleBackToChat} />
          </main>
        </>
      )}
    </div>
  );
}
