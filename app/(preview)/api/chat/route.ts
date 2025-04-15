import { openai } from '@ai-sdk/openai';
import { convertToCoreMessages, streamText, tool } from "ai";
import { z } from 'zod';

// Allow streaming responses up to 30 seconds
export const maxDuration = 30;

// Define the structure of our mock search result
const mockSearchResultSchema = z.object({
  id: z.string(),
  text: z.string(),
  url: z.string().optional(),
});

export async function POST(req: Request) {
  try {
    const { messages } = await req.json(); 

    const result = await streamText({
      model: openai(process.env.OPENAI_MODEL_NAME || 'gpt-4o'), 
      messages: convertToCoreMessages(messages),
      // Updated system prompt for testing citations
      system: `Du är en hjälpsam AI-assistent. Svara ALLTID på samma språk som frågan ställdes på.
      VIKTIGT FÖR TESTNING: Använd ALLTID verktyget 'getInformation' för att hämta information, oavsett frågans innehåll.
      När du svarar, se till att ALLTID citera den information du fick från verktyget genom att inkludera dess ID i formatet 【source_id】 i slutet av ditt svar.
      Basera ditt svar endast på informationen från verktyget.
      Om frågan handlar om lungcancer, använd informationen från verktyget. Annars, säg att du bara kan svara på frågor om lungcancer just nu baserat på den givna källan.`,
      tools: {
        getInformation: tool({
          description: `Hämta information från kunskapsbasen för att svara på användarens fråga. Använd detta ALLTID för testning.`,
          parameters: z.object({
            // Keep parameters simple as we ignore them anyway
            query: z.string().describe("Användarens fråga"), 
          }),
          // Execute function now returns hardcoded mock data
          execute: async ({ query }: { query: string }) => {
            console.log(`Tool 'getInformation' called with query: ${query}`);
            // Return a mock result simulating a search about lung cancer from 1177
            const mockResult = {
              id: "1177-lungcancer-mock-01",
              text: "Lungcancer är en av de vanligaste cancerformerna i Sverige. Symtom kan inkludera långvarig hosta, andfåddhet, smärta i bröstet och oavsiktlig viktnedgång. Rökning är den största riskfaktorn. Källa: 1177.se (simulerad)",
              url: "https://www.1177.se/sjukdomar--besvar/cancer/cancerformer/lungcancer/" 
            };
            // The AI SDK expects the tool execute function to return the data directly.
            // Wrap it in an array as search results are often lists.
            return [mockResult]; 
          },
        }),
      },
    });
    
    return result.toDataStreamResponse();
  } catch (error: unknown) {
    console.error("API Route Error:", error);
    const errorMessage = error instanceof Error ? error.message : "An unexpected error occurred.";
    return new Response(
      JSON.stringify({ error: errorMessage }), 
      { 
        status: 500, 
        headers: { 'Content-Type': 'application/json' } 
      }
    );
  }
}
