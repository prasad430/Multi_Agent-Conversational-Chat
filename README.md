# Multi-Agent Chat System

A Python-based multi-agent chat system where health and sports agents respond to user queries using  Weaviate. The system supports agent-to-agent communication (A2A) and a web UI for user interaction.

---

## Project Structure

 .env – Configuration for ports, API keys, and agent IDs

app.py – Web UI for chat

coordinator.py – Sends queries to agents and collects answers

discovery.py – Keeps track of active agents

health_agent.py – Health agent service

sports_agent.py – Sports agent service

inspector.py – Logs agent activity

weaviate_setup.py – Creates schema and adds sample data

run_all.py – Starts all services together

requirements.txt – Python packages needed




## Setup Steps

### Create a virtual environment

* python -m venv venv

* venv\Scripts\activate         # Windows




### Install dependencies

* pip install -r requirements.txt




###   Load Sample Data

* python weaviate_setup.py

This will:

Create HealthNote and SportsNote classes

Add example health and sports documents




###   Run All Services

* python run_all.py


This will launch:

Discovery service → port 9000

Health Agent → port 8001

Sports Agent → port 8002

Coordinator → port 8000

Web UI → port 8010 (with live reload and open this url)




### Access Web UI

* Open in your browser:http://localhost:8010

Type queries in the input box

Responses from agents appear in the chat

JSON responses appear in the inspector section




###  Stop the System

* Press Ctrl+C in the terminal running run_all.py. All services will shut down gracefully.



















