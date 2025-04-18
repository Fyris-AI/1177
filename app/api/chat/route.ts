// app/api/chat/route.ts
// Remove Vercel AI SDK imports if not needed
// import { StreamingTextResponse, streamText, LangChainStream } from 'ai'; 

export const maxDuration = 60; // Keep or adjust timeout

export async function POST(req: Request) {
  try {
    // Extract the user query from the request body
    const { messages } = await req.json();
    // Get the last message from the user
    const userQuery = messages[messages.length - 1]?.content;

    if (!userQuery) {
      return new Response(JSON.stringify({ error: 'No query provided in messages' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    console.log('Frontend API route received query:', userQuery);

    // --- Call the FastAPI Backend ---
    const backendUrl = process.env.PYTHON_BACKEND_URL || 'http://127.0.0.1:8000'; 
    console.log(`Calling backend: ${backendUrl}/api/chat`);

    const backendResponse = await fetch(`${backendUrl}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query: userQuery }),
    });

    console.log('Backend status:', backendResponse.status);

    if (!backendResponse.ok) {
      const errorBody = await backendResponse.text();
      console.error('Backend Error:', errorBody);
      let detail = errorBody;
      try {
        const errorJson = JSON.parse(errorBody);
        detail = errorJson.detail || errorBody;
      } catch(e) { /* ignore parsing error */ }

      return new Response(JSON.stringify({ 
        error: `Backend request failed: ${detail}` 
      }), {
        status: backendResponse.status, 
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // Get the JSON response from the backend
    const responseData = await backendResponse.json();
    console.log('Backend response data:', responseData);

    // --- Return the JSON response directly ---
    return new Response(JSON.stringify(responseData), {
        headers: { 'Content-Type': 'application/json' },
        status: 200 
    });

  } catch (error: unknown) {
    console.error("Frontend API Route Error:", error);
    const errorMessage = error instanceof Error ? error.message : "An unexpected error occurred processing the chat request.";
    // Return a standard error response in JSON format
     return new Response(
       JSON.stringify({ error: "Failed to process chat request" }), 
       { status: 500, headers: { 'Content-Type': 'application/json' } }
     );
  }
} 