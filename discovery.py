import time
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List

app = FastAPI()
registry: Dict[str, Dict] = {}

class AgentCard(BaseModel):
    id: str
    name: str
    description: str
    base_url: str
    capabilities: List[str]

@app.post("/register")
async def register(card: AgentCard):
    registry[card.id] = card.dict()
    registry[card.id]["last_seen"] = time.time()
    return {"status": "ok", "registered": card.id}

@app.get("/agents")
async def agents():
    now = time.time()
    return [a for a in registry.values() if now - a.get("last_seen", 0) < 3600]

@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    agent = registry.get(agent_id)
    if not agent:
        return {"error": f"Agent {agent_id} not found"}
    return agent

@app.get("/health")
async def health():
    return {"status": "ok", "agents_count": len(registry)}
