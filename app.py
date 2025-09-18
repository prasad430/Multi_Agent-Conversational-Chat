import logging
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import httpx
import asyncio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("web_ui")

app = FastAPI()

# Coordinator connection settings
COORDINATOR_URL = "http://localhost:8000"
COORDINATOR_RETRY_INTERVAL = 3  # increased interval
COORDINATOR_MAX_RETRIES = 20    # increased retries

class ChatRequest(BaseModel):
    query: str

async def post_to_coordinator(query: str):
    """Send query to coordinator with retries."""
    for attempt in range(1, COORDINATOR_MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=10) as client:  # increased timeout
                r = await client.post(f"{COORDINATOR_URL}/ask", json={"query": query})
                r.raise_for_status()
                return r.json()
        except Exception as e:
            logger.warning(f"Attempt {attempt}: Coordinator not available: {e}")
            await asyncio.sleep(COORDINATOR_RETRY_INTERVAL)
    return {"agent_responses": [], "error": "Coordinator not available after multiple attempts."}

@app.post("/chat")
async def chat(req: ChatRequest):
    logger.info(f"📩 User query: {req.query}")
    data = await post_to_coordinator(req.query)
    logger.info(f"✅ Coordinator response: {data}")
    return data

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Multi-Agent Chat</title>
    <style>
        body { font-family: Arial; margin: 30px; background: #f4f4f9; }
        h1 { color: #333; }
        #chat-box, #inspector-box { width: 100%; height: 300px; border: 1px solid #ccc;
                                    padding: 10px; overflow-y: auto; background: #fff; margin-bottom: 20px; border-radius: 5px;}
        input { width: 80%; padding: 10px; margin-top: 10px; border-radius: 5px; border: 1px solid #ccc; }
        button { padding: 10px; border-radius: 5px; background: #4CAF50; color: white; border: none; cursor: pointer; }
        button:hover { background: #45a049; }
        .user { color: blue; margin-bottom: 5px; }
        .bot { color: green; margin-bottom: 10px; }
        .inspector { color: purple; margin-bottom: 10px; font-size: 0.9em; white-space: pre-wrap; }
        .error { color: red; margin-bottom: 10px; }
    </style>
</head>
<body>
<h1>🧑‍💻 Multi-Agent Chat</h1>

<div id="chat-box"></div>
<input type="text" id="query" placeholder="Type your question..." autofocus />
<button onclick="sendMessage()">Send</button>

<h2>🔍 Inspector (JSON)</h2>
<div id="inspector-box">No messages yet...</div>

<script>
async function sendMessage() {
    let query = document.getElementById("query").value.trim();
    if (!query) return;

    let chatBox = document.getElementById("chat-box");
    chatBox.innerHTML += "<div class='user'><b>You:</b> " + query + "</div>";

    try {
        let response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: query })
        });
        let data = await response.json();

        if (data.agent_responses && data.agent_responses.length > 0) {
            for (let res of data.agent_responses) {
                chatBox.innerHTML += `<div class='bot'><b>${res.from}:</b> ${res.answer}</div>`;
            }
        } else {
            chatBox.innerHTML += `<div class='error'><b>System:</b> ${data.error || 'No agents responded.'}</div>`;
        }

        let inspectorBox = document.getElementById("inspector-box");
        inspectorBox.innerHTML = JSON.stringify(data, null, 2);
        inspectorBox.scrollTop = inspectorBox.scrollHeight;

    } catch (err) {
        chatBox.innerHTML += "<div class='error'><b>System:</b> Failed to connect to Coordinator.</div>";
    }

    chatBox.scrollTop = chatBox.scrollHeight;
    document.getElementById("query").value = "";
}

// Allow Enter key to submit
document.getElementById("query").addEventListener("keyup", function(event) {
    if (event.key === "Enter") sendMessage();
});
</script>
</body>
</html>
"""
