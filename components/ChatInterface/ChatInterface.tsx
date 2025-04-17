"use client";

import { ImperativePanelHandle } from "react-resizable-panels";
import { CitationWindowActions } from "./CitationWindowAction";
import { useRef, useEffect, useState } from "react";
import MessageContainer from "./MessageContainer";
import { useMediaQuery } from "react-responsive";
import CitationPreview from "./CitationPreview";
import { Button } from "@/components/ui/button";
import { ExternalLink } from "lucide-react";
import ChatInput from "./ChatInput";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { useChat } from "ai/react";
import { X } from "lucide-react";
import {
  Drawer,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerDescription,
  DrawerFooter,
} from "@/components/ui/drawer";

export default function ChatInterface() {
  const isLargeScreen = useMediaQuery({ minWidth: 768 });
  const [error, setError] = useState<string | null>(null);
  const [citationUrl, setcitationUrl] = useState<string | null>(null);
  const [isCitationShown, setIsCitationShown] = useState(false);

  const { messages, input, handleInputChange, handleSubmit, isLoading } =
    useChat({
      api: "/api/chat",
      onResponse: (response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
      },
      onError: (error: Error) => {
        console.error("API Error:", error);
        setError(error.message || "Ett oväntat fel uppstod");
      },
    });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const citationPanelRef = useRef<ImperativePanelHandle>(null);

  useEffect(() => {
    if (citationUrl) {
      citationPanelRef.current?.expand();
    } else {
      citationPanelRef.current?.collapse();
    }
  }, [citationUrl]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmitWithErrorReset = (event: React.FormEvent) => {
    setError(null);
    handleSubmit(event);
  };

  const showCitation = (url: string) => {
    setcitationUrl(url);
    setIsCitationShown(true);
  };

  const closeDrawer = () => {
    setIsCitationShown(false);
    setcitationUrl(null);
  };

  return (
    <>
      <ResizablePanelGroup
        direction="horizontal"
        className="h-[calc(100vh-4rem)]"
      >
        <ResizablePanel id="chat-panel" order={1}>
          <div className="flex flex-col h-full bg-background">
            {messages.length === 0 ? (
              <>
                <div className="text-center py-10 sm:py-14 md:py-22">
                  <h2 className="text-2xl sm:text-3xl md:text-[2.5rem] font-semibold mt-[30vh] text-center text-title">
                    Vad kan jag hjälpa dig med?
                  </h2>
                </div>
                <div>
                  <ChatInput
                    input={input}
                    onInputChange={handleInputChange}
                    onSubmit={handleSubmitWithErrorReset}
                    isLoading={isLoading}
                  />
                </div>
              </>
            ) : (
              <>
                <div className="h-full overflow-y-auto scrollbar-gutter-stable mask-fade-out">
                  <MessageContainer
                    messages={messages}
                    error={error}
                    isLoading={isLoading}
                    showCitation={showCitation}
                    messagesEndRef={messagesEndRef}
                  />
                </div>

                <div className="shrink-0 bg-background pr-[17px]">
                  <ChatInput
                    input={input}
                    onInputChange={handleInputChange}
                    onSubmit={handleSubmitWithErrorReset}
                    isLoading={isLoading}
                  />
                </div>
              </>
            )}
          </div>
        </ResizablePanel>
        {isLargeScreen && isCitationShown && <ResizableHandle withHandle />}
        {isLargeScreen && isCitationShown && (
          <ResizablePanel
            id="citation-panel"
            order={2}
            collapsible
            collapsedSize={0}
            ref={citationPanelRef}
            defaultSize={25}
            className="h-full flex flex-col"
          >
            <div className="p-2 pt-4 flex-1 flex flex-col min-h-0">
              {citationUrl ? (
                <div className="flex-1 min-h-0 pb-2 overflow-auto">
                  <CitationPreview url={citationUrl} className="h-full" />
                </div>
              ) : (
                <p className="flex-1 flex items-center justify-center">
                  Välj en källa för att se detaljer
                </p>
              )}
              <div className="pb-3 pt-1">
                {" "}
                <CitationWindowActions
                  citationUrl={citationUrl}
                  onClose={closeDrawer}
                />
              </div>
            </div>
          </ResizablePanel>
        )}
      </ResizablePanelGroup>

      <Drawer
        open={!isLargeScreen && isCitationShown}
        onOpenChange={closeDrawer}
      >
        <DrawerContent className="h-[85vh]">
          <DrawerHeader className="flex-1 overflow-hidden flex flex-col">
            <DrawerDescription className="flex-1 overflow-auto">
              {citationUrl ? (
                <CitationPreview url={citationUrl} className="h-full" />
              ) : (
                <div className="h-full flex items-center justify-center">
                  Ingen källa vald.
                </div>
              )}
            </DrawerDescription>
          </DrawerHeader>
          <DrawerFooter className="pb-3 pt-1">
            <CitationWindowActions
              citationUrl={citationUrl}
              onClose={closeDrawer}
            />
          </DrawerFooter>
        </DrawerContent>
      </Drawer>
    </>
  );
}
