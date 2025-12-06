// lib/types.ts

export interface ClarifyingOption {
  id: string; // e.g., "A", "B", "C"
  text: string; // The option text
}

export interface AppMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string; // The main text message
  source_names?: string[]; // Optional source names from backend
  source_links?: string[]; // Optional source links from backend
  // Clarifying question fields
  needs_clarification?: boolean;
  clarifying_question?: string;
  clarifying_options?: ClarifyingOption[];
  // Relevant docs for caching (used for follow-up questions)
  relevant_docs?: string[];
}