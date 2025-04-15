"use client";

import { ImperativePanelHandle } from "react-resizable-panels";
import React, { useRef, useEffect, useState, FormEvent } from "react";
import MessageContainer from "./MessageContainer";
import { useMediaQuery } from "react-responsive";
import { Button } from "@/components/ui/button";
import ChatInput from "./ChatInput";
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
import ReactMarkdown from 'react-markdown';
import { Loader2 } from 'lucide-react';

// --- NEW: Type for formatted context status ---
type FormattedContextStatus = 
   | { status: 'idle' } // Not yet fetched
   | { status: 'loading' }
   | { status: 'error', error: string }
   | { status: 'success', formattedContext: string };
// --- END NEW Type ---

// Define message structure
interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  context?: string[]; // Raw context strings from the API for assistant messages
  createdAt?: Date;
}

// Define API response structure (matching backend)
interface ApiResponse {
  answer: string;
  sources: string[];
  context: string[]; // Raw context strings
}

// Define structure for the new formatting API response
interface FormatContextApiResponse {
    formattedContext: string; // Context formatted as Markdown with highlights
}

export default function ChatInterface() {
  const isLargeScreen = useMediaQuery({ minWidth: 768 });
  const [error, setError] = useState<string | null>(null);

  // --- State for the Drawer ---
  const [isContextDrawerOpen, setIsContextDrawerOpen] = useState(false);
  const drawerContentRef = useRef<HTMLDivElement>(null);
  // --- End Drawer State ---

  // --- ADD State for which drawer is open ---
  const [openedDrawerMessageId, setOpenedDrawerMessageId] = useState<string | null>(null);
  // --- END Add State ---

  // --- State for Messages and Input ---
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  // --- End Message/Input State ---

  // --- State for Pre-loaded Formatted Context (Keep This) ---
  const [formattedContextMap, setFormattedContextMap] = useState<Record<string, FormattedContextStatus>>({});
  // --- END State ---

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll chat messages to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // --- Scroll to highlighted context in drawer (UPDATED) ---
  useEffect(() => {
    // Only scroll if a drawer is open and we have its ID
    if (isContextDrawerOpen && openedDrawerMessageId && drawerContentRef.current) {
      // Get the status from the map for the open drawer
      const status = formattedContextMap[openedDrawerMessageId];
      // Check if the status is success (meaning content is loaded)
      if (status?.status === 'success') {
          // Find the highlighted element (strong tag)
          const highlightedElement = drawerContentRef.current.querySelector('strong');
          if (highlightedElement) {
              // Scroll smoothly into view
              highlightedElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }
      }
    }
    // Dependencies: run when drawer opens/closes, ID changes, or map updates
  }, [isContextDrawerOpen, openedDrawerMessageId, formattedContextMap]); 
  // --- End scroll effect ---

  // --- Manual Input Handler (Keep This) ---
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement> | React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
  };
  // --- End Manual Input Handler ---

  // --- Function to fetch formatted context (Keep This) ---
  const fetchFormattedContext = async (userMessage: Message, assistantMessage: Message) => {
    if (!assistantMessage.context || assistantMessage.context.length === 0) {
        // No context to format, maybe store an 'empty' state or do nothing
        setFormattedContextMap(prevMap => ({ 
          ...prevMap, 
          [assistantMessage.id]: { status: 'success', formattedContext: 'No context was retrieved for this message.' }
        }));
        return;
    }
    
    // Set loading state for this specific message
    setFormattedContextMap(prevMap => ({ ...prevMap, [assistantMessage.id]: { status: 'loading' } }));

    try {
        const response = await fetch('http://localhost:8000/api/format-context', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: userMessage.content,
                answer: assistantMessage.content,
                context: assistantMessage.context,
            }),
        });

        if (!response.ok) {
            // Attempt to parse error message from backend JSON response
            let errorMsg = `API error: ${response.status}`;
            try {
                const errorData = await response.json();
                errorMsg = errorData.error || errorData.detail || errorMsg;
            } catch (parseError) {
                // If response is not JSON (e.g., HTML error page), use status text
                errorMsg = response.statusText || errorMsg;
            }
            throw new Error(errorMsg);
        }

        const result: FormatContextApiResponse = await response.json();
        // Store success state
        setFormattedContextMap(prevMap => ({ 
          ...prevMap, 
          [assistantMessage.id]: { status: 'success', formattedContext: result.formattedContext }
        }));

    } catch (error: any) {
        console.error("Context Formatting API Fetch Error (Pre-fetch):", error);
        // Store error state
        setFormattedContextMap(prevMap => ({ 
          ...prevMap, 
          [assistantMessage.id]: { status: 'error', error: error.message || "Failed to format context." }
        }));
    }
    // No finally block needed as loading state is per-message
  };
  // --- END NEW Function ---

  // --- Manual Submit Handler (Keep This) ---
  const handleSubmit = async (event?: FormEvent) => {
    if (event) event.preventDefault();
    if (!input.trim()) return;

    setError(null);
    setIsLoading(true); // Start loading main response

    const newUserMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      createdAt: new Date(),
    };

    const currentMessages = [...messages, newUserMessage];
    setMessages(currentMessages);
    setInput('');

    try {
      const response = await fetch('/api/chat', { // Assuming this endpoint is handled by Next.js itself
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ messages: currentMessages }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const result: ApiResponse = await response.json();

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(), // Consider a more robust ID generation
        role: 'assistant',
        content: result.answer,
        context: result.context, // Raw context
        createdAt: new Date(),
      };

      // Add assistant message to UI
      setMessages((prevMessages) => [...prevMessages, assistantMessage]);

      // --- Trigger pre-fetch for formatted context (fire and forget) ---
      if (assistantMessage.context && assistantMessage.context.length > 0) {
          fetchFormattedContext(newUserMessage, assistantMessage); 
      }
      // --- End Trigger ---

    } catch (error: any) {
      console.error("API Fetch Error:", error);
      setError(error.message || "Failed to fetch response from the API.");
    } finally {
      setIsLoading(false); // Stop loading main response
    }
  };
  // --- End Manual Submit Handler ---

  // --- Function to handle opening the context drawer (REVISED) ---
  const showContext = (assistantMessageId: string) => {
    setOpenedDrawerMessageId(assistantMessageId); // Set which message context to show
    setIsContextDrawerOpen(true); // Open the drawer
    // The drawer content will now be determined directly from formattedContextMap[assistantMessageId]
  };
  // --- End context drawer handler ---

  // --- Helper to get current status for rendering ---
  const getCurrentDrawerStatus = (): FormattedContextStatus | null => {
    if (!openedDrawerMessageId) return null;
    return formattedContextMap[openedDrawerMessageId] || null; // Return null if ID is set but no map entry yet
  };
  // --- End Helper ---

  return (
    <>
      <ResizablePanelGroup
        direction="horizontal"
        className="h-[calc(100vh-4rem)]"
      >
        <ResizablePanel id="chat-panel">
          <div className="flex flex-col h-full bg-background">
            {messages.length === 0 && !isLoading && (
              <div className="text-center py-20 mb-4 md:mb-8 flex-grow flex items-center justify-center">
                <h2 className="text-[2.5rem] font-semibold text-title">
                  Vad kan jag hjälpa dig med?
                </h2>
              </div>
            )}

            <MessageContainer
              messages={messages}
              error={error}
              isLoading={isLoading}
              showContext={showContext}
              messagesEndRef={messagesEndRef}
            />

            <ChatInput
              input={input}
              onInputChange={handleInputChange}
              onSubmit={handleSubmit}
              isLoading={isLoading}
            />
          </div>
        </ResizablePanel>
      </ResizablePanelGroup>

      <Drawer
        open={isContextDrawerOpen}
        // UPDATED onOpenChange
        onOpenChange={(isOpen) => {
          setIsContextDrawerOpen(isOpen);
          if (!isOpen) {
            setOpenedDrawerMessageId(null); // Clear ID when drawer is closed
          }
        }}
      >
        <DrawerContent>
          <DrawerHeader>
            <DrawerTitle>Retrieved Context</DrawerTitle>
            {/* UPDATED DrawerDescription Content */} 
            <DrawerDescription ref={drawerContentRef} asChild className="h-[60vh] overflow-y-auto pr-4 mt-4">
              <div>
                {(() => { // Immediately invoked function to determine content
                  const currentStatus = getCurrentDrawerStatus();

                  if (currentStatus?.status === 'loading' || (!currentStatus && openedDrawerMessageId)) {
                    // Show loading if explicitly loading OR if drawer is open for an ID but no status exists yet (implies loading initial state)
                    return (
                      <div className="flex items-center justify-center h-full">
                        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                        <span className="ml-2">Loading Formatted Context...</span>
                      </div>
                    );
                  } else if (currentStatus?.status === 'error') {
                    // Show error if status is error
                    return (
                      <div className="text-destructive p-4 border border-destructive rounded bg-destructive/10">
                        <p><strong>Error loading formatted context:</strong></p>
                        <p>{currentStatus.error}</p>
                      </div>
                    );
                  } else if (currentStatus?.status === 'success') {
                    // Show content if status is success
                    return (
                      <ReactMarkdown
                        className="prose prose-sm dark:prose-invert max-w-none"
                        components={{
                          a: ({ node, ...props }) => <a {...props} target="_blank" rel="noopener noreferrer" />,
                        }}
                      >
                        {currentStatus.formattedContext}
                      </ReactMarkdown>
                    );
                  } else {
                    // Fallback if drawer is somehow open without an ID or status
                    return <p>No context data available.</p>;
                  }
                })()}
              </div>
            </DrawerDescription>
            {/* END UPDATED DrawerDescription Content */} 
          </DrawerHeader>
          <DrawerFooter>
            <Button variant="outline" onClick={() => setIsContextDrawerOpen(false)}>Close</Button>
          </DrawerFooter>
        </DrawerContent>
      </Drawer>
    </>
  );
}
