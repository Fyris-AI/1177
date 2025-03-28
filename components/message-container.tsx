import React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Message } from "ai";
import ProjectOverview from "./project-overview";
import { Loader2 } from "lucide-react";

interface MessageContainerProps {
  messages: Message[];
  error: string | null;
  toolCall: string | undefined;
  isLoading: boolean;
  showCitation: (id: string) => void;
  messagesEndRef: React.RefObject<HTMLDivElement>;
}

const MessageItem: React.FC<{
  message: Message;
  showCitation: (id: string) => void;
}> = React.memo(
  ({ message, showCitation }) => {
    const replaceCitationFlags = (response: string): JSX.Element => {
      const citationRegex = /【([^】]+)】/g;
      const parts: JSX.Element[] = [];
      let match;
      const citationMapping: Record<string, number> = {};
      let citationIndex = 1;

      let lastIndex = 0;
      while ((match = citationRegex.exec(response)) !== null) {
        const citationId = match[1];

        if (lastIndex < match.index) {
          parts.push(
            <span key={lastIndex}>
              {response.slice(lastIndex, match.index)}
            </span>
          );
        }

        if (!(citationId in citationMapping)) {
          citationMapping[citationId] = citationIndex++;
        }

        parts.push(
          <button
            key={`${citationId}-${Math.random() * 1000}`}
            onClick={() => showCitation(citationId)}
            className="underline text-muted-foreground hover:text-primary"
          >
            [{citationMapping[citationId]}]
          </button>
        );

        lastIndex = match.index + match[0].length;
      }

      if (lastIndex < response.length) {
        parts.push(<span key={lastIndex}>{response.slice(lastIndex)}</span>);
      }

      return <>{parts}</>;
    };
    return (
      <motion.div
        key={message.id}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        className={`max-w-3xl mx-auto px-4 flex ${
          message.role === "user" ? "justify-end" : "justify-start"
        }`}
      >
        <div
          className={`rounded-lg px-4 py-2 max-w-[85%] ${
            message.role === "user"
              ? "bg-primary text-primary-foreground"
              : "bg-muted"
          }`}
        >
          <div className="whitespace-pre-wrap overflow-wrap-break-word">
            {message.role === "assistant" ? (
              replaceCitationFlags(message.content)
            ) : (
              <span>{message.content}</span>
            )}
          </div>
        </div>
      </motion.div>
    );
  },
  (prev, next) => prev.message == next.message
);

MessageItem.displayName = "MessageItem";

// Use React.memo to prevent unnecessary re-renders
const MessageContainer: React.FC<MessageContainerProps> = React.memo(
  ({ messages, error, toolCall, isLoading, showCitation, messagesEndRef }) => {
    return (
      <div className="flex-1 overflow-y-auto space-y-4 w-full">
        {messages.length === 0 && (
          <div className="flex p-2 overflow-y-auto mb-4 space-y-4 justify-center items-center">
            <ProjectOverview />
          </div>
        )}
        <AnimatePresence initial={false}>
          {messages.map(
            (message: Message) =>
              message.content && (
                <MessageItem
                  key={message.id}
                  message={message}
                  showCitation={showCitation}
                />
              )
          )}
        </AnimatePresence>

        {/* Error Banner */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="flex justify-center"
          >
            <div className="flex items-center gap-2 rounded-lg px-4 py-2 bg-red-500 text-white">
              <span>{error}</span>
            </div>
          </motion.div>
        )}

        {isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex justify-center"
          >
            <div className="flex items-center gap-2 rounded-lg px-4 py-2 bg-muted">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>
                {toolCall === "getInformation"
                  ? "Getting information..."
                  : "Thinking..."}
              </span>
            </div>
          </motion.div>
        )}
        <div ref={messagesEndRef} />
      </div>
    );
  },
  (prev, next) =>
    prev.messages === next.messages &&
    prev.isLoading === next.isLoading &&
    prev.error === next.error
);

MessageContainer.displayName = "MessageContainer";

export default MessageContainer;
