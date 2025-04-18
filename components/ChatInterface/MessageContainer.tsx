import React from "react";
import { AnimatePresence, motion } from "framer-motion";
import CitationButton from "./CitationButton";
import { Loader2 } from "lucide-react";
import { AppMessage } from "@/lib/types";

interface MessageContainerProps {
  messages: AppMessage[];
  error: string | null;
  isLoading: boolean;
  showCitation: (url: string) => void;
  messagesEndRef: React.RefObject<HTMLDivElement>;
}

const MessageItem: React.FC<{
  message: AppMessage;
  showCitation: (url: string) => void;
}> = React.memo(
  ({ message, showCitation }) => {
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
            {message.content}
          </div>

          {message.role === "assistant" &&
            message.source_links &&
            message.source_names && (
              <div className="mt-2 flex flex-wrap gap-2">
                {message.source_links.map((link, index) => (
                  <CitationButton
                    key={index}
                    link={link}
                    name={message.source_names?.[index] || `Källa ${index + 1}`}
                    onClick={showCitation}
                  />
                ))}
              </div>
            )}
        </div>
      </motion.div>
    );
  },
  (prev, next) => prev.message.id === next.message.id && prev.message.content === next.message.content
);

MessageItem.displayName = "MessageItem";

const MessageContainer: React.FC<MessageContainerProps> = React.memo(
  ({ messages, error, isLoading, showCitation, messagesEndRef }) => {
    return (
      <div className="flex-1 overflow-y-auto space-y-4 w-full pt-4">
        <AnimatePresence initial={false}>
          {messages.map(
            (message: AppMessage) =>
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
            <div className="flex items-center gap-2 rounded-lg px-4 py-2 bg-destructive text-destructive-foreground">
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
              <span>Tänker...</span>
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
