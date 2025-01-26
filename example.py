# -*- coding: utf-8 -*-

from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

os.environ["GOOGLE_API_KEY"] = "AIzaSyD8LKVDXO5zAFYbINcKHII-fiDa6rDexR4"

async def main():
    agent = Agent(
        llm=ChatGoogleGenerativeAI(model="gemini-1.5-flash"),
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
