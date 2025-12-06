// Voice configuration for TTS (ElevenLabs) and speech recognition
// Replace placeholder voice IDs with actual ElevenLabs voice IDs

export type VoiceLanguage = 'sv' | 'en' | 'ar' | 'fi';

export interface VoiceConfig {
  id: string;
  name: string;
  locale: string; // BCP-47 locale for speech recognition
  elevenlabsVoiceId: string;
}

export const VOICE_CONFIG: Record<VoiceLanguage, VoiceConfig> = {
  sv: {
    id: 'sv',
    name: 'Svenska',
    locale: 'sv-SE',
    elevenlabsVoiceId: 'cLAH1kXlkAivJHxCW601', // Replace with actual ElevenLabs voice ID
  },
  en: {
    id: 'en',
    name: 'English',
    locale: 'en-US',
    elevenlabsVoiceId: 'c8GqgOMlDjKmhWVDfhvI', // Replace with actual ElevenLabs voice ID
  },
  ar: {
    id: 'ar',
    name: 'العربية',
    locale: 'ar-SA',
    elevenlabsVoiceId: 'B5xxC4eQoOFJnY4R5XkI', // Replace with actual ElevenLabs voice ID
  },
  fi: {
    id: 'fi',
    name: 'Suomi',
    locale: 'fi-FI',
    elevenlabsVoiceId: 'dlbXHgJnwobU5JdZ8F5M', // Replace with actual ElevenLabs voice ID
  },
};

export const DEFAULT_LANGUAGE: VoiceLanguage = 'sv';

export const VOICE_LANGUAGES = Object.keys(VOICE_CONFIG) as VoiceLanguage[];

