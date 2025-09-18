import json, time
from pathlib import Path

LOG_FILE = Path("logs/inspector.jsonl")

class Inspector:
    def __init__(self):
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.log_file = LOG_FILE

    def log(self, event: str, data: dict, agent: str = None):
        """Generic log entry"""
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "event": event,
            "agent": agent if agent else "System",
            "data": data
        }
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def read_logs(self):
        if not self.log_file.exists():
            return []
        with open(self.log_file, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f.readlines()]

    def clear_logs(self):
        if self.log_file.exists():
            self.log_file.unlink()

    # Specific logging methods
    def log_tool(self, agent: str, tool: str, query: str, output: str):
        self.log("tool_used", {"tool": tool, "query": query, "output": output}, agent=agent)

    def log_a2a(self, from_agent: str, to_agent: str, query: str):
        self.log("a2a_delegate", {"from": from_agent, "to": to_agent, "query": query}, agent=from_agent)

    def log_weaviate_fetch(self, agent: str, collection: str, success: bool, query: str):
        self.log("weaviate_fetch", {"collection": collection, "success": success, "query": query}, agent=agent)

    def log_fallback(self, agent: str, query: str, answer: str):
        self.log("fallback", {"query": query, "answer": answer}, agent=agent)

    def get_all_logs_json(self):
        return [json.dumps(log, ensure_ascii=False) for log in self.read_logs()]
