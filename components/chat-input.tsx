import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Send } from "lucide-react";

interface ChatInputProps {
  input: string;
  onInputChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onSubmit: (event: React.FormEvent) => void;
  isLoading: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ input, onInputChange, onSubmit, isLoading }) => (
  <div className="sticky bottom-0 bg-background w-full p-4 max-w-3xl mx-auto">
    <form onSubmit={onSubmit} className="flex gap-2">
      <Input
        value={input}
        onChange={onInputChange}
        placeholder="Send a message..."
        className="flex-1 border-2 text-base"
      />
      <Button
        disabled={isLoading || !input}
        type="submit"
        className="flex-shrink-0 p-2"
      >
        <Send className="h-5 w-5" />
      </Button>
    </form>
  </div>
);

export default ChatInput;
