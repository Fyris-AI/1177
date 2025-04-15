import React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Loader2, BookOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// Define the Message type locally (or import from ChatInterface.tsx)
interface Message {
  id: string; 
  role: 'user' | 'assistant' | 'system';
  content: string;
  context?: string[]; // Add optional context field
  createdAt?: Date; 
}

interface MessageContainerProps {
  messages: Message[]; // Now uses the local/correct Message type
  error: string | null;
  isLoading: boolean;
  showContext: (assistantMessageId: string) => void;
  messagesEndRef: React.RefObject<HTMLDivElement>;
}

const MessageItem: React.FC<{
  message: Message; // Uses local/correct type
  showContext: (assistantMessageId: string) => void;
}> = React.memo(
  ({ message, showContext }) => {
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
          className={`rounded-lg px-4 py-2 max-w-[85%] flex flex-col ${
            message.role === "user"
              ? "bg-primary text-primary-foreground"
              : "bg-muted"
          }`}
        >
          <div className="overflow-wrap-break-word mb-2 prose prose-sm dark:prose-invert max-w-none">
            {message.role === 'assistant' ? (
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    a: ({node, ...props}) => <a {...props} target="_blank" rel="noopener noreferrer" />,
                  }}
                >
                  {message.content}
                </ReactMarkdown>
             ) : (
               message.content
             )
            }
          </div>

          {message.role === 'assistant' && message.context && message.context.length > 0 && (
            <Button 
              variant="outline"
              size="sm"
              className="mt-2 self-start text-xs h-auto py-1 px-2 border-muted-foreground/50 text-muted-foreground hover:bg-muted-foreground/10"
              onClick={() => showContext(message.id)}
            >
              <BookOpen className="h-3 w-3 mr-1" />
              Read More
            </Button>
          )}
        </div>
      </motion.div>
    );
  },
  (prev, next) => prev.message.id === next.message.id && prev.message.content === next.message.content
);

MessageItem.displayName = "MessageItem";

const MessageContainer: React.FC<MessageContainerProps> = React.memo(
  ({ messages, error, isLoading, showContext, messagesEndRef }) => {
    return (
      <div className="flex-1 overflow-y-auto space-y-4 w-full">
        <AnimatePresence initial={false}>
          {messages.map(
            (message: Message) =>
              message.content && (
                <MessageItem
                  key={message.id}
                  message={message}
                  showContext={showContext}
                />
              )
          )}
        </AnimatePresence>

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
