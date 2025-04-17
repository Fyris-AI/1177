export const maxDuration = 30;

export async function POST(req: Request) {
  try {
    // Create the response data
    const responseData = {
      message: "Lungcancer innebär att det har bildats en cancertumör i en av lungorna. Sjukdomen kan sprida sig till andra delar av kroppen och bilda dottertumörer, som också kallas metastaser. Operation, strålbehandling och behandling med olika läkemedel är vanligt vid lungcancer. Läkemedlen delas in efter hur de verkar och det finns flera olika läkemedel inom varje grupp. Vill du veta mer om symptomen eller vilka läkemedel som används?",
      source_links: [
        "https://www.1177.se/Uppsala-lan/sjukdomar--besvar/cancer/cancerformer/lungcancer/#section-16917", 
        "https://www.1177.se/Uppsala-lan/sjukdomar--besvar/cancer/cancerformer/lungcancer/#section-16920"
      ],
      source_names: [
        "Lungcancer behandling", 
        "Vad är lungcancer?"
      ]
    };

    // Create a stream that the Vercel AI SDK expects
    const stream = new ReadableStream({
      async start(controller) {
        const encoder = new TextEncoder();
        
        // First send the text part (required)
        const textContent = JSON.stringify(responseData);
        controller.enqueue(encoder.encode(`0:"${textContent.replace(/"/g, '\\"')}"\n`));
        
        // Then send the data message (must be an array)
        controller.enqueue(encoder.encode(`2:[{"status":"complete"}]\n`));
        
        controller.close();
      },
    });

    return new Response(stream, {
      headers: { 'Content-Type': 'text/plain; charset=utf-8' },
    });
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