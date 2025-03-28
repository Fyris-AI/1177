"use client";

import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { useChat } from "ai/react";
import { useRef, useEffect, useState } from "react";
import { Moon, Send, Sun, X } from "lucide-react";
import { useTheme } from "next-themes";
import MessageContainer from "./message-container";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import ChatInput from "./chat-input";
import { ImperativePanelHandle } from "react-resizable-panels";
import { useMediaQuery } from 'react-responsive';
import { Drawer, DrawerContent, DrawerHeader, DrawerTitle, DrawerDescription, DrawerFooter } from '@/components/ui/drawer';

const ThemeChanger = () => {
  const [mounted, setMounted] = useState(false);
  const { theme, setTheme } = useTheme();

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  return (
    <div className="flex items-center space-x-2">
      <Sun className="h-[1.2rem] w-[1.2rem]" />
      <Switch
        checked={theme === "dark"}
        onCheckedChange={() => setTheme(theme === "dark" ? "light" : "dark")}
        aria-label="Toggle dark mode"
        className="data-[state=checked]:bg-muted-foreground data-[state=unchecked]:bg-muted-foreground"
      />
      <Moon className="h-[1.2rem] w-[1.2rem]" />
      <span className="sr-only">Toggle dark mode</span>
    </div>
  );
};

export default function ChatInterface() {
  const isLargeScreen = useMediaQuery({ minWidth: 768 });
  const [toolCall, setToolCall] = useState<string>();
  const [error, setError] = useState<string | null>(null);
  const [documentMap, setDocumentMap] = useState<Record<string, string>>({});
  const [currentCitation, setCurrentCitation] = useState<string | null>(null);
  const [isCitationShown, setIsCitationShown] = useState(false);
  const { messages, input, handleInputChange, handleSubmit, isLoading } =
    useChat({
      maxToolRoundtrips: 4,
      onToolCall({ toolCall }: { toolCall: { toolName: string } }) {
        setToolCall(toolCall.toolName);
      },
      onError: (error: any) => {
        console.error("API Error:", error); // Log the error
        const errorMessage = error.message ? JSON.parse(error.message)?.error : "An unexpected error occurred.";
        setError(errorMessage);
      },
    });
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const citationPanelRef = useRef<ImperativePanelHandle>(null);

  // expand the right panel when a citation is selected
  useEffect(() => {
    if (currentCitation) {
      citationPanelRef.current?.expand();
    } else {
      citationPanelRef.current?.collapse();
    }
  }, [currentCitation]);

  // Function to extract document IDs and maintain the mapping
  const extractAndMapDocuments = (messages: Array<any>) => {
    const newDocumentMap: Record<string, string> = {};

    messages.forEach((message: { role: string; toolInvocations?: Array<{ result?: Array<{ id: string; text: string }> }> }) => {
      if (message.role === "assistant" && message.toolInvocations) {
        message.toolInvocations.forEach((invocation: { result?: Array<{ id: string; text: string }> }) => {
          if (invocation.result) {
            invocation.result.forEach((item: { id: string; text: string }) => {
              if (typeof item === 'object' && item.id) {
                newDocumentMap[item.id] = item.text; // Assuming item has a `text` field
              }
            });
          }
        });
      }
    });

    setDocumentMap(prevMap => ({ ...prevMap, ...newDocumentMap }));
  };

  // Auto scroll to bottom when new messages arrive and extract documents
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    extractAndMapDocuments(messages);
  }, [messages]);

  const handleSubmitWithErrorReset = (event: React.FormEvent) => {
    setError(null);
    handleSubmit(event);
  };

  const showCitation = (id: string) => {
    const citationText = documentMap[id] || null;
    setCurrentCitation(citationText);
    setIsCitationShown(true);
  };

  const closeDrawer = () => {
    setIsCitationShown(false);
    setCurrentCitation(null);
  };

  return (
    <>
      <ResizablePanelGroup direction="horizontal">
        <ResizablePanel id="chat-panel">
          <div className="flex flex-col min-w-0 h-screen bg-background">
            <div className="flex flex-row justify-between items-center p-4">
              <ThemeChanger />
              <a
                href="https://github.com/Azure-Samples/azure-ai-vercel-rag-starter"
                className="text-sm text-muted-foreground hover:text-primary transition-colors duration-200"
                target="_blank"
                rel="noopener noreferrer"
              >
                Source Code
              </a>
            </div>
            <div className="text-center mb-4 md:mb-8">
              <h1 className="text-2xl font-bold mb-2">AI Chat</h1>
              <p className="text-sm text-muted-foreground">
                A minimal RAG chat application built with Azure AI Search, Azure
                OpenAI, and the Vercel AI SDK
              </p>
            </div>

            <MessageContainer
              messages={messages}
              error={error}
              toolCall={toolCall}
              isLoading={isLoading}
              showCitation={showCitation}
              messagesEndRef={messagesEndRef}
            />

            <ChatInput 
              input={input} 
              onInputChange={handleInputChange} 
              onSubmit={handleSubmitWithErrorReset}
              isLoading={isLoading}
            />
          </div>
        </ResizablePanel>
        {isLargeScreen && isCitationShown && <ResizableHandle withHandle />}
        {isLargeScreen && isCitationShown && (
          <ResizablePanel id="citation-panel" collapsible collapsedSize={0} ref={citationPanelRef} defaultSize={25} className="overflow-y-scroll h-screen">
            <div className="flex justify-between items-center p-4">
              <h3 className="font-bold">Citation Details:</h3>
              <button 
                onClick={closeDrawer}
                className="text-muted-foreground hover:text-primary transition-colors"
                aria-label="Close"
              >
                <X />
              </button>
            </div>
            <div className="p-4">
              {currentCitation ? (  
                  <div>
                    <p>{currentCitation}</p>
                </div>
            ) : (
                <p>Select a citation to view details</p>
            )}
            </div>
          </ResizablePanel>
        )}
      </ResizablePanelGroup>

      <Drawer open={!isLargeScreen && isCitationShown} onOpenChange={closeDrawer}>
        <DrawerContent>
          <DrawerHeader>
            <DrawerTitle>Citation Details</DrawerTitle>
            <DrawerDescription className="h-[50vh] overflow-y-auto">
              {currentCitation || "No citation selected."}
            </DrawerDescription>
          </DrawerHeader>
          <DrawerFooter>
            <Button onClick={closeDrawer}>Close</Button>
          </DrawerFooter>
        </DrawerContent>
      </Drawer>
    </>
  );
}
