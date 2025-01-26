from typing import Dict, Any, List
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from dataclasses import dataclass
from datetime import datetime
from example import VirtualBrowser
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    data: Dict[str, Any]
    timestamp: str
    query: str
    sources: List[str]
    browser_state: Dict[str, Any]

class VirtualAssistant:
    def __init__(self, api_key: str):
        self.browser = VirtualBrowser()
        self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)
        
    def determine_sources(self, query: str) -> List[str]:
        """Détermine les sources pertinentes en fonction de la requête"""
        prompt = f"""
        Pour cette requête : "{query}"
        Détermine les 3 meilleures URLs à consulter pour obtenir l'information.
        Retourne uniquement les URLs, une par ligne.
        Les URLs doivent être complètes et valides.
        """
        
        try:
            response = self.llm.invoke(prompt)
            urls = [url.strip() for url in response.content.splitlines() if url.strip().startswith('http')]
            return urls[:3]  # Limite à 3 URLs
        except Exception as e:
            logger.error(f"Error determining sources: {str(e)}")
            return []
    
    def capture_browser_state(self, url: str, content: str, html_content: str) -> Dict[str, Any]:
        """Capture l'état du navigateur pour la visualisation"""
        try:
            # Extrait le titre de la page
            soup = BeautifulSoup(html_content, 'html.parser')
            title = soup.title.string if soup.title else None
            
            # Si pas de titre, utilise le domaine
            if not title:
                domain = urlparse(url).netloc
                path = urlparse(url).path
                title = domain + (path if path != '/' else '')
            
            return {
                "url": url,
                "title": title,
                "content": content,
                "html": html_content,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error capturing browser state: {str(e)}")
            return {
                "url": url,
                "title": "Erreur",
                "content": f"Erreur : {str(e)}",
                "html": "",
                "timestamp": datetime.now().isoformat(),
                "status": "error"
            }
        
    def format_response(self, data: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """Formate la réponse en langage naturel"""
        prompt = f"""
        En utilisant ces informations : {json.dumps(data)}
        Formule une réponse naturelle et concise à la question : "{query}"
        
        Règles :
        1. Réponds en UNE SEULE phrase claire et directe
        2. Concentre-toi sur les informations les plus pertinentes
        3. Utilise un ton conversationnel
        4. Si l'information est incomplète, dis-le simplement
        """
        
        response = self.llm.invoke(prompt)
        return {
            "answer": response.content,
            "raw_data": data
        }
            
    async def search(self, query: str) -> SearchResult:
        """Effectue une recherche et retourne une réponse en langage naturel"""
        try:
            # Détermine dynamiquement les sources
            sources = self.determine_sources(query)
            if not sources:
                sources = [
                    "https://www.google.com/search?q=" + query.replace(" ", "+")
                ]
            
            results = []
            browser_states = []
            
            for url in sources:
                try:
                    # Navigation et extraction
                    response = await self.browser.navigate(url)
                    html_content = response.text
                    content = self.browser.extract_content(response)
                    
                    # Capture de l'état avec le HTML
                    browser_states.append(
                        self.capture_browser_state(url, content, html_content)
                    )
                    
                    # Analyse du contenu
                    analysis_prompt = f"""
                    Analyse ce contenu de {url} : {content}
                    Par rapport à la question : "{query}"
                    Extrais les informations pertinentes et retourne une courte phrase.
                    """
                    
                    analysis = self.llm.invoke(analysis_prompt)
                    results.append({
                        "source": url,
                        "content": analysis.content
                    })
                except Exception as e:
                    logger.error(f"Error processing {url}: {str(e)}")
                    browser_states.append({
                        "url": url,
                        "title": "Erreur",
                        "content": f"Erreur lors du chargement : {str(e)}",
                        "html": "",
                        "timestamp": datetime.now().isoformat(),
                        "status": "error"
                    })
                    continue
            
            if not results:
                response_data = {
                    "answer": "Désolé, je n'ai pas pu accéder aux sources pour le moment. Essayez de reformuler votre question ou réessayez plus tard.",
                    "raw_data": []
                }
            else:
                response_data = self.format_response(results, query)
            
            return SearchResult(
                data=response_data,
                timestamp=datetime.now().isoformat(),
                query=query,
                sources=sources,
                browser_state={"states": browser_states}
            )
            
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            return SearchResult(
                data={
                    "answer": f"Désolé, une erreur s'est produite lors de la recherche : {str(e)}",
                    "raw_data": []
                },
                timestamp=datetime.now().isoformat(),
                query=query,
                sources=[],
                browser_state={"states": []}
            )
