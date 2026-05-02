import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("full_content.fetcher")

def fetch_full_content(url: str, timeout: int = 15) -> str:
    """
    Downloads and extracts the main text content from a URL using BeautifulSoup.
    Returns empty string if extraction fails.
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove non-content elements
        for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
            element.extract()
            
        # Extract text and clean up whitespace
        text = soup.get_text(separator='\n')
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        cleaned_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        if cleaned_text:
            return cleaned_text
        else:
            logger.warning(f"No text extracted from: {url}")
            return ""
    except Exception as e:
        logger.error(f"Error extracting content from {url}: {e}")
        return ""
