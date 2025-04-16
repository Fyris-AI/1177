import { useAutosizeTextArea } from "../../hooks/use-autosize-textarea";
import { useEffect, useRef, useState } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Send } from "lucide-react";

interface ChatInputProps {
  input: string;
  onInputChange: (event: React.ChangeEvent<HTMLTextAreaElement>) => void;
  onSubmit: (event: React.FormEvent) => void;
  isLoading: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({
  input,
  onInputChange,
  onSubmit,
  isLoading,
}) => {
  const [isComposing, setIsComposing] = useState(false);
  const textAreaRef = useRef<HTMLTextAreaElement>(null);

  useAutosizeTextArea({
    ref: textAreaRef,
    maxHeight: 240,
    borderWidth: 1,
    dependencies: [input],
  });

  const handleKeyDown = (ev: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (isComposing) return;
    if (ev.key === "Enter" && !ev.shiftKey) {
      ev.preventDefault();
      const form = ev.currentTarget.form;
      if (form) {
        form.dispatchEvent(
          new Event("submit", { cancelable: true, bubbles: true })
        );
      }
    }
  };

  return (
    <div className="bg-background w-full p-4 max-w-3xl mx-auto">
      <form onSubmit={onSubmit} className="relative flex w-full items-center">
        <Textarea
          ref={textAreaRef}
          value={input}
          onChange={onInputChange}
          onKeyDown={handleKeyDown}
          onCompositionStart={() => setIsComposing(true)}
          onCompositionEnd={() => setIsComposing(false)}
          placeholder="Skriv en fråga..."
          disabled={isLoading}
          className="pr-14 resize-none bg-background text-base md:text-base lg:text-base"
          rows={1}
        />
        <div className="absolute right-3 top-3">
          <Button
            type="submit"
            size="icon"
            className="h-8 w-8"
            disabled={isLoading || !input.trim()}
            title="Send"
          >
            <Send className="h-5 w-5" />
          </Button>
        </div>
      </form>
    </div>
  );
};

export default ChatInput;
