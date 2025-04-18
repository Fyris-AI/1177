// lib/types.ts
export interface AppMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string; // The main text message
  source_names?: string[]; // Optional source names from backend
  source_links?: string[]; // Optional source links from backend
} 