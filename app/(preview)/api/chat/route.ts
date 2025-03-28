import { findRelevantContent } from "@/lib/ai/search";
import { azure } from "@ai-sdk/azure";
import { convertToCoreMessages, generateObject, streamText, tool } from "ai";
import { z } from "zod";

// Allow streaming responses up to 30 seconds
export const maxDuration = 30;

export async function POST(req: Request) {
  try {
    const { messages } = await req.json();
    const result = await streamText({
      model: azure(process.env.AZURE_DEPLOYMENT_NAME!),
      messages: convertToCoreMessages(messages),
      system: `You are a helpful assistant acting as the users' second brain.
      Use tools on every request.
      Be sure to getInformation from your knowledge base before answering any questions.
      If a response requires multiple tools, call one tool after another without responding to the user.
      If a response requires information from an additional tool to generate a response, call the appropriate tools in order before responding to the user.
      ONLY respond to questions using information from tool calls.
      If no relevant information is found in the tool calls and information fetched from the knowledge base, respond, "Sorry, I don't know."
      Be sure to adhere to any instructions in tool calls ie. if they say to respond like "...", do exactly that.
      Keep responses short and concise. Answer in a single sentence where possible.
      If you are unsure, use the getInformation tool and you can use common sense to reason based on the information you do have.
      Use your abilities as a reasoning machine to answer questions based on the information you do have.

      Cite the sources using source ids at the end of the answer text, like 【234d987】, using the id of the source.

      Respond "Sorry, I don't know." if you are unable to answer the question using the information provided by the tools.
    `,
      tools: {
        getInformation: tool({
          description: `get information from your knowledge base to answer the user's question.`,
          parameters: z.object({
            question: z.string().describe("the users question"),
            similarQuestions: z.array(z.string()).describe("similar questions to the user's question. generate 3 similar questions to the user's question."),
          }),
          execute: async ({ similarQuestions }: { similarQuestions: string[] }) => {
            const results = await Promise.all(
              similarQuestions.map(
                async (question: string) => await findRelevantContent(question),
                ),
              );
            const uniqueResults = Array.from(
              new Map(results.flat().map((item) => [item?.text, item])).values(),
            );
            return uniqueResults;
          },
        }),
      },
    });

    return result.toDataStreamResponse();
  } catch (error: unknown) {
    console.error(error);
    return new Response(JSON.stringify({ error: "An unexpected error occurred. Please try again later." }), { status: 500 });
  }
}
