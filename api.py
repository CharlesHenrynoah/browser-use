from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
from dotenv import load_dotenv
from assistant import VirtualAssistant

load_dotenv()

app = FastAPI()

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèles de données
class SearchRequest(BaseModel):
    query: str
    user_id: str

class SearchResponse(BaseModel):
    status: str
    data: Dict[str, Any]
    sources: List[str]
    timestamp: str
    browser_state: Optional[Dict[str, Any]] = None

# Initialisation de l'assistant
assistant = VirtualAssistant(os.getenv("GOOGLE_API_KEY"))

@app.post("/search")
async def search(request: SearchRequest) -> SearchResponse:
    try:
        result = await assistant.search(request.query)
        
        return SearchResponse(
            status="success",
            data=result.data,
            sources=result.sources,
            timestamp=result.timestamp,
            browser_state=result.browser_state
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
