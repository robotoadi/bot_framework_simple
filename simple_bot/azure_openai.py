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
import tldextract
from urllib.parse import urljoin, urlparse


load_dotenv()


# logging.basicConfig(level=logging.INFO)
# openai_logger = logging.getLogger("openai")
# openai_logger.setLevel(logging.DEBUG)


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

MAX_LINKS_TO_FOLLOW = 10  # You can increase this for deeper scraping

def get_embedding(text: str) -> list:
    if not isinstance(text, str):
        raise ValueError("Expected string for embedding")
    text = text.strip()[:8191]
    response = openai_embeddings_client.embeddings.create(
        model=os.getenv("AZURE_EMBEDDING_DEPLOYMENT"),
        input=[text]
    )
    return response.data[0].embedding

def cosine_similarity(a, b):
    return dot(a, b) / (norm(a) * norm(b))

def extract_visible_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "header", "footer", "nav", "aside"]):
        tag.extract()
    visible_texts = soup.stripped_strings
    return " ".join(visible_texts)

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

def get_internal_links(base_url, html):
    soup = BeautifulSoup(html, "html.parser")
    domain = tldextract.extract(base_url).registered_domain
    links = set()

    for a in soup.find_all("a", href=True):
        href = a['href'].strip()
        full_url = urljoin(base_url, href)
        if domain in tldextract.extract(full_url).registered_domain:
            links.add(full_url)

    return list(links)

def scrape_website(url: str, query: str) -> str:
    visited = set()
    collected_chunks = []

    def crawl_page(u):
        try:
            print(f"🔗 Visiting: {u}")
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(u, headers=headers, timeout=10)
            r.raise_for_status()
            text = extract_visible_text(r.text)
            chunks = chunk_text(text)
            return chunks, r.text
        except Exception as e:
            print(f"⚠️ Error fetching {u}: {e}")
            return [], ""

    # 1. Scrape root page
    root_chunks, root_html = crawl_page(url)
    collected_chunks.extend(root_chunks)

    # 2. Get internal links from root page
    internal_links = get_internal_links(url, root_html)

    # 3. Score links based on anchor text vs. query
    link_scores = []
    query_vector = get_embedding(query)
    for link in internal_links:
        try:
            # Use last part of URL or anchor as approximation
            text = urlparse(link).path.split("/")[-1].replace("-", " ")
            if not text:
                continue
            sim = cosine_similarity(query_vector, get_embedding(text))
            link_scores.append((sim, link))
        except Exception:
            continue

    # 4. Sort and visit top-N links
    top_links = sorted(link_scores, reverse=True)[:MAX_LINKS_TO_FOLLOW]
    for _, link in top_links:
        if link not in visited:
            visited.add(link)
            chunks, _ = crawl_page(link)
            collected_chunks.extend(chunks)

    # 5. Embed all chunks and score them
    scored_chunks = []
    for chunk in collected_chunks:
        try:
            sim = cosine_similarity(query_vector, get_embedding(chunk))
            scored_chunks.append((sim, chunk))
        except Exception:
            continue

    if not scored_chunks:
        return "❌ No relevant content found after crawling."

    # 6. Return top result
    top_score, top_chunk = max(scored_chunks, key=lambda x: x[0])
    return f"📌 Best match from crawled pages (score {top_score:.2f}):\n\n{top_chunk}"
    
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
