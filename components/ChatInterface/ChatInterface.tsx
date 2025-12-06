"use client";

import { ImperativePanelHandle } from "react-resizable-panels";
import { CitationWindowActions } from "./CitationWindowAction";
import { useRef, useEffect, useState } from "react";
import MessageContainer from "./MessageContainer";
import { useMediaQuery } from "react-responsive";
import CitationPreview from "./CitationPreview";
import { Button } from "@/components/ui/button";
import { Shield, RotateCcw } from "lucide-react";
import { VoiceLanguage, DEFAULT_LANGUAGE } from "@/lib/voice-config";
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
import { AppMessage, ClarifyingOption } from "@/lib/types";
import { nanoid } from 'nanoid';
import { useTheme } from "next-themes";
import { useAuth } from "@/lib/auth-context";

export default function ChatInterface() {
  const isLargeScreen = useMediaQuery({ minWidth: 768 });
  const { theme } = useTheme();
  const { isAuthenticated, journalData, user } = useAuth();

  const [messages, setMessages] = useState<AppMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [clarificationRound, setClarificationRound] = useState(0);
  const [conversationHistory, setConversationHistory] = useState<{role: string, content: string}[]>([]);
  const [lastRelevantDocs, setLastRelevantDocs] = useState<string[]>([]); // Cache relevant docs for follow-ups

  const [citationUrl, setcitationUrl] = useState<string | null>(null);
  const [isCitationShown, setIsCitationShown] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState<VoiceLanguage>(DEFAULT_LANGUAGE);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const citationPanelRef = useRef<ImperativePanelHandle>(null);

  const handleInputChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(event.target.value);
  };

  // Handle clicking on a clarifying option
  const handleOptionClick = async (option: ClarifyingOption) => {
    const optionText = `${option.id}) ${option.text}`;
    await sendMessage(optionText, clarificationRound + 1);
  };

  // Core message sending function
  const sendMessage = async (messageContent: string, newClarificationRound: number = clarificationRound) => {
    if (!messageContent.trim() || isLoading) return;

    setError(null);
    setIsLoading(true);

    const newUserMessage: AppMessage = { 
      id: nanoid(), 
      role: 'user', 
      content: messageContent 
    };

    setMessages(prev => [...prev, newUserMessage]); 
    const currentMessages = [...messages, newUserMessage];

    // Update conversation history for clarification tracking
    const newHistory = [...conversationHistory, { role: 'user', content: messageContent }];
    setConversationHistory(newHistory);

    const [mode, audience] = (theme || "light-invanare").split("-") as [
      "light" | "dark",
      "invanare" | "personal"
    ];

    try {
      // Check if this is a follow-up question (has previous history)
      const isFollowUp = conversationHistory.length > 0;
      
      // Include journal data if user is authenticated (for invånare audience only)
      const apiPayload = { 
        messages: currentMessages,
        audience: audience,
        journalData: (isAuthenticated && audience === "invanare" && journalData) ? journalData : null,
        clarificationRound: newClarificationRound,
        conversationHistory: newHistory,
        isFollowUp: isFollowUp,
        lastRelevantDocs: isFollowUp ? lastRelevantDocs : [] // Send cached docs for follow-ups
      }; 

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
        needs_clarification: assistantResponseData.needs_clarification || false,
        clarifying_question: assistantResponseData.clarifying_question || undefined,
        clarifying_options: assistantResponseData.clarifying_options || [],
        relevant_docs: assistantResponseData.relevant_docs || [],
      };

      setMessages(prev => [...prev, newAssistantMessage]);
      
      // Update conversation history with assistant response (persist across all questions)
      setConversationHistory(prev => [...prev, { role: 'assistant', content: assistantResponseData.message }]);
      
      // Cache relevant documents for follow-up questions
      if (assistantResponseData.relevant_docs && assistantResponseData.relevant_docs.length > 0) {
        setLastRelevantDocs(assistantResponseData.relevant_docs);
        console.log('Cached relevant docs for follow-up:', assistantResponseData.relevant_docs.length, 'documents');
      }
      
      // Update clarification round if assistant asked for clarification
      if (assistantResponseData.needs_clarification) {
        setClarificationRound(newClarificationRound + 1);
      } else {
        // Reset clarification round when we get a final answer, but KEEP conversation history
        setClarificationRound(0);
        // Don't clear conversationHistory - we want to remember previous Q&A for follow-ups
      }

    } catch (err: unknown) {
      console.error("Error fetching chat response:", err);
      setError(err instanceof Error ? err.message : "Ett oväntat fel uppstod vid hämtning av svar.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!input.trim() || isLoading) return;
    
    const messageToSend = input;
    setInput('');
    
    // If the last message was a clarifying question, continue that round
    // Otherwise, reset clarification round but keep conversation history for follow-ups
    const lastMessage = messages[messages.length - 1];
    const isContinuingClarification = lastMessage?.needs_clarification;
    
    await sendMessage(messageToSend, isContinuingClarification ? clarificationRound : 0);
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

  // Reset chat to start over
  const handleResetChat = () => {
    setMessages([]);
    setInput('');
    setError(null);
    setClarificationRound(0);
    setConversationHistory([]);
    setLastRelevantDocs([]);
    setcitationUrl(null);
    setIsCitationShown(false);
  };

  // Parse audience from theme
  const [, audience] = (theme || "light-invanare").split("-") as [
    "light" | "dark",
    "invanare" | "personal"
  ];

  // Show personalization banner only for invånare when authenticated
  const showPersonalizationBanner = isAuthenticated && audience === "invanare";

  return (
    <>
      <ResizablePanelGroup
        direction="horizontal"
        className="h-[calc(100vh-4rem)]"
      >
        <ResizablePanel id="chat-panel" order={1}>
          <div className="flex flex-col h-full bg-background">
            {/* Personalization banner */}
            {showPersonalizationBanner && (
              <div className="bg-green-500/10 border-b border-green-500/20 px-4 py-2 flex items-center justify-center gap-2">
                <Shield className="h-4 w-4 text-green-600" />
                <span className="text-sm text-green-700">
                  Inloggad som <strong>{user?.name}</strong> – dina svar är personliga baserat på din journal
                </span>
              </div>
            )}
            
            {messages.length === 0 && !isLoading ? (
              <>
                <div className="text-center py-10 sm:py-14 md:py-22">
                  <h2 className="text-2xl sm:text-3xl md:text-[2.5rem] font-semibold mt-[30vh] text-center text-title">
                    {showPersonalizationBanner && user?.name
                      ? `Hej ${user.name.split(' ')[0]}, vad kan jag hjälpa dig med?`
                      : "Vad kan jag hjälpa dig med?"}
                  </h2>
                  {showPersonalizationBanner && (
                    <p className="text-muted-foreground mt-4 text-sm">
                      Dina frågor kommer besvaras med hänsyn till din medicinska historik
                    </p>
                  )}
                </div>
                <div>
                  <ChatInput
                    input={input}
                    onInputChange={handleInputChange}
                    onSubmit={handleSubmit}
                    isLoading={isLoading}
                    selectedLanguage={selectedLanguage}
                    onLanguageChange={setSelectedLanguage}
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
                    selectedLanguage={selectedLanguage}
                    onOptionClick={handleOptionClick}
                  />
                </div>

                <div className="shrink-0 bg-background pr-[17px]">
                  <div className="flex justify-center mb-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleResetChat}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      <RotateCcw className="h-4 w-4 mr-2" />
                      Börja om chat
                    </Button>
                  </div>
                  <ChatInput
                    input={input}
                    onInputChange={handleInputChange}
                    onSubmit={handleSubmit}
                    isLoading={isLoading}
                    selectedLanguage={selectedLanguage}
                    onLanguageChange={setSelectedLanguage}
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
