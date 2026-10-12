<p align="center">
  <img src="https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/heart-handshake.svg" width="64" height="64" alt="AuraMatch AI Logo" />
</p>

<h1 align="center">AuraMatch AI — Autonomous Agentic Dating Platform</h1>

<p align="center">
  <em>Autonomous multi-agent dating platform where AI agents date on behalf of consenting users using LinkedIn & Instagram profile evidence to produce explainable rankings.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Next.js-14.2+-000000?style=flat&logo=next.js&logoColor=white" alt="Next.js 14" />
  <img src="https://img.shields.io/badge/React-18.3+-61DAFB?style=flat&logo=react&logoColor=black" alt="React 18" />
  <img src="https://img.shields.io/badge/TypeScript-5.4+-3178C6?style=flat&logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-3.4+-06B6D4?style=flat&logo=tailwindcss&logoColor=white" alt="Tailwind CSS" />
  <img src="https://img.shields.io/badge/Pytest-52%20Passed-4EAA25?style=flat&logo=pytest&logoColor=white" alt="52 Tests Passing" />
  <img src="https://img.shields.io/badge/Alembic-Migrations_Active-007ACC?style=flat" alt="Alembic Migrations" />
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white" alt="Docker Ready" />
  <img src="https://img.shields.io/badge/License-MIT-green.svg?style=flat" alt="License MIT" />
</p>

---

## Table of Contents

1. [Executive Summary & Core Mission](#1-executive-summary--core-mission)
2. [High-Level Technical Architecture & Data Flow](#2-technical-architecture--data-flow)
3. [Product Pages & Route Matrix](#3-product-pages--route-matrix)
4. [Multi-Component Mathematical Ranking Methodology](#4-multi-component-mathematical-ranking-methodology)
5. [Security & Architectural Hardening](#5-security--architectural-hardening)
6. [Multi-LLM Provider Engine](#6-multi-llm-provider-engine)
7. [REST API Endpoint Reference](#7-rest-api-endpoint-reference)
8. [Batch Manifest Import for Real Consenting Cohorts](#8-batch-manifest-import-for-real-consenting-cohorts)
9. [Repository Structure](#9-repository-structure)
10. [Local Quickstart & Development](#10-local-quickstart--development)
11. [Database Schema & Alembic Migrations](#11-database-schema--alembic-migrations)
12. [Automated Test Suite Verification (52 Tests)](#12-automated-test-suite-verification-52-tests)
13. [Continuous Integration (GitHub Actions)](#13-continuous-integration-github-actions)
14. [Production Deployment Blueprint](#14-production-deployment-blueprint)
15. [Technical Demonstration Storyboard (3-Minute Walkthrough)](#15-technical-demonstration-storyboard-3-minute-walkthrough)
16. [Troubleshooting & FAQ](#16-troubleshooting--faq)

---

## 1. Executive Summary & Core Mission

Modern digital dating suffers from swipe fatigue, deceptive profiles, low response rates, and opaque black-box recommendation algorithms. **AuraMatch AI** solves these systemic issues by pioneering an **autonomous agentic dating ecosystem**:

1. **Autonomous Personal AI Agents**: Each participant is represented by an intelligent agent equipped with the user's verified background, authentic interests, lifestyle cadence, and explicit communication goals.
2. **Strict Profile Evidence Grounding**: Profiles are constructed exclusively from public LinkedIn and Instagram data, with mandatory consent verification and source attribution.
3. **Rigorous Evidence Partitioning**:
   - **Explicit Facts**: Direct statements backed by concrete source URLs (e.g., career milestones, verified degrees).
   - **Observed Public Signals**: Demonstrated activities (e.g., photography portfolios, athletic events, published open-source work).
   - **Model-Generated Inferences**: Probabilistic hypotheses tagged with strict confidence scores ($0.0 \le c \le 1.0$) and supporting evidence rationales.
   - **Explicit Unknowns**: Deliberately cataloged gaps in knowledge to prevent hallucinated assumptions.
4. **Authentic Multi-Turn Coffee Date Simulations**: Autonomous agents participate in genuine, multi-turn conversational dates across a deterministic state machine. They ask insightful questions, probe compatibility, highlight mutual passions, identify friction points, and compile independent post-date evaluation scorecards.
5. **Explainable Multi-Component Mathematical Ranking**: Compatibility is computed using deterministic mathematics: preference alignment, Jaccard interest overlap, lifestyle harmony, date interaction chemistry, and harmonic reciprocal scoring ($S_{\text{reciprocal}}$)—eliminating arbitrary black-box scores.
6. **Transparent Data Provenance**: Strict runtime and visual partitioning between `SYNTHETIC BENCHMARK` development fixtures (`is_synthetic=True`) and `VERIFIED RECORD` consenting cohorts (`is_synthetic=False`, `source_verified=True`, `consent_verified=True`).
7. **Production-Grade Infrastructure**: Dockerized multi-stage containers, PostgreSQL connection pooling, timing-attack safe admin authentication, SSRF protection, Alembic database migrations, and turn-key deployment blueprints for Render and Vercel.

---

## 2. Technical Architecture & Data Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Next.js 14 Frontend UI                          │
│  - 9 Routes: Overview Dashboard, Ingestion, Directory, Profile Analysis│
│    Live Simulation, History & Replay, Rankings, Demo, Admin Operations │
│  - Data Provenance Badges (SYNTHETIC BENCHMARK vs. VERIFIED RECORD)    │
│  - Sanitized Observable Decision Strategy Drawer                       │
│  - Real-time Server-Sent Events (SSE) Dating Stream Viewer             │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │ HTTP REST API (X-Admin-Key / Bearer Auth)
┌───────────────────────────────────▼────────────────────────────────────┐
│                         FastAPI Python Backend                         │
│  - Timing-Safe Admin Authentication (X-Admin-Key & Bearer Token)       │
│  - SSRF-safe URL validation & Private IP/Loopback/Metadata Blocklist   │
│  - Strict Data Provenance Adapters (LinkedIn, Instagram, Manifest)     │
│  - Profile Analyzer (Evidence extraction & Non-inference of sensitive) │
│  - Agent Dating Harness (State machine & observable decision factors)  │
│  - Explainable Compatibility Engine (Directional & harmonic reciprocal)│
│  - Resilient Error Masking with UUID correlation IDs                   │
│  - Automatic Startup Lifespan Demo Seeding with Idempotency            │
└───────────────────────▲───────────────────────▲────────────────────────┘
                        │                       │
      ┌─────────────────┴─┐                   ┌─┴────────────────────────┐
      ▼                   ▼                   ▼                          ▼
┌───────────────────────────┐   ┌──────────────────────────────────────────────┐
│     Persistence Layer     │   │             Multi-LLM Provider Engine        │
│ - SQLAlchemy 2.0 ORM      │   │ - Groq Cloud Engine (Recommended)            │
│ - Alembic Migrations      │   │   (openai/gpt-oss-20b, gpt-oss-120b, 70b)    │
│ - PostgreSQL Pool (Prod)  │   │ - Google Gemini API (Alternative)            │
│ - SQLite (Dev / QA Tests) │   │   (gemini-2.5-flash with dynamic discovery)  │
│ - Cascade Foreign Keys    │   │ - OfflineMockProvider (Zero-credential harness│
│ - Cascading Withdrawals   │   │   for offline tests, isolated CI/CD builds)  │
└───────────────────────────┘   └──────────────────────────────────────────────┘
```

---

## 3. Product Pages & Route Matrix

The frontend is built with **Next.js 14 (App Router)**, **TypeScript**, and **Tailwind CSS**, featuring 9 distinct routes:

| # | Route | Page Name | Core Capabilities |
|:---:|---|---|---|
| **1** | `/` | **Overview Dashboard** | Real-time aggregate telemetry: total participants, analyzed profiles, dynamically calculated theoretical pairs ($N(N-1)/2$), active dating sessions, completion percentage, token usage, and cumulative cost/latency tracking. |
| **2** | `/ingest` | **Participant Ingestion** | Self-serve onboarding form with real-time LinkedIn & Instagram URL validation, anti-SSRF protections, duplicate URL prevention, and batch cohort manifest JSON import. |
| **3** | `/participants` | **Participant Directory** | Searchable and filterable directory by name, location, and demographic tags. Displays verified profile source links, consent timestamps, and clear `SYNTHETIC BENCHMARK` vs `VERIFIED RECORD` badges. |
| **4** | `/participants/[id]` | **Profile Analysis & Evidence** | Deep-dive profile breakdown: explicit verified facts, career focus, demonstrated hobbies, calibrated probabilistic inferences (with confidence %), explicit unknowns, raw quote evidence cards, and admin-authenticated withdrawal/deletion. |
| **5** | `/dates/live` | **Live Dating Simulation** | Real-time agent coffee date execution: alternating dialogue turns, active topic badges, questions asked, and an interactive **"Inspect Decision Strategy"** slide-out drawer revealing internal reasoning factors without leaking raw prompt scaffolding. |
| **6** | `/dates` & `/dates/[id]` | **Session History & Replay** | Immutable session ledger with token consumption, cost metrics, latency statistics, outcome statuses (`second_date_agreed`, `mutual_friendship`, `polite_pass`), and full turn-by-turn interactive replay mode. |
| **7** | `/rankings` | **Compatibility Rankings** | Ranked candidate leaderboard for any selected participant. Inspect detailed sub-scores (Preferences, Interests, Lifestyle, Date Flow, Confidence) and adjust live ranking weights via an interactive slider drawer. |
| **8** | `/demo` | **Benchmark Demonstration** | Permanent showcase of the 25-participant cohort run, demonstrating all 300 potential combinatorial pairs, execution status, simulated transcripts, and comprehensive ranking coverage. |
| **9** | `/admin` | **Operations & System Health** | Admin dashboard secured with API key authentication: active LLM provider configuration, token/cost counters, health & readiness probes, background job queue manager, and database re-seeder. |

---

## 4. Multi-Component Mathematical Ranking Methodology

AuraMatch AI replaces arbitrary black-box percentages with a mathematically rigorous, explainable compatibility formulation:

```
                                  Compatibility Formulation
                                  
  Candidate B ──[Profile Data]──┐
                                ▼
  Candidate A ──[Dating Flow]──► Directional Score S(A → B) ──┐
                                                              ▼
  Candidate B ──[Dating Flow]──► Directional Score S(B → A) ─► Harmonic Reciprocal S_reciprocal
                                                              ▲
                                                    Penalizes One-Sided Matches
```

### A. Directional Compatibility Score: $S(A \to B) \in [0, 100]$
Measures how comprehensively Candidate $B$'s profile and date interaction satisfy Participant $A$'s expectations:

$$S(A \to B) = w_{\text{pref}} S_{\text{pref}} + w_{\text{int}} S_{\text{int}} + w_{\text{life}} S_{\text{life}} + w_{\text{eng}} S_{\text{eng}} + w_{\text{val}} S_{\text{val}}$$

Where the configurable default weights sum to $1.0$:
- $w_{\text{pref}} = 0.25$ (Relationship Preference Alignment)
- $w_{\text{int}} = 0.25$ (Shared Demonstrated Interests & Hobbies)
- $w_{\text{life}} = 0.20$ (Lifestyle & Rhythm Harmony)
- $w_{\text{eng}} = 0.20$ (Date Interaction Engagement)
- $w_{\text{val}} = 0.10$ (Communication & Core Values Alignment)

#### Sub-Component Formulations:
1. **Preference Score ($S_{\text{pref}}$)**: Evaluates overlap between $A$'s relationship preferences and $B$'s verified attributes.
2. **Interest Overlap ($S_{\text{int}}$)**: Jaccard similarity index across verified hobbies ($H$) and stated interests ($I$):
   $$\text{Jaccard}(A, B) = \frac{|H_A \cap H_B| + |I_A \cap I_B|}{\max(|H_A \cup H_B|, 1)} \times 100$$
3. **Lifestyle Fit ($S_{\text{life}}$)**: Daily routine, active pace, and career/leisure balance compatibility ($0-100$).
4. **Date Engagement Score ($S_{\text{eng}}$)**: Derived from the post-date evaluation completed by $A$'s agent:
   $$S_{\text{eng}} = \left(0.40 \cdot \text{Chemistry} + 0.40 \cdot \text{Comfort} + 0.20 \cdot \mathbf{1}_{\text{WouldDateAgain}} \times 10\right) \times 10$$
5. **Values Alignment ($S_{\text{val}}$)**: Mutual communication priority and core philosophical alignment ($1-10 \times 10$).

### B. Harmonized Reciprocal Score: $S_{\text{reciprocal}}(A, B)$
Human attraction is fundamentally directional, but sustainable partnerships require mutual balance. The platform computes the **harmonic mean** between $S(A \to B)$ and $S(B \to A)$, which strongly penalizes asymmetric, one-sided attraction:

$$S_{\text{reciprocal}}(A, B) = \frac{2 \cdot S(A \to B) \cdot S(B \to A)}{S(A \to B) + S(B \to A) + \epsilon}$$

*(where $\epsilon = 10^{-6}$ prevents division by zero).*

> **Example**: If Participant $A$ rates Candidate $B$ at $90/100$, but Candidate $B$ rates Participant $A$ at only $30/100$:
> - Arithmetic Mean: $\frac{90 + 30}{2} = 60.0$ *(Misleadingly moderate)*
> - Harmonic Reciprocal Mean: $\frac{2 \cdot 90 \cdot 30}{90 + 30} = 45.0$ *(Accurately reflects mutual friction)*

### C. Deterministic Tie-Breaking Order
To ensure 100% reproducible and audit-safe match ordering, candidate rankings are resolved through a strict deterministic hierarchy:
1. `reciprocal_score` (Descending)
2. `confidence_score` (Descending — prioritizing candidates with higher volumes of verified evidence)
3. `individual_score` (Descending)
4. `target_participant_id` (Ascending lexicographical sort)

---

## 5. Security & Architectural Hardening

The codebase has undergone comprehensive security and reliability audits:

| Severity | Domain | Threat / Vulnerability | Hardened Implementation |
|:---:|---|---|---|
| **P0** | **Access Control** | Unauthenticated destructive endpoints (`DELETE /participants/{id}`, `POST /runs`, `POST /admin/seed-demo`). | Implemented timing-attack safe `require_admin_auth` dependency validating `X-Admin-Key` or `Authorization: Bearer <key>`. Production startup rejects default/insecure keys. |
| **P0** | **CORS & Information Leakage** | Permissive wildcard origins (`*`); raw database tracebacks leaking internal SQL schemas. | Restricted CORS via `BACKEND_CORS_ORIGINS` with explicit allowed origins. Added global exception handlers masking errors behind UUID `correlation_id`s. |
| **P1** | **Data Integrity & Traceability** | Synthetic fixtures masquerading as verified real profiles; hardcoded pair assumptions. | Added `is_synthetic`, `source_verified`, `consent_verified` flags across database models, schemas, and UI badges. Dynamically compute $N(N-1)/2$ combinations. |
| **P1** | **SSRF Prevention** | Malicious participant URLs accessing cloud metadata (AWS 169.254.169.254) or local loopback. | Strict regex validation for LinkedIn (`linkedin.com/in/...`) and Instagram (`instagram.com/...`), handle extraction, and automatic DNS-resolution blocking of private IP ranges (RFC 1918, RFC 3927). |
| **P1** | **Participant Rights** | Right-to-be-forgotten / withdrawal lacked cascading logic. | Added `/withdraw` and `/verify` endpoints with cascade deletion (`CASCADE`) across dating sessions, messages, evaluations, and rankings. Withdrawn participants are barred from simulations. |
| **P2** | **AI Provider Integrity** | Mock providers disguising themselves as live LLMs; API keys leaking in tracebacks. | Explicit provider labeling (`provider="offline_mock"` vs `"groq"` vs `"gemini"`). Added regex sanitization stripping `gsk_*` and `AIza*` keys from all runtime error messages. |
| **P2** | **Privacy & Prompt Scaffolding** | Raw chain-of-thought leaking internal prompt instructions and private user prompts. | Structured turns into `decision_summary`, `decision_factors`, `question_asked`, and `interest_referenced`. UI presents a safe **"Inspect Decision Strategy"** drawer. |
| **P3** | **Database Connection Scaling** | SQLite database locks under concurrent load; lack of PostgreSQL connection pooling. | Added PostgreSQL pooling configuration (`pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`). Added Alembic migration framework (`alembic upgrade head`). |

---

## 6. Multi-LLM Provider Engine

AuraMatch AI features a resilient, multi-tiered LLM abstraction layer ([`app/llm/provider.py`](file:///c:/Users/rohit/Downloads/datingSite/backend/app/llm/provider.py)):

### Supported Providers:

1. **Groq Cloud Engine (`LLM_PROVIDER=groq`) — *Recommended for Production***
   - Ultra-fast token generation and minimal latency.
   - Default Model: `openai/gpt-oss-20b` (also supports `openai/gpt-oss-120b`, `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`).
   - Automated 404 model failover without looping over failed candidates.
   - Transient network error retries with exponential backoff (HTTP 429, 500, 503).
   - Dynamic model discovery automatically filters out non-chat utilities (prompt-guard, whisper, embed, safety classifiers).
   - Automatic API key sanitization on quota or rate errors.

2. **Google Gemini API (`LLM_PROVIDER=gemini`) — *Alternative Production Provider***
   - Default Model: `gemini-2.5-flash` (with automated fallback to `gemini-1.5-flash`).
   - Dynamic model discovery: Queries Google API to discover available chat models if specified model encounters deprecation or 404 errors.
   - Robust JSON extraction handling markdown code fences (` ```json `), raw dictionaries, and plain strings.

3. **Offline Mock Provider (`LLM_PROVIDER=offline_mock`) — *Zero-Credential Harness***
   - Deterministic offline execution requiring zero API keys or external network connectivity.
   - Fully simulates profile analysis, multi-turn dating dialogue, post-date scorecards, and ranking explanations.
   - Transparently sets `provider="offline_mock"` in all response payloads to guarantee observability honesty.

### Switching Providers via `.env`:
```env
# Fast Groq Cloud (Recommended)
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b

# Or Google Gemini
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash

# Or Zero-Credential Offline Test Harness
LLM_PROVIDER=offline_mock
```

---

## 7. REST API Endpoint Reference

All endpoints are prefixed with `/api/v1` and documented interactively via OpenAPI Swagger at `http://localhost:8000/api/v1/docs`.

### System Health & Administration
| Method | Endpoint | Auth | Description |
|---|---|:---:|---|
| `GET` | `/health` | None | System health check (database connectivity, active LLM provider, uptime). |
| `GET` | `/ready` | None | Container readiness probe for Kubernetes / cloud orchestrators. |
| `GET` | `/admin/config` | Admin | Retrieve active platform configuration (weights, timeout limits, environment). |
| `POST` | `/admin/config` | Admin | Update runtime ranking weights and simulation parameters dynamically. |
| `GET` | `/admin/metrics` | Admin | Telemetry metrics: cumulative tokens, estimated cost, simulation counts. |
| `POST` | `/admin/seed-demo` | Admin | Re-seed the 25-participant benchmark cohort idempotently. |

### Participant Management
| Method | Endpoint | Auth | Description |
|---|---|:---:|---|
| `POST` | `/participants` | None | Ingest a new participant with LinkedIn/Instagram URLs and explicit consent. |
| `POST` | `/participants/import-manifest` | Admin | Batch ingest an authorized, pre-verified cohort manifest. |
| `GET` | `/participants` | None | List all participants with filtering (search, location, status) and pagination. |
| `GET` | `/participants/{id}` | None | Retrieve participant profile details, verification status, and provenance. |
| `DELETE` | `/participants/{id}` | Admin | Delete participant and cascade delete all associated sessions and rankings. |
| `POST` | `/participants/{id}/verify` | Admin | Update verification status (`source_verified`, `consent_verified`). |
| `POST` | `/participants/{id}/withdraw` | None | Withdraw consent; cancels active dates and bars future simulation eligibility. |
| `POST` | `/participants/{id}/analyze` | None | Trigger AI profile analyzer to extract evidence, hobbies, and inferences. |
| `GET` | `/participants/{id}/profile` | None | Fetch structured analyzed profile (explicit facts, inferences, unknowns). |
| `GET` | `/participants/{id}/evidence` | None | Fetch quote-level evidence records with confidence ratings and source URLs. |

### Dating Simulations & Replay
| Method | Endpoint | Auth | Description |
|---|---|:---:|---|
| `POST` | `/dates` | None | Initiate a dating session between two participants (`participant_a_id`, `participant_b_id`). |
| `GET` | `/dates` | None | List historical dating sessions with outcome summaries and metrics. |
| `GET` | `/dates/{session_id}` | None | Get dating session details, scorecards, and mutual engagement score. |
| `GET` | `/dates/{session_id}/messages` | None | Retrieve chronological conversation turns with decision factors. |
| `GET` | `/dates/{session_id}/events` | None | Server-Sent Events (SSE) stream for live turn-by-turn dialogue broadcast. |

### Compatibility Rankings
| Method | Endpoint | Auth | Description |
|---|---|:---:|---|
| `GET` | `/rankings/participants/{id}/rankings` | None | Get ranked match candidates for a participant with harmonic reciprocal scores. |
| `POST` | `/rankings/participants/{id}/rankings/recalculate` | None | Recalculate rankings on-demand using custom sub-score weights. |

### Batch Demonstration Runs
| Method | Endpoint | Auth | Description |
|---|---|:---:|---|
| `POST` | `/runs` | Admin | Trigger a batch demonstration run across cohort pairs. |
| `GET` | `/runs` | None | List demonstration runs and completion statuses. |
| `GET` | `/runs/{run_id}` | None | Retrieve run metadata, progress percentage, and pair counts. |
| `GET` | `/runs/{run_id}/progress` | None | Stream or poll real-time execution progress of a batch run. |
| `POST` | `/runs/{run_id}/resume` | Admin | Resume an interrupted or failed batch run. |

---

## 8. Batch Manifest Import for Real Consenting Cohorts

To onboard real, consenting cohorts without manual single-form entry, authenticate with your admin key and post a JSON manifest to `/api/v1/participants/import-manifest`:

```http
POST /api/v1/participants/import-manifest HTTP/1.1
Host: localhost:8000
Content-Type: application/json
X-Admin-Key: dev-admin-secret-change-in-prod

{
  "manifest_name": "Bengaluru Tech & Creative Cohort - Fall 2026",
  "participants": [
    {
      "name": "Jordan Rivera",
      "age": 29,
      "gender": "Female",
      "target_gender": "Male",
      "location": "San Francisco, CA",
      "linkedin_url": "https://www.linkedin.com/in/jordan-rivera-tech",
      "instagram_url": "https://www.instagram.com/jordan_rivera_sf",
      "consent_verified": true,
      "source_verified": true,
      "is_synthetic": false,
      "bio": "Product manager passionate about urban cycling and trail running.",
      "evidence": [
        {
          "source_type": "linkedin",
          "source_url": "https://www.linkedin.com/in/jordan-rivera-tech",
          "field_name": "career_focus",
          "raw_quote": "Lead PM scaling distributed data systems.",
          "confidence_score": 0.95
        },
        {
          "source_type": "instagram",
          "source_url": "https://www.instagram.com/jordan_rivera_sf",
          "field_name": "demonstrated_hobbies",
          "raw_quote": "Completed 100km coastal gravel bike brevet in Marin.",
          "confidence_score": 0.90
        }
      ]
    }
  ]
}
```

---

## 9. Repository Structure

```
datingSite/
├── .github/
│   └── workflows/
│       └── ci.yml                   # GitHub Actions: Alembic + 52 Pytests + Next.js build
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   │   └── e49d5916c3ae_0001_initial_schema.py # Complete database schema migration
│   │   ├── env.py                   # Alembic environment runner
│   │   └── script.py.mako           # Migration template
│   ├── app/
│   │   ├── adapters/                # Platform adapters (LinkedIn, Instagram, direct import)
│   │   ├── analysis/                # AI profile analyzer & evidence extractor
│   │   ├── api/v1/                  # FastAPI routers: admin, dates, participants, rankings, runs
│   │   ├── core/                    # Settings (config.py) and security/SSRF logic (security.py)
│   │   ├── dating/                  # Multi-turn coffee date state machine harness
│   │   ├── db/                      # SQLAlchemy models, session factory, 25-cohort seeder
│   │   ├── llm/                     # Groq, Gemini, and OfflineMock provider engine
│   │   ├── ranking/                 # Multi-component harmonic compatibility engine
│   │   ├── schemas/                 # Pydantic v2 validation models
│   │   └── main.py                  # FastAPI application entry point & lifespan handler
│   ├── scripts/
│   │   └── seed_demo_participants.py# CLI benchmark seeder
│   ├── tests/                       # 52 Automated Pytest test suites
│   ├── alembic.ini                  # Alembic migration configuration
│   ├── Dockerfile                   # Multi-stage production container
│   ├── pytest.ini                   # Pytest configuration
│   └── requirements.txt             # Python dependencies
├── frontend/
│   ├── src/app/
│   │   ├── page.tsx                 # Overview Dashboard (/)
│   │   ├── ingest/page.tsx          # Participant Ingestion (/ingest)
│   │   ├── participants/            # Directory (/participants) & Profile Detail (/[id])
│   │   ├── dates/                   # History (/dates), Live Date (/dates/live), Replay (/[id])
│   │   ├── rankings/page.tsx        # Compatibility Rankings (/rankings)
│   │   ├── demo/page.tsx            # 25-Participant Demo Showcase (/demo)
│   │   ├── admin/page.tsx           # Operations & Admin Dashboard (/admin)
│   │   └── layout.tsx               # Root layout & responsive navigation bar
│   ├── Dockerfile                   # Next.js standalone container
│   ├── package.json                 # Next.js 14, React 18, Tailwind, Lucide dependencies
│   ├── tailwind.config.js           # Tailwind theme configuration
│   ├── tsconfig.json                # TypeScript configuration
│   └── vercel.json                  # Vercel deployment blueprint
├── .env.example                     # Unified environment template
├── docker-compose.yml               # PostgreSQL + Backend + Frontend orchestration
├── render.yaml                      # Render Blueprint (Web service + Managed PostgreSQL)
├── start_all.ps1                    # Portable one-click PowerShell launch script
└── README.md                        # Documentation
```

---

## 10. Local Quickstart & Development

### Prerequisites
- **Python 3.11+**
- **Node.js 18+** & **npm**
- *(Optional)* **Docker & Docker Compose**

---

### Option A: Portable One-Click Launch (PowerShell)

On Windows, use the provided launcher script to spin up both the FastAPI backend and Next.js frontend in parallel:

```powershell
.\start_all.ps1
```

Once running:
- **Frontend Application**: `http://localhost:3000`
- **Backend API & Docs**: `http://localhost:8000/api/v1/docs`

---

### Option B: Docker Compose (Full-Stack + PostgreSQL)

Launch the complete containerized stack with a dedicated PostgreSQL database:

```bash
# 1. Build and start containers
docker compose up --build

# 2. To stop containers
docker compose down
```

**Services launched:**
- `auramatch-db`: PostgreSQL 15 on port `5432`
- `auramatch-backend`: FastAPI on `http://localhost:8000`
- `auramatch-frontend`: Next.js 14 on `http://localhost:3000`

---

### Option C: Manual Step-by-Step Setup

#### 1. Configure Environment Variables
Copy `.env.example` to the backend directory and configure your keys:

```bash
# In repository root
cp .env.example backend/.env
```

Edit `backend/.env` with your preferred settings:
```env
ENVIRONMENT=development
ADMIN_API_KEY=dev-admin-secret-key
DATABASE_URL=sqlite:///./dating.db
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=openai/gpt-oss-20b
```

#### 2. Backend Setup & Startup
```bash
cd backend

# Create and activate virtual environment
python -m venv .venv

# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start FastAPI server with live reloading
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 3. Frontend Setup & Startup
In a separate terminal:
```bash
cd frontend

# Install dependencies
npm install

# Start Next.js development server
npm run dev
```

Visit `http://localhost:3000` in your browser.

---

## 11. Database Schema & Alembic Migrations

AuraMatch AI uses **SQLAlchemy 2.0 ORM** with **Alembic** for reproducible database migrations across both SQLite and PostgreSQL.

```
                                  Database Entity Model
                                  
    ┌───────────────────────────┐         1:N         ┌───────────────────────────┐
    │       participants        │────────────────────►│      evidence_items       │
    └─────────────┬─────────────┘                     └───────────────────────────┘
                  │ 1:1
                  ▼
    ┌───────────────────────────┐
    │     analyzed_profiles     │
    └───────────────────────────┘
                  │
                  ▼
    ┌───────────────────────────┐         1:N         ┌───────────────────────────┐
    │      dating_sessions      │────────────────────►│   conversation_messages   │
    └─────────────┬─────────────┘                     └───────────────────────────┘
                  │ 1:N
                  ├──────────────────────────────────►┌───────────────────────────┐
                  ▼                                   │     agent_evaluations     │
    ┌───────────────────────────┐                     └───────────────────────────┘
    │  compatibility_rankings   │
    └───────────────────────────┘
```

### Key Migration Commands
```bash
cd backend

# Apply all migrations to head
alembic upgrade head

# Revert the latest migration
alembic downgrade -1

# Generate a new autodetected migration after editing models.py
alembic revision --autogenerate -m "describe_schema_change"

# View current migration version
alembic current
```

---

## 12. Automated Test Suite Verification (52 Tests)

The backend features an automated **52-test verification suite** covering API endpoints, provider fallbacks, mathematical ranking determinism, SSRF security, dating state machine flows, and demo seeder idempotency:

```bash
cd backend
.\.venv\Scripts\python -m pytest tests -v
```

### Test Suite Execution Output:
```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\rohit\Downloads\datingSite\backend
configfile: pytest.ini
collected 52 items

tests/test_api.py::test_health_endpoint PASSED                           [  1%]
tests/test_api.py::test_readiness_endpoint PASSED                        [  3%]
tests/test_api.py::test_list_participants PASSED                         [  5%]
tests/test_api.py::test_participant_evidence_traceability PASSED         [  7%]
tests/test_api.py::test_compatibility_rankings_deterministic PASSED      [  9%]
tests/test_api.py::test_ingest_duplicate_rejection PASSED                [ 11%]
tests/test_api.py::test_ingest_without_consent_rejection PASSED          [ 13%]
tests/test_dating_flow.py::test_full_dating_and_ranking_flow PASSED      [ 15%]
tests/test_dating_flow.py::test_incompatible_gender_date_rejected_with_400 PASSED [ 17%]
tests/test_gemini_provider.py::test_gemini_provider_requires_api_key PASSED [ 19%]
tests/test_gemini_provider.py::test_gemini_provider_model_name_normalization PASSED [ 21%]
tests/test_gemini_provider.py::test_gemini_successful_generation PASSED  [ 23%]
tests/test_gemini_provider.py::test_gemini_404_failover_without_retrying_same_model PASSED [ 25%]
tests/test_gemini_provider.py::test_gemini_transient_error_retries_with_backoff PASSED [ 26%]
tests/test_gemini_provider.py::test_gemini_all_candidates_exhausted_raises_actionable_error PASSED [ 28%]
tests/test_gemini_provider.py::test_gemini_dynamic_model_discovery_fallback PASSED [ 30%]
tests/test_gemini_provider.py::test_json_extraction_formats PASSED       [ 32%]
tests/test_groq_provider.py::test_groq_provider_requires_api_key PASSED  [ 34%]
tests/test_groq_provider.py::test_strict_groq_mode_raises_when_missing_key PASSED [ 36%]
tests/test_groq_provider.py::test_groq_successful_text_generation PASSED [ 38%]
tests/test_groq_provider.py::test_groq_404_failover_without_retrying_same_model PASSED [ 40%]
tests/test_groq_provider.py::test_groq_transient_error_retries_with_backoff PASSED [ 42%]
tests/test_groq_provider.py::test_groq_token_limit_error_skips_without_retry PASSED [ 44%]
tests/test_groq_provider.py::test_groq_quota_exhaustion_sanitizes_api_keys PASSED [ 46%]
tests/test_groq_provider.py::test_groq_dynamic_discovery_excludes_prompt_guard PASSED [ 48%]
tests/test_groq_provider.py::test_groq_alternating_multi_turn_dating_dialogue_and_persistence PASSED [ 50%]
tests/test_hardening_security.py::test_admin_auth_required_for_seed_demo PASSED [ 51%]
tests/test_hardening_security.py::test_admin_auth_bearer_token PASSED    [ 53%]
tests/test_hardening_security.py::test_delete_participant_requires_admin_auth PASSED [ 55%]
tests/test_hardening_security.py::test_synthetic_data_integrity_flagging PASSED [ 57%]
tests/test_manifest_import_real_participants PASSED                     [ 59%]
tests/test_hardening_security.py::test_strict_gemini_mode_raises_when_missing_key PASSED [ 61%]
tests/test_hardening_security.py::test_offline_mock_provider_explicit_reporting PASSED [ 63%]
tests/test_hardening_security.py::test_cors_preflight_and_headers PASSED [ 65%]
tests/test_hardening_security.py::test_participant_withdrawal_cascades PASSED [ 67%]
tests/test_hardening_security.py::test_withdrawn_participant_cannot_date PASSED [ 69%]
tests/test_hardening_security.py::test_production_admin_key_validation PASSED [ 71%]
tests/test_hardening_security.py::test_observability_metrics_truthfulness PASSED [ 73%]
tests/test_ranking.py::test_jaccard_overlap PASSED                       [ 75%]
tests/test_ranking.py::test_jaccard_overlap_empty PASSED                 [ 76%]
tests/test_ranking.py::test_harmonic_mean_reciprocity PASSED             [ 78%]
tests/test_security.py::test_linkedin_url_validation PASSED              [ 80%]
tests/test_security.py::test_instagram_url_validation PASSED             [ 82%]
tests/test_security.py::test_ssrf_protection PASSED                      [ 84%]
tests/test_security.py::test_sanitize_text PASSED                        [ 86%]
tests/test_seed_demo.py::test_seed_dataset_specification PASSED          [ 88%]
tests/test_seed_demo.py::test_seed_creates_exactly_25_synthetic_profiles_on_clean_db PASSED [ 90%]
tests/test_seed_demo.py::test_seed_idempotency_creates_no_duplicates PASSED [ 92%]
tests/test_seed_demo.py::test_seed_does_not_delete_or_overwrite_real_participants PASSED [ 94%]
tests/test_seed_demo.py::test_api_directory_listing_and_pagination PASSED [ 96%]
tests/test_seed_demo.py::test_api_search_by_name_and_location PASSED     [ 98%]
tests/test_seed_demo.py::test_lifespan_autoseeding_execution[asyncio] PASSED [100%]

======================= 52 passed in 11.97s =======================
```

### Module Breakdown:
- `tests/test_api.py` (7 tests): API routing, health probes, readiness checks, duplicate rejection, and consent enforcement.
- `tests/test_dating_flow.py` (2 tests): End-to-end multi-agent dating simulation, dialogue turn persistence, and gender compatibility guards.
- `tests/test_groq_provider.py` (9 tests): Groq API key enforcement, prompt-guard safety model filtering, transient backoff retries, and API key sanitization on quota errors.
- `tests/test_gemini_provider.py` (8 tests): Gemini dynamic model discovery fallback, 404 failovers, and JSON parsing robustness.
- `tests/test_hardening_security.py` (12 tests): Admin key timing-safe auth, Bearer tokens, CORS policies, participant withdrawal cascade deletions, and production key validation.
- `tests/test_ranking.py` (3 tests): Directional scoring math, Jaccard interest overlap, and harmonic reciprocal penalty validation.
- `tests/test_security.py` (4 tests): LinkedIn/Instagram URL syntax validation, handle extraction, SSRF IP blocking, and input sanitization.
- `tests/test_seed_demo.py` (7 tests): Exact 25-participant cohort creation, seeding idempotency, non-overwrite of real cohorts, and startup lifespan auto-seeding.

---

## 13. Continuous Integration (GitHub Actions)

The repository includes a production-grade CI pipeline configured in [`.github/workflows/ci.yml`](file:///c:/Users/rohit/Downloads/datingSite/.github/workflows/ci.yml):

```yaml
name: AuraMatch CI

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  backend-tests:
    name: Backend Test Suite & Migrations
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r backend/requirements.txt
      - run: alembic upgrade head
      - run: pytest tests/ -v
        env:
          LLM_PROVIDER: offline_mock

  frontend-build:
    name: Frontend Production Build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: cd frontend && npm ci
      - run: cd frontend && npm run build
        env:
          NEXT_PUBLIC_API_URL: http://localhost:8000/api/v1
```

---

## 14. Production Deployment Blueprint

### A. Deploy Backend & PostgreSQL on Render
The repository includes a ready-to-use [`render.yaml`](file:///c:/Users/rohit/Downloads/datingSite/render.yaml) blueprint:

1. Connect your GitHub repository in the **Render Dashboard**.
2. Select **New Blueprint Instance**.
3. Render automatically provisions:
   - `auramatch-backend`: Python 3.11 web service running `uvicorn app.main:app`.
   - `auramatch-postgres`: Managed PostgreSQL instance with connection pooling.
4. Set your production secrets in Render environment variables:
   - `ADMIN_API_KEY`: A cryptographically secure secret (minimum 32 characters).
   - `LLM_PROVIDER`: `groq` (or `gemini`).
   - `GROQ_API_KEY`: Your Groq Cloud API key.
   - `BACKEND_CORS_ORIGINS`: `["https://your-frontend.vercel.app"]`.

### B. Deploy Frontend on Vercel
The repository includes [`frontend/vercel.json`](file:///c:/Users/rohit/Downloads/datingSite/frontend/vercel.json):

1. Import the repository in **Vercel**.
2. Set the **Root Directory** to `frontend`.
3. Configure Environment Variables:
   - `NEXT_PUBLIC_API_URL`: `https://your-backend.onrender.com/api/v1` *(Trailing slashes are automatically sanitized by the frontend)*.
   - `NEXT_PUBLIC_ADMIN_KEY`: `<your-admin-secret>`
4. Click **Deploy**.

---

## 15. Technical Demonstration Storyboard (3-Minute Walkthrough)

| Timecode | Route / Screen | Technical Narrative & Focus |
|:---:|---|---|
| **0:00–0:25** | `/demo` Route | **Dataset Scale & Provenance**: Showcase the 25-participant cohort, verified profile links, dynamically calculated pair counts ($N(N-1)/2 = 300$ pairs), and explicit `SYNTHETIC BENCHMARK` tags vs. `VERIFIED RECORD` cohorts. |
| **0:25–0:55** | `/participants/[id]` | **Traceable Profile Evidence**: Open a participant profile. Highlight explicit facts, observed activities, calibrated probabilistic inferences with confidence percentages, explicit unknowns, and raw quote provenance cards. |
| **0:55–1:55** | `/dates/live` | **Genuine Autonomous Agent Dating**: Launch a live date between two agents. Observe alternating dialogue, dynamic topic pills, and expand the **"Inspect Decision Strategy"** drawer showing real decision factors. Inspect post-date evaluation scorecards. |
| **1:55–2:35** | `/rankings` | **Explainable Compatibility Engine**: Review ranked match candidates. Demonstrate why Candidate #1 outranks Candidate #2 using harmonic reciprocal scoring ($S_{\text{reciprocal}}$). Adjust weights live via the slider drawer to demonstrate dynamic re-ranking. |
| **2:35–3:00** | `/dates` & `/admin` | **Persistence & Operations**: Review session replay mode. Navigate to `/admin` to demonstrate admin key security, token tracking, system health probes, and database connection pooling. |

---

## 16. Troubleshooting & FAQ

### Q1: How do I run tests or develop without spending LLM API credits?
Set `LLM_PROVIDER=offline_mock` in your `.env`. The backend will use `OfflineMockProvider`, which generates realistic structured dates, evaluations, and profile analyses deterministically with zero network calls and zero cost.

### Q2: Why does the backend fail to start in production with an `ADMIN_API_KEY` error?
In `ENVIRONMENT=production`, the platform enforces timing-attack safe authentication and strictly prohibits default development keys (`dev-admin-secret-key`, `dev-admin-secret-change-in-prod`). Generate a strong secret:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
And assign it to `ADMIN_API_KEY` in your environment.

### Q3: Why does Next.js report network errors connecting to FastAPI?
Ensure `NEXT_PUBLIC_API_URL` points to `http://localhost:8000/api/v1` (or your Render URL) and that `BACKEND_CORS_ORIGINS` in the backend allows your frontend's origin (`http://localhost:3000` or your Vercel URL).

### Q4: How do I wipe and reset the demo dataset?
Authenticate with your admin key and trigger the seed endpoint:
```bash
curl -X POST http://localhost:8000/api/v1/admin/seed-demo \
  -H "X-Admin-Key: dev-admin-secret-change-in-prod"
```

---

<p align="center">
  Built with ❤️ for authentic, explainable, and privacy-respecting human connections.
</p>
