"use client";

import { ImperativePanelHandle } from "react-resizable-panels";
import { useRef, useEffect, useState } from "react";
import MessageContainer from "./MessageContainer";
import { useMediaQuery } from "react-responsive";
import { Button } from "@/components/ui/button";
import ChatInput from "./ChatInput";
import CitationPreview from "./CitationPreview";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { X } from "lucide-react";
import {
  Drawer,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerDescription,
  DrawerFooter,
} from "@/components/ui/drawer";
import { AppMessage } from "@/lib/types";
import { nanoid } from 'nanoid';

export default function ChatInterface() {
  const isLargeScreen = useMediaQuery({ minWidth: 768 });

  const [messages, setMessages] = useState<AppMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [citationUrl, setcitationUrl] = useState<string | null>(null);
  const [isCitationShown, setIsCitationShown] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const citationPanelRef = useRef<ImperativePanelHandle>(null);

  const handleInputChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(event.target.value);
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!input.trim() || isLoading) return;

    setError(null);
    setIsLoading(true);

    const newUserMessage: AppMessage = { 
      id: nanoid(), 
      role: 'user', 
      content: input 
    };

    setMessages(prev => [...prev, newUserMessage]); 
    const currentMessages = [...messages, newUserMessage];
    setInput('');

    try {
      const apiPayload = { messages: currentMessages }; 

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(apiPayload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `API request failed with status ${response.status}`);
      }

      const assistantResponseData = await response.json();
      
      const newAssistantMessage: AppMessage = {
        id: nanoid(),
        role: 'assistant',
        content: assistantResponseData.message || "No message content received.",
        source_names: assistantResponseData.source_names || [],
        source_links: assistantResponseData.source_links || [],
      };

      setMessages(prev => [...prev, newAssistantMessage]); 

    } catch (err: unknown) {
      console.error("Error fetching chat response:", err);
      setError(err instanceof Error ? err.message : "Ett oväntat fel uppstod vid hämtning av svar.");
    } finally {
      setIsLoading(false);
    }
  };

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
            {messages.length === 0 && !isLoading ? (
              <>
                <div className="text-center py-8 sm:py-12 md:py-20 mb-4 md:mb-8">
                  <h2 className="text-2xl sm:text-3xl md:text-[2.5rem] font-semibold mt-8 sm:mt-12 md:mt-[20vh] text-center text-title">
                    Vad kan jag hjälpa dig med?
                  </h2>
                </div>
                <div>
                  <ChatInput
                    input={input}
                    onInputChange={handleInputChange}
                    onSubmit={handleSubmit}
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
                    onSubmit={handleSubmit}
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
            className="overflow-y-scroll h-full"
          >
            <div className="flex justify-between items-center p-4">
              <h3 className="font-bold">Källinformation:</h3>
              <button
                onClick={closeDrawer}
                className="text-muted-foreground hover:text-primary transition-colors"
                aria-label="Close"
              >
                <X />
              </button>
            </div>
            <div className="p-4">
              {citationUrl ? (
                <CitationPreview url={citationUrl} />
              ) : (
                <p>Välj en källa för att se detaljer</p>
              )}
            </div>
          </ResizablePanel>
        )}
      </ResizablePanelGroup>

      <Drawer
        open={!isLargeScreen && isCitationShown}
        onOpenChange={closeDrawer}
      >
        <DrawerContent>
          <DrawerHeader>
            <DrawerTitle>Källinformation:</DrawerTitle>
            <DrawerDescription className="h-[75vh] overflow-y-auto">
              {citationUrl ? (
                <CitationPreview url={citationUrl} />
              ) : (
                "Ingen källa vald."
              )}
            </DrawerDescription>
          </DrawerHeader>
          <DrawerFooter>
            <Button onClick={closeDrawer}>Stäng</Button>
          </DrawerFooter>
        </DrawerContent>
      </Drawer>
    </>
  );
}
