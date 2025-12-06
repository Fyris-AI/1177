import { useAutosizeTextArea } from "../../hooks/use-autosize-textarea";
import { useEffect, useRef, useState, useCallback } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Send, Mic, MicOff } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  VOICE_CONFIG,
  VOICE_LANGUAGES,
  VoiceLanguage,
} from "@/lib/voice-config";

// Type declarations for Web Speech API
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message?: string;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  onstart: (() => void) | null;
}

declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition;
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
}

interface ChatInputProps {
  input: string;
  onInputChange: (event: React.ChangeEvent<HTMLTextAreaElement>) => void;
  onSubmit: (event: React.FormEvent) => void;
  isLoading: boolean;
  selectedLanguage: VoiceLanguage;
  onLanguageChange: (language: VoiceLanguage) => void;
}

const ChatInput: React.FC<ChatInputProps> = ({
  input,
  onInputChange,
  onSubmit,
  isLoading,
  selectedLanguage,
  onLanguageChange,
}) => {
  const [isComposing, setIsComposing] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const [speechError, setSpeechError] = useState<string | null>(null);
  const textAreaRef = useRef<HTMLTextAreaElement>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  useAutosizeTextArea({
    ref: textAreaRef,
    maxHeight: 240,
    borderWidth: 1,
    dependencies: [input],
  });

  // Check for speech recognition support
  useEffect(() => {
    const SpeechRecognitionAPI =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    setSpeechSupported(!!SpeechRecognitionAPI);
  }, []);

  // Initialize speech recognition
  const startListening = useCallback(() => {
    const SpeechRecognitionAPI =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognitionAPI) {
      setSpeechError("Speech recognition not supported");
      return;
    }

    setSpeechError(null);
    const recognition = new SpeechRecognitionAPI();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = VOICE_CONFIG[selectedLanguage].locale;

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let finalTranscript = "";
      let interimTranscript = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }

      if (finalTranscript) {
        // Create synthetic event to update input
        const syntheticEvent = {
          target: { value: input + finalTranscript },
        } as React.ChangeEvent<HTMLTextAreaElement>;
        onInputChange(syntheticEvent);
      }
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error("Speech recognition error:", event.error);
      if (event.error === "not-allowed") {
        setSpeechError("Microphone access denied");
      } else if (event.error === "no-speech") {
        setSpeechError("No speech detected");
      } else {
        setSpeechError(`Error: ${event.error}`);
      }
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;
    recognition.start();
  }, [selectedLanguage, input, onInputChange]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    setIsListening(false);
  }, []);

  const toggleListening = useCallback(() => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [isListening, startListening, stopListening]);

  // Stop listening when language changes
  useEffect(() => {
    if (isListening) {
      stopListening();
    }
  }, [selectedLanguage]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, []);

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
    <div className="bg-background w-full p-4 pt-2 max-w-3xl mx-auto">
      {/* Language selector row */}
      <div className="flex items-center gap-2 mb-2">
        <Select
          value={selectedLanguage}
          onValueChange={(value) => onLanguageChange(value as VoiceLanguage)}
        >
          <SelectTrigger className="w-[140px] h-8 text-sm">
            <SelectValue placeholder="Language" />
          </SelectTrigger>
          <SelectContent>
            {VOICE_LANGUAGES.map((lang) => (
              <SelectItem key={lang} value={lang}>
                {VOICE_CONFIG[lang].name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {speechError && (
          <span className="text-xs text-destructive">{speechError}</span>
        )}
      </div>

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
          className="pr-24 resize-none bg-background text-base md:text-base lg:text-base"
          rows={1}
        />
        <div className="absolute right-3 top-3 flex items-center gap-1">
          {/* Dictation button */}
          {speechSupported && (
            <Button
              type="button"
              size="icon"
              variant={isListening ? "destructive" : "ghost"}
              className="h-8 w-8"
              onClick={toggleListening}
              disabled={isLoading}
              title={isListening ? "Stop dictation" : "Start dictation"}
            >
              {isListening ? (
                <MicOff className="h-5 w-5" />
              ) : (
                <Mic className="h-5 w-5" />
              )}
            </Button>
          )}
          {/* Send button */}
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
