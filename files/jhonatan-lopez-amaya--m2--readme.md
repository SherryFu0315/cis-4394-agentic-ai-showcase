# Post-Purchase Concierge (PPC)

A full-stack agentic AI system that tracks warranties and return windows from purchase receipts, researches live retailer policies via real web search, and helps users initiate return claims — all powered by a multi-agent pipeline running on Groq's Llama 3.3-70B.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18 + Vite 5 |
| **Styling** | Tailwind CSS 3 |
| **Backend** | Python 3.13 + FastAPI |
| **LLM Provider** | Groq (Llama 3.3-70B Versatile) |
| **Web Search** | Tavily Search API |
| **Agent Coordination** | Fixed pipeline (Orchestrator → Inbox Scout → Agent 1 → Agent 2) |

---

## Milestone I — Web UI

**Goal:** Build a usable front-end for submitting tasks and viewing agent responses.

### Features

- **Dashboard** with Recent Purchases table: product name, price, retailer, purchase date, warranty/return status badges with visual countdown bars.
- **Ask the Concierge** chat box: natural-language questions with reasoning display and source links.
- **Action buttons:** Sync Inbox, Research Policies.
- **Sidebar navigation:** Purchases, Active Claims, Settings, Policy Database.
- **FinTech-style design:** Deep Navy sidebar, Emerald active status, Amber expiring-soon indicators.

### Deliverables

- [x] Web UI (React + Tailwind) to submit tasks and view agent responses.
- [x] Functional and clearly structured; usable by a non-technical user.
- [x] Short description (README) with tech stack and screenshot placeholders.
- [x] Code for the front-end in the repo.

---

## Milestone II — Multi-Agent Workflow

**Goal:** Implement a real multi-agent pipeline where each agent uses an LLM and has a distinct, restricted role.

### Architecture Overview

The system implements a **fixed pipeline** coordination mechanism:

```
User Question
      │
      ▼
Orchestrator (Intent Classifier)
      │
      ▼
Inbox Scout (Python — receipt lookup, no LLM)
      │
      ▼
Agent 1: Policy Research Agent  ──► Tavily Web Search (live internet)
      │
      ▼
Agent 2: Purchase Concierge Agent  ──► Personalized response
      │
      ▼
User Answer + Start Claim option
```

### Agent 1 — Policy Research Agent

| Property | Detail |
|----------|--------|
| **Role** | Tool-using Executor |
| **Model** | Groq / Llama 3.3-70B Versatile |
| **Tool** | `web_search` via Tavily Search API |
| **Input** | Retailer name, product name, membership tier |
| **Output** | Structured policy data: return window, conditions, exclusions, warranty summary, membership benefit, real source URLs |

This agent uses **Groq function calling** to drive an agentic search loop. It decides what to search, reads the results from live retailer pages, and extracts structured policy facts. It makes up to 4 real web searches per retailer per request.

**Restriction:** The agent is scoped to policy research only. It has no access to user data, no write tools, and no ability to take actions — only search and synthesize.

### Agent 2 — Purchase Concierge Agent

| Property | Detail |
|----------|--------|
| **Role** | Domain Expert / Explainer |
| **Model** | Groq / Llama 3.3-70B Versatile |
| **Tools** | None — synthesis only |
| **Input** | User's question, purchase context, Agent 1's live policy findings |
| **Output** | Personalized, intent-aware answer with exact day-count math |

This agent receives Agent 1's research and synthesizes it with the user's specific purchase data into a direct, friendly answer. It detects the user's intent (return eligibility, return process, warranty, etc.) and tailors its response accordingly. It also outputs a `claim_context` object that the UI uses to offer a "Start Return Claim" button when the item is eligible.

**Restriction:** No tool access. Cannot search the web, modify data, or take external actions.

### Coordination Mechanism

**Type:** Fixed pipeline (A → B → C)

The Orchestrator (`POST /api/agent/ask`) controls execution order:
1. Classifies intent from the user's question (fast LLM call, temperature 0.1)
2. Runs Inbox Scout to locate the purchase receipt (Python keyword lookup — no LLM, no network)
3. Calls Agent 1 to fetch live policy data from the web
4. Calls Agent 2 to synthesize the final personalized answer using Agent 1's output

Each agent's output becomes the next agent's input. Agent 2 cannot run without Agent 1's research, and Agent 1 cannot run without the purchase context from the Inbox Scout.

### New Features in Milestone II

**Sync Inbox**
- Animated progress bar with 5 steps ("Connecting to Gmail…", "Scanning 1,243 emails…", etc.)
- On completion, a membership modal pops up asking the user to select their Amazon and Best Buy membership tier before purchases are revealed

**Research Policies button**
- Triggers Agent 1 to run real Tavily web searches for each retailer (Best Buy, Amazon, Oura)
- Navigates to the Policy Database tab and populates it with live-researched data
- Shows the actual search queries Agent 1 made, the number of sources found, and expandable policy cards

**Policy Database**
- Starts empty — populated only after "Research Policies" is clicked
- Each card shows: policy summary, return conditions, membership benefit, warranty info, exclusions, and real URLs from Tavily
- Only shows the 3 retailers present in the user's purchase history (no hardcoded Apple/Target/Walmart)

**Active Claims**
- Starts empty — no hardcoded mock claims
- When the Concierge determines an item is eligible for return, a green "Start Return Claim" banner appears in the chat
- Clicking it creates a claim in the backend (in-memory store) and navigates to Active Claims
- Each claim includes the real source URLs found by Agent 1 for the user to proceed with the return

**Membership Selection**
- Amazon: toggle between Standard / Amazon Prime (with a "Link Amazon Account" button)
- Best Buy: three-tier card selector — My Best Buy (Free / 15d), My Best Buy Plus (30d), My Best Buy Total (45d) — with a "Link Best Buy Account" button
- Oura: no paid membership tiers — always Standard 30-day
- Selection updates the backend (`POST /api/user/memberships`) so all agents use the correct return window

### Supported Retailers

| Retailer | Membership Tiers | Return Window |
|----------|-----------------|---------------|
| Best Buy | Free (15d) · Plus (30d) · Total (45d) | Tier-dependent |
| Amazon | Standard (30d) · Prime (30d) | Same window, Prime has easier process |
| Oura | Standard only (30d) | Flat 30 days |

### Data Privacy Note

The demo uses **fake purchase data** (hardcoded product names and dates relative to today). The only real data sent to external APIs:
- To **Groq:** the user's question text, product name, retailer, purchase date, and membership tier label
- To **Tavily:** search query strings (e.g. "Best Buy Total return policy 2025")

The user's name and email are hardcoded demo values and are never sent to any external service.

### Deliverables

- [x] At least two distinct agents with different roles (Policy Research Agent + Purchase Concierge Agent)
- [x] Tool-using executor agent (Agent 1 with Tavily web search via Groq function calling)
- [x] Domain expert / explainer agent (Agent 2 — synthesis only)
- [x] Defined coordination mechanism (fixed pipeline with orchestrator controller)
- [x] Visible pipeline UI showing each agent's step, search queries made, and intent detected
- [x] Live web data — real retailer policy pages fetched on every request

---

## Getting Started

### Prerequisites

- **Node.js 18+** and npm
- **Python 3.11+** and pip
- A **Groq API key** — free at [console.groq.com](https://console.groq.com)
- A **Tavily API key** — free tier at [tavily.com](https://tavily.com)

### 1. Backend

```bash
cd code/backend
pip install -r requirements.txt
```

Create `code/backend/.env`:
```
GROQ_API_KEY=your_groq_key_here
TAVILY_API_KEY=your_tavily_key_here
```

Start the server:
```bash
uvicorn main:app --reload --port 8000 --app-dir .
```

### 2. Frontend

```bash
cd code/frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

### Demo Flow

1. Click **Sync Inbox** → watch the progress bar → confirm your memberships in the modal → purchases appear
2. Click **Research Policies** → Agent 1 runs live Tavily searches → Policy Database populates with real data
3. Ask the **Concierge** a question (e.g. *"Can I still return my Canon camera?"*) → watch both agents work in the pipeline → if eligible, click **Start Return Claim**
4. Check **Active Claims** to see your claim with real return portal links

---

## Project Structure

```
PPC/
├── code/
│   ├── backend/
│   │   ├── main.py              # All agents, endpoints, LLM calls
│   │   ├── requirements.txt
│   │   └── .env                 # GROQ_API_KEY + TAVILY_API_KEY (not committed)
│   └── frontend/
│       ├── src/
│       │   ├── App.jsx                        # State, routing, action handlers
│       │   └── components/
│       │       ├── AgentInteraction.jsx       # Chat box + pipeline UI + Start Claim
│       │       ├── ActionButtons.jsx          # Sync Inbox, Research Policies
│       │       ├── PurchasesTable.jsx         # Purchases + sync progress bar
│       │       ├── PolicyDatabase.jsx         # Dynamic from research results
│       │       ├── ActiveClaims.jsx           # Dynamic from claims state
│       │       ├── Settings.jsx               # Membership tier selectors
│       │       ├── SyncModal.jsx              # Post-sync membership confirmation
│       │       ├── Sidebar.jsx
│       │       └── WarrantyStatus.jsx
│       ├── vite.config.js                     # API proxy /api → localhost:8000
│       └── package.json
├── docs/
│   ├── AGENT_ARCHITECTURE.md    # Mermaid diagrams — flowchart, sequence, ER
│   ├── DESIGN_DOCUMENT.md       # Agent design doc (roles, I/O, comms, failures)
│   ├── SECURITY_ANALYSIS.md     # Vulnerability register with mitigations
│   └── assets/                  # Screenshots
└── README.md
```
