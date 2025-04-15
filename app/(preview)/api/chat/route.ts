import { StreamingTextResponse, Message as VercelChatMessage } from 'ai';

export const maxDuration = 30;

// Define the expected structure for messages (especially the last user message)
interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

// Define the expected response structure from the Python backend
interface PineconeResponse {
  answer: string;
  sources: string[]; // Assuming sources are returned as an array of strings
  context: string[]; // Add context field
}

export async function POST(req: Request) {
  try {
    const { messages }: { messages: ChatMessage[] } = await req.json();

    console.log("--- New Chat Request (Pinecone Backend) ---");
    console.log(`Number of messages received: ${messages.length}`);

    // Extract the last user message
    const userQuery = messages.findLast((msg) => msg.role === 'user')?.content;

    if (!userQuery) {
      return new Response(JSON.stringify({ error: "No user query found" }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    console.log(`User Query: ${userQuery}`);

    // Define the backend URL (Ideally use an environment variable)
    const backendUrl = process.env.PYTHON_BACKEND_URL || 'http://localhost:8000/query';
    console.log(`Fetching from backend: ${backendUrl}`);

    // Make the request to the Python/Pinecone backend
    const pineconeResponse = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query: userQuery }),
    });

    if (!pineconeResponse.ok) {
      const errorBody = await pineconeResponse.text();
      console.error(`Backend Error: ${pineconeResponse.status} ${pineconeResponse.statusText}`, errorBody);
      throw new Error(`Failed to fetch from backend: ${pineconeResponse.statusText}`);
    }

    const result: PineconeResponse = await pineconeResponse.json();
    console.log("Backend Response:", result);

    // Return the result directly as JSON
    return new Response(JSON.stringify(result), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });

  } catch (error: unknown) {
    console.error("API Route Error Details:", error);
    const errorMessage = error instanceof Error ? error.message : "An unexpected error occurred";
    // Return a JSON error response
    return new Response(JSON.stringify({ error: errorMessage }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}
