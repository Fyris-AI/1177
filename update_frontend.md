# Frontend Update Guide

This guide explains how to update the frontend to work with the new Python FastAPI backend. The main changes involve updating the API client to point to the new endpoint.

## Steps to Update the Frontend

### 1. Update API Client

Find where your frontend makes API calls to the current Next.js API routes and update them to point to the new FastAPI backend.

For example, if you're using the Vercel AI SDK, update your chat implementation:

```typescript
// Before (using Vercel AI SDK with Next.js API routes)
import { useChat } from 'ai/react';

function ChatComponent() {
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat();
  
  // Rest of your component
}

// After (pointing to the FastAPI backend)
import { createChat } from 'ai/react';

function ChatComponent() {
  const { messages, input, handleInputChange, handleSubmit, isLoading } = createChat({
    api: 'http://localhost:8000/api/chat', // Update with your FastAPI URL
    headers: {
      'Content-Type': 'application/json',
    },
  });
  
  // Rest of your component
}
```

### 2. Update Environment Variables

If your frontend shares environment variables with the backend, make sure to update them to reflect the new OpenAI configuration instead of Azure.

Update your `.env` file or environment configuration:

```
# Before
AZURE_DEPLOYMENT_NAME=your-azure-deployment
AZURE_EMBEDDING_DEPLOYMENT_NAME=your-azure-embedding-deployment
AZURE_SEARCH_ENDPOINT=your-azure-search-endpoint
AZURE_SEARCH_INDEX_NAME=your-azure-search-index-name
AZURE_SEARCH_KEY=your-azure-search-key
AZURE_SEARCH_CONTENT_FIELD=content

# After
OPENAI_API_KEY=your-openai-api-key
FASTAPI_BACKEND_URL=http://localhost:8000  # Or your FastAPI production URL
```

### 3. CORS Configuration

If your frontend is hosted on a different domain than the backend, make sure to update the CORS configuration in the backend to allow requests from your frontend domain.

In the FastAPI backend `app/main.py` file:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Update with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. Testing the Integration

1. Start the FastAPI backend:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. Start your frontend application (e.g., Next.js dev server):
   ```bash
   npm run dev
   ```

3. Test the chat functionality to ensure it's communicating with the new backend.

## Troubleshooting

If you encounter issues with the integration:

1. Check the browser console for any network errors
2. Verify the API endpoint URL is correct
3. Ensure CORS is properly configured to allow requests from your frontend
4. Check that the API request format matches what the new backend expects
5. Verify that your OpenAI API key is valid and properly configured

For streaming responses, make sure your frontend properly handles Server-Sent Events (SSE) from the FastAPI backend. 