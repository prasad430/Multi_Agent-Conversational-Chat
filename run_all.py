import subprocess, time, os, signal
from dotenv import load_dotenv
import weaviate
from weaviate.auth import AuthApiKey

load_dotenv()

WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
STARTUP_TIMEOUT = int(os.getenv("WEAVIATE_STARTUP_TIMEOUT", "120"))

def wait_for_weaviate(client, timeout=120, interval=5):
    start_time = time.time()
    while True:
        try:
            if client.is_ready():
                print("✅ Weaviate is ready!")
                return True
        except:
            pass
        if time.time() - start_time > timeout:
            print(f"❌ Weaviate did not become ready in {timeout}s.")
            return False
        time.sleep(interval)

client = weaviate.Client(
    url=WEAVIATE_URL,
    auth_client_secret=AuthApiKey(api_key=WEAVIATE_API_KEY),
    timeout_config=(30, 120)
)

if not wait_for_weaviate(client, STARTUP_TIMEOUT):
    exit(1)

services = [
    ("Discovery", ["uvicorn", "discovery:app", "--port", "9000", "--log-level", "critical"]),
    ("Health Agent", ["uvicorn", "health_agent:app", "--port", "8001", "--log-level", "critical"]),
    ("Sports Agent", ["uvicorn", "sports_agent:app", "--port", "8002", "--log-level", "critical"]),
    ("Coordinator", ["uvicorn", "coordinator:app", "--port", "8000", "--log-level", "critical"]),
    ("Web UI", ["uvicorn", "app:app", "--reload", "--port", "8010"])
]

processes = []

def start_services():
    # Start Coordinator first
    for name, cmd in services:
        print(f"🚀 Starting {name}...")
        # Web UI waits until Coordinator is up
        if name == "Web UI":
            time.sleep(5)  # give Coordinator time to start
            p = subprocess.Popen(cmd)
        else:
            p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        processes.append((name, p))
        time.sleep(2)
    print("✅ All services started!")

def stop_services():
    print("🛑 Shutting down...")
    for name, p in processes:
        try:
            p.send_signal(signal.SIGTERM)
            p.wait(timeout=5)
        except:
            p.kill()
    print("✅ Services stopped.")

if __name__ == "__main__":
    try:
        start_services()
        for _, p in processes:
            p.wait()
    except KeyboardInterrupt:
        stop_services()
