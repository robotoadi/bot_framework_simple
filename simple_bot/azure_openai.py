# azure_agent_v1.py

import json
import logging

import openai
import os
import re
import requests
import traceback

from openai import AzureOpenAI  # This is the new v1-style client
from bs4 import BeautifulSoup, Comment
from dotenv import load_dotenv
from numpy import dot
from numpy.linalg import norm


load_dotenv()


logging.basicConfig(level=logging.INFO)
openai_logger = logging.getLogger("openai")
openai_logger.setLevel(logging.DEBUG)


# Configure the Azure OpenAI client
openai_chat_client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_deployment=os.getenv("OPENAI_CHAT_DEPLOYMENT_NAME"),
    api_key=os.getenv("OPENAI_CHAT_API_KEY"),
    azure_endpoint=os.getenv("OPENAI_CHAT_ENDPOINT")
)

openai_embeddings_client = AzureOpenAI(
    api_version="2023-05-15",
    azure_deployment=os.getenv("OPENAI_EMBEDDINGS_DEPLOYMENT_NAME"),
    api_key=os.getenv("OPENAI_EMBEDDINGS_API_KEY"),
    azure_endpoint=os.getenv("OPENAI_EMBEDDINGS_ENDPOINT")
)


# Define function tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather info for a city",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name"
                    }
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scrape_website",
            "description": "Scrapes a website and returns relevant content",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The full URL of the website to scrape"
                    },
                    "query": {
                        "type": "string",
                        "description": "What the user is looking for in the website content"
                    }
                },
                "required": ["url", "query"]
            }
        }
    }
]

# Define the actual Python function
def get_weather(location):
    return f"The weather in {location} is sunny with a high of 25°C."

def get_embedding(text: str) -> list:
    if not isinstance(text, str):
        print("[x] Input must be a string")
        raise ValueError("Embedding input must be a string")
    
    if len(text) > 10000:
        print("[!] Input text too long, truncating to 10000 characters")
        text = text[:10000]

    print(f"[*] Getting embedding for text: '{text[:50]}...' (length={len(text)}, type={type(text)})")
    response = openai_embeddings_client.embeddings.create(
        model=os.getenv("OPENAI_EMBEDDINGS_DEPLOYMENT_NAME"),
        input=[text]
    )
    return response.data[0].embedding

def cosine_similarity(vec1, vec2):
    return dot(vec1, vec2) / (norm(vec1) * norm(vec2))

def extract_visible_text(html):
    soup = BeautifulSoup(html, "html.parser")

    # Remove scripts/styles/comments
    for tag in soup(["script", "style", "header", "footer", "nav", "aside"]):
        tag.extract()
    for element in soup(text=lambda text: isinstance(text, Comment)):
        element.extract()

    # Get all visible text chunks
    visible_texts = soup.stripped_strings
    full_text = " ".join(visible_texts)

    return full_text

def chunk_text(text, max_chars=800):
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks = []
    chunk = ""
    for sentence in sentences:
        if len(chunk) + len(sentence) < max_chars:
            chunk += sentence + " "
        else:
            chunks.append(chunk.strip())
            chunk = sentence + " "
    if chunk:
        chunks.append(chunk.strip())
    return chunks

def scrape_website(url: str, query: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Extract and chunk all visible text
        full_text = extract_visible_text(response.text)
        text_chunks = chunk_text(full_text)

        if not text_chunks:
            return "❌ No usable text found on the page."

        # Embed query once
        query_vector = get_embedding(query)

        # Score all chunks
        scored_chunks = []
        for chunk in text_chunks:
            chunk_vector = get_embedding(chunk)
            score = cosine_similarity(query_vector, chunk_vector)
            scored_chunks.append((score, chunk))

        # Get top match
        best_score, best_chunk = max(scored_chunks, key=lambda x: x[0])

        return f"🔍 Best match (score {best_score:.2f}):\n\n{best_chunk}"

    except Exception as e:
        print(f"[x] Error scraping website: {traceback.format_exc()}")
        return f"❌ Error: {str(e)}"
    
# Core LLM agent logic using function-calling
async def call_azure_openai_agent(user_input: str) -> str:
    response = openai_chat_client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),  # e.g., "gpt-4-agent"
        messages=[{"role": "user", "content": user_input}],
        tools=tools,
        tool_choice="auto"
    )

    message = response.choices[0].message

    # If tool call detected
    if message.tool_calls:
        print("Tool call detected:", message.tool_calls)
        tool_call = message.tool_calls[0]
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        if name == "get_weather":
            result = get_weather(**args)
            return f"Function `{name}` was called:\n{result}"

        if name == "scrape_website":
            result = scrape_website(**args)
            return f"Function `{name}` was called:\n{result}"
        
    # Otherwise return plain LLM message
    return message.content
