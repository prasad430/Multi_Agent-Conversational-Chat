import weaviate, os
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

client = weaviate.Client(
    url=os.getenv("WEAVIATE_URL"),
    auth_client_secret=weaviate.AuthApiKey(api_key=os.getenv("WEAVIATE_API_KEY"))
)

# --- Clean old schema ---
for cls in ["HealthNote", "SportsNote"]:
    try:
        client.schema.delete_class(cls)
    except:
        pass

# --- Define schema ---
health_class = {
    "class": "HealthNote",
    "description": "Health domain notes",
    "properties": [{"name": "text", "dataType": ["text"]}]
}
sports_class = {
    "class": "SportsNote",
    "description": "Sports domain notes",
    "properties": [{"name": "text", "dataType": ["text"]}]
}

client.schema.create_class(health_class)
client.schema.create_class(sports_class)

# --- Sample Health Data ---
health_docs = [
    {"text": "If you have fever, rest and drink fluids. Take paracetamol 500 mg if needed."},
    {"text": "Chest pain: seek immediate medical attention; avoid strenuous activity."},
    {"text": "For headaches, ensure proper hydration and avoid excessive screen time."},
    {"text": "Maintain at least 7-8 hours of sleep daily for good health."},
    {"text": "Regular exercise and a balanced diet reduce the risk of lifestyle diseases."},
    {"text": "Diabetic patients should monitor blood sugar regularly and avoid sugary foods."},
    {"text": "High blood pressure can be managed with reduced salt intake and regular checkups."}
]

# --- Sample Sports Data ---
sports_docs = [
    {"text": "Football is played with 11 players per side; avoid playing while sick."},
    {"text": "Cricket requires warmups and is usually played in 11-player teams."},
    {"text": "Basketball is played with 5 players per side and requires good stamina."},
    {"text": "Always stretch before running to avoid muscle injuries."},
    {"text": "Swimming is a low-impact sport suitable for people with joint problems."},
    {"text": "Badminton improves reflexes and requires quick footwork."},
    {"text": "Wearing proper shoes reduces the risk of sports-related injuries."}
]

# --- Insert Health Data ---
print("📌 Inserting Health Notes...")
with client.batch as batch:
    for d in health_docs:
        batch.add_data_object(d, "HealthNote")

# --- Insert Sports Data ---
print("📌 Inserting Sports Notes...")
with client.batch as batch:
    for d in sports_docs:
        batch.add_data_object(d, "SportsNote")

print("✅ Schema + sample data loaded into Weaviate Cloud")

