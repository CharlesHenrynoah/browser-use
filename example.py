# -*- coding: utf-8 -*-

from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent, VirtualBrowser
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

os.environ["GOOGLE_API_KEY"] = "AIzaSyD8LKVDXO5zAFYbINcKHII-fiDa6rDexR4"

from dataclasses import dataclass
from typing import Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BrowserResponse:
    status_code: int
    text: str
    url: str
    headers: Dict[str, str]

class VirtualBrowser:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.current_url: Optional[str] = None
        self.history: list[str] = []
        
    async def navigate(self, url: str) -> BrowserResponse:
        """Simule la navigation vers une URL"""
        try:
            logger.info(f"Navigating to {url}")
            response = self.session.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            self.current_url = url
            self.history.append(url)
            
            return BrowserResponse(
                status_code=response.status_code,
                text=response.text,
                url=url,
                headers=dict(response.headers)
            )
        except requests.RequestException as e:
            logger.error(f"Error navigating to {url}: {str(e)}")
            return BrowserResponse(
                status_code=500,
                text=f"Error: {str(e)}",
                url=url,
                headers={}
            )
    
    def extract_content(self, response: BrowserResponse) -> str:
        """Extrait le contenu pertinent de la page"""
        try:
            if response.status_code != 200:
                return f"Error: Status code {response.status_code}"
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Garde les styles CSS
            styles = soup.find_all('style')
            css = '\n'.join([style.string for style in styles if style.string])
            
            # Garde les liens CSS externes
            css_links = []
            for link in soup.find_all('link', rel='stylesheet'):
                href = link.get('href')
                if href:
                    if href.startswith('//'):
                        href = 'https:' + href
                    elif not href.startswith('http'):
                        base_url = '/'.join(response.url.split('/')[:3])
                        href = base_url + ('' if href.startswith('/') else '/') + href
                    css_links.append(f'<link rel="stylesheet" href="{href}">')
            
            # Nettoie le contenu mais garde la structure
            for script in soup(['script', 'iframe', 'noscript']):
                script.decompose()
            
            # Reconstruit le HTML avec les styles
            html = f"""
            <html>
            <head>
                <meta charset="UTF-8">
                <base href="{response.url}">
                {''.join(css_links)}
                <style>{css}</style>
            </head>
            <body>
                {str(soup.body) if soup.body else str(soup)}
            </body>
            </html>
            """
            
            return html
            
        except Exception as e:
            logger.error(f"Error extracting content: {str(e)}")
            return f"Error extracting content: {str(e)}"

async def main():
    browser = VirtualBrowser()
    agent = Agent(
        llm=ChatGoogleGenerativeAI(model="gemini-1.5-flash"),
        browser=browser,
        task="""
        1. Consulter les scores NBA du 26 janvier 2025:
           - Vérifier sur NBA.com et ESPN
           - Se concentrer sur le match Lakers vs Warriors s'il est listé
           - Noter l'heure prévue du match si disponible
           
        2. Analyser les informations disponibles:
           - Compositions d'équipes
           - Statistiques des joueurs clés
           - Cotes et prédictions
        """
    )
    
    print("\nRecherche des informations sur le match Lakers vs Warriors...")
    result = await agent.run()
    print("\nRésultats de la recherche :")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
