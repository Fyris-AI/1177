// app/api/chat/route.ts

export const maxDuration = 60; // Keep or adjust timeout

interface ConversationMessage {
  role: string;
  content: string;
}

export async function POST(req: Request) {
  try {
    // Extract the user query, audience, journal data, and conversation tracking from the request body
    const { 
      messages, 
      audience, 
      journalData, 
      clarificationRound = 0, 
      conversationHistory = [],
      isFollowUp = false,
      lastRelevantDocs = []
    } = await req.json();
    // Get the last message from the user
    const userQuery = messages[messages.length - 1]?.content;

    if (!userQuery) {
      return new Response(JSON.stringify({ error: 'No query provided in messages' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // Validate audience
    if (!audience || (audience !== 'invanare' && audience !== 'personal')) {
      return new Response(JSON.stringify({ error: 'Invalid or missing audience' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    const hasJournalData = journalData !== null && journalData !== undefined;
    console.log('Frontend API route received query:', userQuery, 'Audience:', audience, 'Has Journal Data:', hasJournalData, 'Clarification Round:', clarificationRound, 'Is Follow-up:', isFollowUp);

    // --- Call the FastAPI Backend ---
    const backendUrl = process.env.PYTHON_BACKEND_URL || 'http://127.0.0.1:8000';
    
    // Use the personalized endpoint if journal data is provided
    const endpoint = hasJournalData ? '/api/chat-with-journal' : '/api/chat';
    console.log(`Calling backend: ${backendUrl}${endpoint}`);

    // Build request body with conversation tracking and follow-up info
    const requestBody = hasJournalData 
      ? { 
          query: userQuery, 
          audience: audience, 
          journal_data: journalData,
          clarification_round: clarificationRound,
          conversation_history: conversationHistory.map((msg: ConversationMessage) => ({
            role: msg.role,
            content: msg.content
          })),
          is_follow_up: isFollowUp,
          last_relevant_docs: lastRelevantDocs
        }
      : { query: userQuery, audience: audience };

    const backendResponse = await fetch(`${backendUrl}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
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
    // Return a standard error response in JSON format
     return new Response(
       JSON.stringify({ error: "Failed to process chat request" }), 
       { status: 500, headers: { 'Content-Type': 'application/json' } }
     );
  }
}