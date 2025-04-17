import { openai } from '@ai-sdk/openai';
import { convertToCoreMessages, streamText, tool } from "ai";
import { z } from 'zod';

export const maxDuration = 30;

const mockSearchResultSchema = z.object({
  id: z.string(),
  text: z.string(),
  url: z.string().optional(),
});

export async function POST(req: Request) {
  try {
    const { messages } = await req.json();

    const result = await streamText({
      model: openai(process.env.OPENAI_MODEL || 'gpt-4o'),
      messages: convertToCoreMessages(messages),
      system: `Du är en expert på svensk sjukvård med tillgång till verifierade källor. Följ dessa regler exakt:

      ### KÄLLHANTERING
      För LUNGCANCER-frågor:
      1. Använd ALLTID verktyget 'getInformation'
      2. Formatera källhänvisning så här:
         - Placera ALLTID i slutet av svaret
         - Använd exakt detta format: 【käll-id】
         - ALLTID mellanslag innan eller efter hakparenteserna
         - Exempel: "Symtom inkluderar hosta.【1177-lungcancer-01】"

      ### SVARSSTRUKTUR
      För lungcancer-svar:
      1. Besvara frågan med fakta från källan
      2. Avsluta ALLTID med källhänvisning i specificerat format
      3. Håll svaret koncist (1-3 meningar)

      För övriga frågor:
      1. Ge direkt svar utan verktyg
      2. Inga källhänvisningar
      
      ### SPRÅKREGEL
      - Svara på samma språk som frågan
      - Använd enkelt och tydligt språk`,
      
      tools: {
        getInformation: tool({
          description: `Returnerar verifierad information om lungcancer från 1177`,
          parameters: z.object({ 
            question: z.string().describe("Användarens fråga om lungcancer"),
          }),
          execute: async () => { 
            return [{
              id: "1177-lungcancer-mock-01",
              text: "Lungcancer är en av de vanligaste cancerformerna i Sverige. Symtom kan inkludera långvarig hosta, andfåddhet, smärta i bröstet och oavsiktlig viktnedgång. Rökning är den största riskfaktorn.",
              url: "https://www.1177.se/sjukdomar--besvar/cancer/cancerformer/lungcancer/" 
            }];
          },
        }),
      },
    });
    
    return result.toDataStreamResponse();
  } catch (error: unknown) {
    console.error("API Route Error:", error);
    return new Response(
      JSON.stringify({ 
        error: error instanceof Error ? error.message : "Ett oväntat fel uppstod" 
      }), 
      { 
        status: 500, 
        headers: { 'Content-Type': 'application/json' } 
      }
    );
  }
}
