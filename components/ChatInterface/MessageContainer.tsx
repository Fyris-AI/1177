import React from "react";
import { AnimatePresence, motion } from "framer-motion";
import CitationButton from "./CitationButton";
import { Loader2 } from "lucide-react";
import { AppMessage } from "@/lib/types";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MessageContainerProps {
  messages: AppMessage[];
  error: string | null;
  isLoading: boolean;
  showCitation: (url: string) => void;
  messagesEndRef: React.RefObject<HTMLDivElement>;
}

interface CodeProps extends React.HTMLAttributes<HTMLElement> {
  inline?: boolean;
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
              : "bg-muted text-foreground"
          }`}
        >
          <div
            className={`prose prose-sm dark:prose-invert max-w-none ${
              message.role === "user"
                ? "text-primary-foreground"
                : "text-foreground"
            }`}
          >
            {message.role === "user" ? (
              <div className="whitespace-pre-wrap overflow-wrap-break-word">
                {message.content}
              </div>
            ) : (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  // Style links to match the theme
                  a: ({ ...props }) => (
                    <a
                      {...props}
                      className={`${
                        message.role === "user"
                          ? "text-primary-foreground hover:text-primary-foreground/80"
                          : "text-primary hover:text-primary/80"
                      } underline`}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (props.href) {
                          showCitation(props.href);
                        }
                      }}
                    />
                  ),
                  // Style code blocks
                  code: ({ inline, ...props }: CodeProps) => (
                    <code
                      {...props}
                      className={`${
                        inline
                          ? "bg-muted/50 px-1.5 py-0.5 rounded text-sm"
                          : "block bg-muted/50 p-2 rounded my-2 text-sm"
                      }`}
                    />
                  ),
                  // Style blockquotes
                  blockquote: ({ ...props }) => (
                    <blockquote
                      {...props}
                      className="border-l-4 border-primary pl-4 my-2 italic"
                    />
                  ),
                  // Style lists
                  ul: ({ ...props }) => (
                    <ul {...props} className="list-disc pl-4 my-2" />
                  ),
                  ol: ({ ...props }) => (
                    <ol {...props} className="list-decimal pl-4 my-2" />
                  ),
                  // Style strong text
                  strong: ({ ...props }) => (
                    <strong {...props} className="font-semibold" />
                  ),
                  // Style emphasis text
                  em: ({ ...props }) => <em {...props} className="italic" />,
                }}
              >
                {message.content}
              </ReactMarkdown>
            )}
          </div>

          {message.role === "assistant" &&
            message.source_links &&
            message.source_names &&
            message.source_names.length === message.source_links.length && (
              <div className="mt-2 flex flex-wrap gap-2">
                {message.source_links.map((link, index) => (
                  <CitationButton
                    key={index}
                    url={link}
                    name={message.source_names![index]}
                    onPreview={showCitation}
                  />
                ))}
              </div>
            )}
        </div>
      </motion.div>
    );
  },
  (prev, next) =>
    prev.message.id === next.message.id &&
    prev.message.content === next.message.content
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
              <span>Thinking...</span>
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
