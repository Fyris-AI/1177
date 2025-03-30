from typing import List, Dict, Any, AsyncGenerator, Optional
import json
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import StructuredTool
from langchain.agents import create_openai_tools_agent
from langchain.agents import AgentExecutor

from app.utils.config import (
    OPENAI_API_KEY,
    OPENAI_MODEL
)
from app.services.vector_store import vector_store_service

class AIService:
    def __init__(self):
        self.llm = ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=0,
            streaming=True
        )
        
        # Define tools similar to the TypeScript implementation
        self.tools = [
            StructuredTool.from_function(
                func=self._get_information,
                name="getInformation",
                description="Get information from your knowledge base to answer the user's question.",
                args_schema={
                    "question": str,
                    "similarQuestions": List[str]
                },
                return_direct=True
            )
        ]
        
        # Create system message
        self.system_message = """You are a helpful assistant acting as the users' second brain.
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
        """
        
        # Create the agent prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create agent
        self.agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=4  # Equivalent to maxToolRoundtrips in TS
        )
    
    async def _get_information(self, question: str, similarQuestions: List[str]) -> List[Dict[str, Any]]:
        """
        Tool implementation to get information from knowledge base.
        Similar to the getInformation tool in the TypeScript implementation.
        """
        results = []
        for query in similarQuestions:
            docs = await vector_store_service.find_relevant_content(query)
            results.extend(docs)
            
        # Remove duplicates (just like in the TS implementation)
        unique_results = {}
        for doc in results:
            if doc["text"] not in unique_results:
                unique_results[doc["text"]] = doc
                
        return list(unique_results.values())
    
    async def generate_response(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response to the user's messages.
        
        Args:
            messages: List of message objects with role and content
            
        Yields:
            Chunks of the generated response for streaming
        """
        # Convert messages to LangChain format
        langchain_messages = []
        for msg in messages:
            if msg["role"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                langchain_messages.append(AIMessage(content=msg["content"]))
                
        # Create a streaming response
        response_stream = await self.agent_executor.astream_log(
            {"input": langchain_messages[-1].content if langchain_messages else "", 
             "chat_history": langchain_messages[:-1] if len(langchain_messages) > 1 else []}
        )
        
        # Stream the response chunks
        async for chunk in response_stream:
            if "actions" in chunk:
                # This is a tool call
                yield json.dumps({"type": "tool_call", "tool": chunk["actions"][0].tool})
            elif "steps" in chunk and chunk["steps"][-1].action_log and "output" in chunk["steps"][-1].action_log:
                # This is a tool response
                continue  # We don't need to stream this
            elif "output" in chunk:
                # This is the final answer
                yield chunk["output"]

# Create a singleton instance
ai_service = AIService()
