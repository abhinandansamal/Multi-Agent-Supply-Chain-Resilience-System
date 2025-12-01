# Sentinell.ai 🛡️
### Autonomous Supply Chain Resilience System

![Build Status](https://img.shields.io/github/actions/workflow/status/abhinandansamal/sentinell-autonomous-supply-chain/deploy.yaml?style=for-the-badge&label=CI%2FCD)
![Python](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/Frontend-Next.js-black?style=for-the-badge&logo=next.js&logoColor=white)
![Cloud](https://img.shields.io/badge/Deploy-Google_Cloud_Run-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)
![AI](https://img.shields.io/badge/AI-Gemini_2.5-8E75B2?style=for-the-badge&logo=google&logoColor=white)
![Terraform](https://img.shields.io/badge/IaC-Terraform-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)

---

## 🚀 The Pitch
Modern supply chains are fragile. When a disruption (e.g., Earthquake in Taiwan) occurs, human teams take **3-5 days** to assess impact, verify inventory, and negotiate with backup suppliers.

**Sentinell.ai** is an agentic system that reduces this Mean Time to Recovery (MTTR) from **days to seconds**.

It autonomously:
1.  **Detects Risks:** Monitors global news for disruptions (e.g., "Port Strikes").
2.  **Analyzes Impact:** Correlates external events with internal inventory databases.
3.  **Negotiates Solutions:** Uses the **A2A (Agent-to-Agent)** protocol to autonomously negotiate price and quantity with backup suppliers.
4.  **Enforces Compliance:** Pauses for "Human-in-the-Loop" approval only when costs exceed pre-defined safety thresholds.

---

## 🏗️ Architecture

The system follows a microservices-based, multi-agent architecture deployed on **Google Cloud Run**.

```mermaid
graph TD
    User[User Dashboard] -->|HTTP/JSON| API[FastAPI Gateway]
    API --> Supervisor[Supervisor Agent]
    
    subgraph "The Brain (Vertex AI)"
        Supervisor -->|Parallel| Watchtower[Watchtower Agent]
        Supervisor -->|Parallel| Procurement[Procurement Agent]
    end
    
    subgraph "Tools & MCP"
        Watchtower -->|Context Compaction| Search[News Search Tool]
        Watchtower -->|MCP Protocol| DB[(SQLite Inventory DB)]
        Procurement -->|HTTP/A2A| Supplier[External Supplier API]
        Procurement -->|OpenAPI| Currency[Currency Converter]
    end
    
    subgraph "State & Memory"
        Procurement --> Memory[(Long-Term Memory Bank)]
    end
```

---

## ✨ Key Features

#### 1. Multi-Agent System
* **Loop Agent (Watchtower)**: Implements a ReAct loop (Observation -> Thought -> Action) to investigate risks iteratively.
* **Parallel Agent (Supervisor)**: Spawns concurrent threads to analyze Political and Weather risks simultaneously (reducing latency by ~50%).
* **Sequential Agent (Procurement)**: Follows a strict compliance workflow (Memory Check -> Quote -> Approval -> Order).

#### 2. Advanced Tooling
* **MCP Integration**: Uses the Model Context Protocol to safely query the internal Inventory Database.
* **OpenAPI Tools**: Consumes a standardized REST API for real-time Currency Conversion.
* **A2A Protocol**: Implements a Client/Server architecture where the Procurement Agent negotiates with a separate Supplier Agent over HTTP.

#### 3. Cognitive Capabilities
* **Context Engineering**: Uses a lightweight LLM (Flash) to "compact" noisy news search results into high-density summaries before reasoning.
* **Long-Term Memory**: Persists supplier reliability scores. If a supplier fails a delivery, the agent "remembers" and avoids them in future sessions.
* **Human-in-the-Loop**: Automatically pauses execution for high-value transactions (> $5,000) to request user approval.

#### 4. Enterprise Grade (DevOps & AIOps)
* **Observability**: Full OpenTelemetry instrumentation traces every "Thought" and "Tool Call" through the system.
* **CI/CD**: GitHub Actions pipeline automatically runs tests and deploys to Cloud Run on push.
* **Infrastructure as Code**: All cloud resources provisioned via Terraform.

---

## 🛠️ Tech Stack
* **AI Core**: Google Vertex AI (Gemini 2.5 Flash-Lite), Google ADK.
* **Backend**: Python 3.11, FastAPI, Uvicorn (Multi-worker).
* **Frontend**: Next.js 14, TypeScript, Tailwind CSS, CopilotKit.
* **Data**: SQLite (Inventory), JSON (Memory Bank).
* **DevOps**: Docker, Google Cloud Build, Terraform, OpenTelemetry.

---

## ⚡ Getting Started
#### Prerequisites
* Google Cloud Project with Vertex AI API enabled.
* Python 3.11+ & Node.js 18+.
* `gcloud` CLI installed and authenticated.

#### 1. Clone & Setup

```bash
git clone [https://github.com/abhinandansamal/sentinell-autonomous-supply-chain.git](https://github.com/abhinandansamal/sentinell-autonomous-supply-chain.git)

cd sentinell-autonomous-supply-chain
```

#### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Create .env file
echo "GOOGLE_CLOUD_PROJECT=your-project-id" > .env
echo "GOOGLE_CLOUD_REGION=us-central1" >> .env

# Initialize Data
python src/tools/generate_data.py

# Run Server (Auto-mounts Supplier API on port 8080)
python -m src.main
```

#### 3. Frontend Setup
```bash
cd ../frontend
npm install

# Create .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8080" > .env.local

# Run Dashboard
npm run dev
```

---

## 🧪 Testing & Evaluation
We use a "Golden Dataset" to validate Agent decision-making accuracy.
```bash
cd backend
# Runs 3 scenarios: Taiwan (Critical), Vietnam (Low), USA (Medium)
pytest tests/test_agents.py -v
```

---

## 📦 Deployment (Cloud Run)
The project includes a fully automated CI/CD Pipeline.

1. Push code to main branch.

2. GitHub Actions triggers:

    * Runs Unit Tests (`pytest`).
    * Builds Docker Container via Cloud Build.
    * Deploys to **Google Cloud Run**.

**Manual Deployment via Terraform:**
```bash
cd infrastructure/terraform
terraform init
terraform apply
```

---

## 📂 Repository Structure

```text
sentinell-autonomous-supply-chain/
├── .github/workflows/         # CI/CD Pipeline definitions
│   └── deploy.yaml            # GitHub Actions workflow for testing & deployment
├── backend/                   # Python/FastAPI Agentic Backend
│   ├── data/                  # Local data persistence
│   │   ├── agent_memory.json  # Long-term memory storage
│   │   └── supply_chain.db    # Inventory SQLite database
│   ├── src/                   # Source Code
│   │   ├── a2a/               # Mock Supplier Service (Agent-to-Agent)
│   │   ├── agents/            # Core Agent Logic (Watchtower, Procurement, Supervisor)
│   │   ├── api/               # Pydantic Models & API Routes
│   │   ├── memory/            # Session Manager & Memory Bank
│   │   ├── tools/             # Custom Tools (MCP, Search, Currency)
│   │   ├── utils/             # Logging & Telemetry setup
│   │   ├── config.py          # Environment configuration
│   │   └── main.py            # Application Entry Point
│   ├── tests/                 # Pytest Suite
│   ├── Dockerfile             # Container definition for Cloud Run
│   ├── pytest.ini             # Testing configuration
│   └── requirements.txt       # Python dependencies
├── frontend/                  # Next.js Dashboard
│   ├── public/                # Static assets
│   ├── src/
│   │   ├── app/               # React Pages (Dashboard UI)
│   │   └── lib/               # API Client (Fetch wrappers)
│   ├── .env.local             # Frontend environment variables
│   ├── next.config.ts         # Next.js configuration
│   └── package.json           # Frontend dependencies
├── infrastructure/terraform/  # Infrastructure as Code (IaC)
│   ├── main.tf                # Cloud Run resource definition
│   ├── variables.tf           # Terraform variables
│   └── terraform.tfvars       # Project-specific values (Git-ignored)
├── logs/                      # Application logs
└── README.md                  # Project Documentation
```

---

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

