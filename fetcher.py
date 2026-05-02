import os
import logging
import requests

logger = logging.getLogger("full_content.fetcher")

def fetch_full_content(url: str, timeout: int = 30) -> str:
    """
    Downloads and extracts the main text content from a URL using Jina Reader API.
    This bypasses Datacenter IP blocks (403 Forbidden) that plague cloud VMs
    by delegating the scraping and Javascript execution to Jina's proxy network.
    Returns clean Markdown text.
    """
    try:
        jina_url = f"https://r.jina.ai/{url}"
        headers = {
            "Accept": "text/plain"  # Request clean text/markdown
        }
        
        # Optional: Use API key if provided in .env to increase rate limits
        jina_api_key = os.getenv("JINA_API_KEY")
        if jina_api_key:
            headers["Authorization"] = f"Bearer {jina_api_key}"
            
        response = requests.get(jina_url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        text = response.text.strip()
        if text:
            return text
        else:
            logger.warning(f"No text extracted from: {url}")
            return ""
    except Exception as e:
        logger.error(f"Error extracting content from {url}: {e}")
        return ""
