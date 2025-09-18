from fastapi import FastAPI, Request
import httpx, weaviate, os, asyncio, time
from weaviate.auth import AuthApiKey
from dotenv import load_dotenv
from inspector import Inspector

load_dotenv()

WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
DISCOVERY_URL = os.getenv("DISCOVERY_URL", "http://localhost:9000")
AGENT_ID = os.getenv("HEALTH_AGENT_ID", "health-agent-1")
CERTAINTY = float(os.getenv("WEAVIATE_CERTAINTY", "0.3"))
HEARTBEAT_INTERVAL = int(os.getenv("AGENT_HEARTBEAT_SECONDS", "30"))
CLASS_NAME = "HealthNote"
BASE_URL = os.getenv("HEALTH_BASE_URL", "http://localhost:8001")

app = FastAPI()
insp = Inspector()

AGENT_CARD = {
    "id": AGENT_ID,
    "name": "Health Agent",
    "description": "Answers health-related queries using semantic search.",
    "base_url": BASE_URL,
    "capabilities": ["health.triage", "health.advice"]
}

client = weaviate.Client(
    url=WEAVIATE_URL,
    auth_client_secret=AuthApiKey(api_key=WEAVIATE_API_KEY),
    timeout_config=(10, 60)
)

def wait_for_weaviate(client, timeout=120):
    start_time = time.time()
    while True:
        try:
            if client.is_ready():
                print(f"✅ {AGENT_ID} connected to Weaviate")
                return True
        except:
            pass
        if time.time() - start_time > timeout:
            raise Exception(f"❌ {AGENT_ID} Weaviate not ready after {timeout}s")
        time.sleep(5)

wait_for_weaviate(client)

def ensure_schema():
    cls = {
        "class": CLASS_NAME,
        "description": "Health domain notes",
        "properties": [{"name": "text", "dataType": ["text"]}]
    }
    existing = client.schema.get()
    if not any(c["class"] == CLASS_NAME for c in existing.get("classes", [])):
        client.schema.create_class(cls)
        print(f"✅ Created Weaviate class: {CLASS_NAME}")

heartbeat_task = None
stop_event = asyncio.Event()

async def heartbeat_register():
    while not stop_event.is_set():
        try:
            async with httpx.AsyncClient() as s:
                await s.post(f"{DISCOVERY_URL}/register", json=AGENT_CARD, timeout=5)
        except:
            pass
        await asyncio.sleep(HEARTBEAT_INTERVAL)

@app.on_event("startup")
async def startup_event():
    ensure_schema()
    global heartbeat_task
    heartbeat_task = asyncio.create_task(heartbeat_register())

@app.on_event("shutdown")
async def shutdown_event():
    stop_event.set()
    if heartbeat_task:
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass

@app.get("/agent-card")
def agent_card():
    return AGENT_CARD

@app.get("/status")
def status():
    return {"status": "ok", "agent_id": AGENT_ID}

async def a2a_delegate(query: str):
    responses = []
    try:
        async with httpx.AsyncClient(timeout=10) as client_http:
            r = await client_http.get(f"{DISCOVERY_URL}/agents")
            r.raise_for_status()
            agents = r.json()
            for agent in agents:
                if agent["id"] == AGENT_ID:
                    continue
                insp.log_a2a(from_agent=AGENT_ID, to_agent=agent["id"], query=query)
                for attempt in range(2):  # reduced retries
                    try:
                        resp = await client_http.post(
                            f"{agent['base_url']}/a2a/message",
                            json={"from": AGENT_ID, "payload": {"query": query}},
                            timeout=5
                        )
                        resp.raise_for_status()
                        responses.append(resp.json())
                        break
                    except:
                        await asyncio.sleep(1)
    except:
        pass
    return responses

@app.post("/a2a/message")
async def receive(req: Request):
    body = await req.json()
    query = body.get("payload", {}).get("query", "").strip()
    answer = f"No data available from {AGENT_ID}."
    source_hits = []
    if query:
        try:
            res = client.query.get(CLASS_NAME, ["text", "_additional { certainty }"]) \
                .with_near_text({"concepts": [query]}) \
                .with_limit(3).do()
            hits = res.get("data", {}).get("Get", {}).get(CLASS_NAME, [])
            source_hits = [h.get("text", "") for h in hits if "text" in h and h.get("_additional", {}).get("certainty", 1.0) >= CERTAINTY]
            if source_hits:
                answer = " | ".join(source_hits)
                insp.log_tool(agent=AGENT_ID, tool="health.search", query=query, output=answer)
            else:
                delegated = await a2a_delegate(query)
                if delegated:
                    answer = " | ".join([d.get("answer", "") for d in delegated if "answer" in d])
                    source_hits = sum([d.get("source_hits", []) for d in delegated], [])
        except:
            pass
    return {"from": AGENT_ID, "tool": "health.search", "answer": answer, "source_hits": source_hits}
