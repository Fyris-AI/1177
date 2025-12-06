import React, { useState, useRef, useCallback } from "react";
import { AnimatePresence, motion } from "framer-motion";
import CitationButton from "./CitationButton";
import { Loader2, Volume2, VolumeX, Square } from "lucide-react";
import { AppMessage, ClarifyingOption } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { VoiceLanguage, VOICE_CONFIG } from "@/lib/voice-config";

interface MessageContainerProps {
  messages: AppMessage[];
  error: string | null;
  isLoading: boolean;
  showCitation: (url: string) => void;
  messagesEndRef: React.RefObject<HTMLDivElement>;
  selectedLanguage: VoiceLanguage;
  onOptionClick?: (option: ClarifyingOption) => void;
}

// TTS playback state for each message
interface TTSState {
  isPlaying: boolean;
  isLoading: boolean;
  error: string | null;
}

const MessageItem: React.FC<{
  message: AppMessage;
  showCitation: (url: string) => void;
  selectedLanguage: VoiceLanguage;
  ttsState: TTSState;
  onPlayTTS: () => void;
  onStopTTS: () => void;
  onOptionClick?: (option: ClarifyingOption) => void;
  isLastMessage: boolean;
}> = React.memo(
  ({ message, showCitation, selectedLanguage, ttsState, onPlayTTS, onStopTTS, onOptionClick, isLastMessage }) => {
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

          {/* Clarifying options - only show on the last message */}
          {message.role === "assistant" &&
            message.needs_clarification &&
            message.clarifying_options &&
            message.clarifying_options.length > 0 &&
            isLastMessage &&
            onOptionClick && (
              <div className="mt-3 space-y-2">
                <p className="text-sm font-medium text-muted-foreground mb-2">
                  {message.clarifying_question || "Välj ett alternativ:"}
                </p>
                <div className="flex flex-col gap-2">
                  {message.clarifying_options.map((option) => (
                    <Button
                      key={option.id}
                      variant="outline"
                      className="justify-start text-left h-auto py-2 px-3 hover:bg-primary/10"
                      onClick={() => onOptionClick(option)}
                    >
                      <span className="font-semibold mr-2">{option.id})</span>
                      <span>{option.text}</span>
                    </Button>
                  ))}
                </div>
              </div>
            )}

          {/* TTS and Citation buttons - ONLY show for final answers, NOT for clarifying questions */}
          {message.role === "assistant" && !message.needs_clarification && (
            <div className="mt-2 flex flex-wrap gap-2 items-center">
              {/* TTS Play/Stop button */}
              <Button
                variant="ghost"
                size="sm"
                className="h-7 px-2 text-xs"
                onClick={ttsState.isPlaying ? onStopTTS : onPlayTTS}
                disabled={ttsState.isLoading}
                title={ttsState.isPlaying ? "Stop" : `Read aloud (${VOICE_CONFIG[selectedLanguage].name})`}
              >
                {ttsState.isLoading ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" />
                ) : ttsState.isPlaying ? (
                  <Square className="h-3.5 w-3.5 mr-1" />
                ) : (
                  <Volume2 className="h-3.5 w-3.5 mr-1" />
                )}
                {ttsState.isLoading ? "Loading..." : ttsState.isPlaying ? "Stop" : "Listen"}
              </Button>
              
              {ttsState.error && (
                <span className="text-xs text-destructive">{ttsState.error}</span>
              )}

              {/* Citation buttons */}
              {message.source_links &&
                message.source_names &&
                message.source_links.length > 0 && (
                  <>
                    {message.source_links.map((link, index) => (
                      <CitationButton
                        key={index}
                        link={link}
                        name={message.source_names?.[index] || `Källa ${index + 1}`}
                        onClick={showCitation}
                      />
                    ))}
                  </>
                )}
            </div>
          )}
        </div>
      </motion.div>
    );
  },
  (prev, next) =>
    prev.message.id === next.message.id &&
    prev.message.content === next.message.content &&
    prev.selectedLanguage === next.selectedLanguage &&
    prev.ttsState.isPlaying === next.ttsState.isPlaying &&
    prev.ttsState.isLoading === next.ttsState.isLoading &&
    prev.ttsState.error === next.ttsState.error &&
    prev.isLastMessage === next.isLastMessage
);

MessageItem.displayName = "MessageItem";

const MessageContainer: React.FC<MessageContainerProps> = React.memo(
  ({ messages, error, isLoading, showCitation, messagesEndRef, selectedLanguage, onOptionClick }) => {
    // Track TTS state for each message
    const [ttsStates, setTTSStates] = useState<Record<string, TTSState>>({});
    const audioRef = useRef<HTMLAudioElement | null>(null);
    const currentPlayingIdRef = useRef<string | null>(null);

    const getTTSState = useCallback((messageId: string): TTSState => {
      return ttsStates[messageId] || { isPlaying: false, isLoading: false, error: null };
    }, [ttsStates]);

    const updateTTSState = useCallback((messageId: string, updates: Partial<TTSState>) => {
      setTTSStates(prev => ({
        ...prev,
        [messageId]: { ...getTTSState(messageId), ...updates }
      }));
    }, [getTTSState]);

    const stopCurrentAudio = useCallback(() => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = '';
        audioRef.current = null;
      }
      if (currentPlayingIdRef.current) {
        updateTTSState(currentPlayingIdRef.current, { isPlaying: false });
        currentPlayingIdRef.current = null;
      }
    }, [updateTTSState]);

    const playTTS = useCallback(async (message: AppMessage) => {
      // Stop any currently playing audio
      stopCurrentAudio();

      const voiceId = VOICE_CONFIG[selectedLanguage].elevenlabsVoiceId;
      
      updateTTSState(message.id, { isLoading: true, error: null });
      currentPlayingIdRef.current = message.id;

      try {
        const response = await fetch('/api/tts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: message.content,
            voiceId: voiceId,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Failed to generate speech');
        }

        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        
        const audio = new Audio(audioUrl);
        audioRef.current = audio;

        audio.onended = () => {
          updateTTSState(message.id, { isPlaying: false });
          currentPlayingIdRef.current = null;
          URL.revokeObjectURL(audioUrl);
        };

        audio.onerror = () => {
          updateTTSState(message.id, { isPlaying: false, error: 'Playback error' });
          currentPlayingIdRef.current = null;
          URL.revokeObjectURL(audioUrl);
        };

        updateTTSState(message.id, { isLoading: false, isPlaying: true });
        await audio.play();

      } catch (err) {
        console.error('TTS error:', err);
        updateTTSState(message.id, { 
          isLoading: false, 
          isPlaying: false, 
          error: err instanceof Error ? err.message : 'TTS failed' 
        });
        currentPlayingIdRef.current = null;
      }
    }, [selectedLanguage, stopCurrentAudio, updateTTSState]);

    const stopTTS = useCallback((messageId: string) => {
      if (currentPlayingIdRef.current === messageId) {
        stopCurrentAudio();
      }
    }, [stopCurrentAudio]);

    return (
      <div className="flex-1 overflow-y-auto space-y-4 w-full pt-4">
        <AnimatePresence initial={false}>
          {messages.map(
            (message: AppMessage, index: number) =>
              message.content && (
                <MessageItem
                  key={message.id}
                  message={message}
                  showCitation={showCitation}
                  selectedLanguage={selectedLanguage}
                  ttsState={getTTSState(message.id)}
                  onPlayTTS={() => playTTS(message)}
                  onStopTTS={() => stopTTS(message.id)}
                  onOptionClick={onOptionClick}
                  isLastMessage={index === messages.length - 1}
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
    prev.error === next.error &&
    prev.selectedLanguage === next.selectedLanguage &&
    prev.onOptionClick === next.onOptionClick
);

MessageContainer.displayName = "MessageContainer";

export default MessageContainer;
