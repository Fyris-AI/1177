import type { Metadata } from "next";
import { ThemeProvider } from 'next-themes'

import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://ai-sdk-preview-rag.vercel.app"),
  title: "Retrieval-Augmented Generation Preview - Azure AI Search, Azure OpenAI, and Vercel AI SDK",
  description:
    "Augment language model generations with vector based retrieval using Azure AI Search, text generation from Azure OpenAI, and orchestration with Vercel AI SDK",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
