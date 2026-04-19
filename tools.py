from langchain.tools import tool
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os
from dotenv import load_dotenv
from rich import print
load_dotenv()

Tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

@tool
def web_search(query: str) -> str:
    """search the web for recent and reliable information on a topic. Reterns titles, URLs and snippets."""
    results = Tavily.search(query= query, max_results=5)
    # print("\n----- Web Search Results -----\n")
    # print(results)
    out = []
    # print("\n----- Formatted Web Search Results -----\n")
    for result in results['results']:
        out.append(f'Title: {result['title']}\nURL: {result['url']}\nSnippet: {result['content'][:300]}')
        
    return "\n----\n".join(out)

# print(web_search.invoke("what are the recent update of war?"))

@tool
def scrap_url(url: str) -> str:
    """Scrape and return clean text content from a given URL for deeper reading."""
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, 'html.parser')
        for tag in soup(['script', 'style', 'footer', 'nav']):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)[:3000]  # ← soup, not tag
    except Exception as e:
        return f"Error scraping URL: {e}"
    
# print(scrap_url.invoke("https://www.cbsnews.com/us-iran-tensions/"))