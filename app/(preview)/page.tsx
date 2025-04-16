"use client";
import React from "react";
import ChatInterface from "@/components/ChatInterface/ChatInterface";
import { Header } from "@/components/Header/Header";

export default function Chat() {
  return (
    <div className="flex flex-col h-screen">
      <Header />
      <main className="flex-1 min-h-0">
        <ChatInterface />
      </main>
    </div>
  );
}
