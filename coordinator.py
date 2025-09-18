import asyncio
import logging
import httpx
from fastapi import FastAPI
from pydantic import BaseModel

logger = logging.getLogger("coordinator")
logging.basicConfig(level=logging.INFO)

app = FastAPI()
DISCOVERY_URL = "http://localhost:9000"
MAX_RETRIES = 3
RETRY_DELAY = 1

class ChatQuery(BaseModel):
    query: str

async def fetch_agents():
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(f"{DISCOVERY_URL}/agents")
                r.raise_for_status()
                return list(r.json())
        except:
            await asyncio.sleep(RETRY_DELAY)
    return []

async def delegate_to_agents(query: str):
    agents = await fetch_agents()
    if not agents:
        return {"agent_responses": [], "error": "Coordinator not available after multiple attempts."}
    results = []
    for agent in agents:
        try:
            agent_url = f"{agent['base_url']}/a2a/message"
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(agent_url, json={"from": "coordinator", "payload": {"query": query}})
                r.raise_for_status()
                resp_json = r.json()
                if "answer" not in resp_json:
                    resp_json["answer"] = resp_json.get("text", "No data")
                results.append(resp_json)
        except:
            continue
    return {"agent_responses": results}

@app.post("/chat")
async def chat(query: ChatQuery):
    return await delegate_to_agents(query.query)

@app.post("/ask")
async def ask(query: ChatQuery):
    return await delegate_to_agents(query.query)

@app.get("/health")
async def health():
    agents = await fetch_agents()
    return {"status": "ok", "agents_count": len(agents)}  