# Fråga 1177

A project made by Fyris AI.

## Getting Started

To get the project up and running, follow these steps:

1. Install dependencies:

   ```bash
   npm install
   ```

2. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

3. Create prerequisite resources in Azure AI:
- Azure AI Search index
  - Optionally create a semantic search configuration and include vector fields in the index

_Note: create a vector search index via [REST API](https://learn.microsoft.com/azure/search/search-get-started-vector) or within [Azure Portal](https://learn.microsoft.com/en-us/azure/search/search-get-started-portal-import-vectors?tabs=sample-data-storage%2Cmodel-aoai%2Cconnect-data-storage))_
- Azure OpenAI Chat model
- Azure OpenAI Embedding model, if using vector search

_Note: see available Azure OpenAI models [here](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models) and deploy them using this [guide](https://learn.microsoft.com/en-us/azure/ai-services/openai/chatgpt-quickstart)_


4. Add your Azure OpenAI and Azure AI Search variables to the `.env` file:

   ```
   AZURE_SEARCH_ENDPOINT=your_azure_search_endpoint_here
   AZURE_SEARCH_KEY=your_azure_search_key_here
   AZURE_SEARCH_INDEX_NAME=your_azure_search_index_name_here
   AZURE_SEARCH_CONTENT_FIELD=your_azure_search_content_field_here
   AZURE_SEARCH_VECTOR_FIELD=your_azure_search_vector_field_here # include if using vector search
   AZURE_SEARCH_SEMANTIC_CONFIGURATION_NAME=your_azure_search_semantic_configuration_name_here # include if using semantic search

   AZURE_OPENAI_API_ENDPOINT=your_azure_openai_api_endpoint_here
   AZURE_RESOURCE_NAME=your_azure_resource_name_here
   AZURE_DEPLOYMENT_NAME=your_azure_deployment_name_here # chat model deployment name
   AZURE_EMBEDDING_DEPLOYMENT_NAME=your_azure_embedding_deployment_name_here # embedding model deployment name
   AZURE_API_KEY=your_azure_api_key_here
   ```

5. Start the development server:
   ```bash
   npm run dev
   ```

Your project should now be running on [http://localhost:3000](http://localhost:3000).
