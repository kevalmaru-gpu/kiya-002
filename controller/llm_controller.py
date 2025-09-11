from core.llm.gemini_llm import GeminiLLM
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

llm = GeminiLLM(instruction="You are a helpful assistant that can answer questions and help with tasks.", model="gemini-1.5-flash", enable_web_search=True)

async def test_llm():
    logger.info("Sending request to LLM")
    response = await llm.query("You are a helpful assistant that can answer questions and help with tasks.", "What is the capital of France?")
    return response

async def test_web_search():
    """Test the web search functionality with a current events question"""
    logger.info("Testing web search functionality")
    response = await llm.query("You are a helpful assistant that can answer questions and help with tasks.", "What are the latest developments in AI technology this week?")
    return response
