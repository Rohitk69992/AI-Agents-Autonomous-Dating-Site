# AuraMatch AI — Production-Ready Agentic Dating Platform

> **200-Character Overview:**
> Autonomous multi-agent dating platform where AI agents date on behalf of consenting users using LinkedIn & Instagram profile evidence to produce explainable rankings.

---

## 1. Executive Summary & Core Mission

AuraMatch AI is a full-stack, production-grade agentic dating platform where:
1. **Each participant is represented by an autonomous AI agent.**
2. **Profiles originate strictly from verified public LinkedIn and Instagram profiles**, subject to explicit authorization and consent.
3. **Information extracted is strictly partitioned into**:
   - **Explicit facts**: Direct statements with source URL attribution.
   - **Observed public signals**: Professional roles, demonstrated activities, and creative projects.
   - **Model-generated inferences**: Calibrated probabilistic interpretations with numerical confidence scores (0.0–1.0).
   - **Unknown / Insufficiently supported characteristics**: Explicitly tracked to prevent hallucination.
4. **Autonomous agents participate in genuine, multi-turn coffee dates** across an observable state machine. Agents probe mutual compatibility, ask authentic questions, discover common ground or friction, and independently record post-date scorecards.
5. **Compatibility is calculated through explainable multi-component mathematics** (preference alignment, shared interests, lifestyle fit, date interaction engagement, and values), with directional scores and harmonic reciprocal scores—never arbitrary black-box percentages.
6. **Strict separation of synthetic development fixtures vs. verified consenting cohorts**: Synthetic records are transparently tagged with `is_synthetic=True` and badged across all UI views and API payloads.
7. **Production deployment ready**: Dockerized multi-stage containers, Docker Compose orchestration, PostgreSQL connection pooling, timing-attack safe admin authentication, and automated Render/Vercel blueprints.

---

## 2. Technical Architecture & Data Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Next.js 14 Frontend UI                          │
│  - 9 Routes: Dashboard, Ingest, Directory, Profile Analysis,           │
│    Live Simulation, History, Rankings, 25-Participant Demo, Operations │
│  - Provenance badges (SYNTHETIC BENCHMARK vs. VERIFIED RECORD)         │
│  - Sanitized Observable Decision Strategy viewer                       │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │ HTTP REST API (X-Admin-Key Auth)
┌───────────────────────────────────▼────────────────────────────────────┐
│                         FastAPI Python Backend                         │
│  - Timing-Safe Admin Authentication (X-Admin-Key / Bearer Token)       │
│  - SSRF-safe URL validation & normalization (Private IP blocks)        │
│  - Strict Data Provenance Adapters (LinkedIn, Instagram, Manifest)     │
│  - Profile Analyzer (Strict non-inference of sensitive data)          │
│  - Agent Dating Harness (Observable state machine & decision factors)  │
│  - Compatibility Engine (Directional & harmonic reciprocal math)       │
│  - Resilient Error Masking with UUID correlation IDs                   │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │
            ┌───────────────────────┴───────────────────────┐
            ▼                                               ▼
┌───────────────────────────────┐               ┌───────────────────────────────┐
│     Persistence Layer         │               │      LLM Provider Engine      │
│  - SQLAlchemy 2.0 ORM         │               │  - Google Gemini API          │
│  - PostgreSQL Pool (Prod)     │               │    (gemini-2.5-flash)         │
│  - SQLite (Dev / Isolated QA) │               │  - OfflineMockProvider        │
│  - Cascade Foreign Keys       │               │    (Zero-credential harness)  │
└───────────────────────────────┘               └───────────────────────────────┘
```

---

## 3. Product Pages & Route Matrix

| Page | Route | Description |
|---|---|---|
| **1. Overview Dashboard** | `/` | Persisted statistics: participants, analyzed count, dynamically calculated theoretical pairs ($N(N-1)/2$), sessions, completion %, and cost/latency metrics. |
| **2. Participant Ingestion** | `/ingest` | Real-time URL validation, SSRF protection, duplicate detection, and authorized cohort manifest import. |
| **3. Participant Directory** | `/participants` | Searchable directory with source links, demographic badges, consent status, and `SYNTHETIC` vs `VERIFIED` indicators. |
| **4. Profile Analysis** | `/participants/[id]` | Supported hobbies, career focus, inferences with confidence, unknowns, quote-level evidence traceability, and admin deletion. |
| **5. Live Dating Simulation** | `/dates/live` | Interactive pair dating with alternating dialogue, observable decision strategies, topic pills, and post-date evaluations. |
| **6. Session History** | `/dates` | Persisted session ledger with tokens, costs, latency, provenance tags, and replay mode (`REPLAY MODE` badge). |
| **7. Compatibility Rankings** | `/rankings` | Ordered candidates, score breakdowns (Preferences, Interests, Lifestyle, Date Flow, Confidence), and configurable weights drawer. |
| **8. Completed Demonstration** | `/demo` | Permanent showcase of the 25-participant benchmark run, dynamically computed pairs, transcripts, and ranking coverage. |
| **9. Operations & Admin** | `/admin` | LLM configuration status, token/cost tracking, health probes, queue manager, and admin-authenticated re-seeder. |

---

## 4. Multi-Component Mathematical Ranking Methodology

Compatibility is calculated deterministically across multi-factor dimensions:

### A. Directional Score $S(A \to B) \in [0, 100]$
Measures how well Candidate $B$ satisfies Participant $A$'s profile and interaction history:
$$S(A \to B) = w_{\text{pref}} S_{\text{pref}} + w_{\text{int}} S_{\text{int}} + w_{\text{life}} S_{\text{life}} + w_{\text{eng}} S_{\text{eng}} + w_{\text{val}} S_{\text{val}}$$

- $S_{\text{pref}}$: Overlap between $A$'s relationship preferences and $B$'s verified attributes.
- $S_{\text{int}}$: Jaccard and semantic similarity of demonstrated hobbies and interests:
  $$\text{Overlap} = \frac{|H_A \cap H_B| + |I_A \cap I_B|}{\max(|H_A \cup H_B|, 1)}$$
- $S_{\text{life}}$: Lifestyle pace and daily rhythm alignment.
- $S_{\text{eng}}$: Derived from actual dating session evaluation:
  $$S_{\text{eng}} = (0.4 \cdot \text{Chemistry} + 0.4 \cdot \text{Comfort} + 0.2 \cdot \text{WouldDateAgain}) \times 10$$
- $S_{\text{val}}$: Shared values and communication priorities ($1-10 \times 10$).

### B. Harmonized Reciprocal Score $S_{\text{reciprocal}}(A, B)$
Attraction is directional; reciprocal chemistry requires mutual balance. The reciprocal score uses the harmonic mean, penalizing one-sided matches:
$$S_{\text{reciprocal}}(A, B) = \frac{2 \cdot S(A \to B) \cdot S(B \to A)}{S(A \to B) + S(B \to A) + \epsilon}$$

### C. Deterministic Tie-Breaking
1. `reciprocal_score` (Descending)
2. `confidence_score` (Descending, based on verified evidence count)
3. `individual_score` (Descending)
4. `target_participant_id` (Ascending lexicographical sort)

---

## 5. Security & Architecture Audit Resolutions

| Severity | Category | Identified Defect | Resolution & Hardening Implemented |
|---|---|---|---|
| **P0** | **Access Control** | Destructive endpoints (`DELETE /participants/{id}`, `POST /runs`, `POST /admin/seed-demo`) were unauthenticated. | Implemented timing-attack safe `require_admin_auth` dependency checking `X-Admin-Key` and `Authorization: Bearer <key>`. |
| **P0** | **CORS & Secrets** | Wildcard `allow_origins=["*"]` permitted arbitrary web origin calls; raw database exceptions leaked internal details. | Restricted CORS via `BACKEND_CORS_ORIGINS` config and added global exception handler with masked UUID `correlation_id`. |
| **P1** | **Data Integrity** | Seed fixtures claimed to be verified without tracking synthetic status; pair counts were hardcoded to 300. | Added `is_synthetic`, `source_verified`, `consent_verified` flags across models, schemas, and UI; dynamically compute $N(N-1)/2$. |
| **P1** | **Database & Startup** | Heavy seeding blocked FastAPI startup lifespan; SQLite lacked connection pooling for PostgreSQL. | Removed heavy seed from startup; added PostgreSQL connection pooling (`pool_size=10, max_overflow=20, pool_pre_ping=True`). |
| **P2** | **AI Provider Integrity** | `DeterministicProvider` masked missing Gemini keys and masqueraded as live Gemini. | Renamed to `OfflineMockProvider` reporting `provider="offline_mock"`; strict `GeminiLLMProvider` raises explicit runtime errors on credential absence. |
| **P2** | **Privacy & UI** | Raw chain-of-thought leaked internal prompt scaffolding into UI. | Structured agent turns with `decision_summary` and `decision_factors`; updated UI with "Inspect Decision Strategy" drawer. |
| **P3** | **Production Readiness** | Missing Dockerfiles, container orchestration, Render/Vercel configs, and portable scripts. | Added multi-stage `Dockerfile` (backend & frontend), `docker-compose.yml`, `render.yaml`, `vercel.json`, and portable `start_all.ps1`. |

---

## 6. Manifest Import for Consenting Real Cohorts

To ingest authorized, consenting participants into the platform without manual single-form entry, use the authenticated batch manifest API:

```http
POST /api/v1/participants/import-manifest HTTP/1.1
Host: localhost:8000
Content-Type: application/json
X-Admin-Key: dev-admin-secret-change-in-prod

{
  "manifest_name": "Autumn 2026 Consenting Cohort",
  "participants": [
    {
      "name": "Jordan Rivera",
      "age": 29,
      "gender": "Female",
      "location": "San Francisco, CA",
      "linkedin_url": "https://linkedin.com/in/jordan-rivera-tech",
      "instagram_url": "https://instagram.com/jordan_rivera_sf",
      "consent_verified": true,
      "source_verified": true,
      "is_synthetic": false,
      "bio": "Product manager passionate about urban cycling and trail running.",
      "evidence": [
        {
          "source_type": "linkedin",
          "source_url": "https://linkedin.com/in/jordan-rivera-tech",
          "field_name": "career_focus",
          "raw_quote": "Lead PM scaling distributed data systems.",
          "confidence_score": 0.95
        }
      ]
    }
  ]
}
```

---

## 7. Local Quickstart & Development

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- Docker & Docker Compose (Optional, for containerized run)

### Option A: Portable Launch Script (PowerShell)
```powershell
.\start_all.ps1
```

### Option B: Docker Compose (Full Stack + PostgreSQL)
```bash
docker compose up --build
```
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000/api/v1`
- Swagger Docs: `http://localhost:8000/api/v1/docs`

### Option C: Manual Local Setup

#### 1. Backend Setup
```bash
cd backend
python -m venv .venv

# Windows
.\.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
cp ../.env.example .env

# Set LLM_PROVIDER=offline_mock for zero-credential offline testing
# Or set LLM_PROVIDER=gemini and provide GEMINI_API_KEY for live AI
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 8. Test Suite Verification

The backend includes a comprehensive 23-test suite covering security, authentication, SSRF protection, mathematical rankings, API contracts, synthetic flags, and full-loop dating simulations:

```bash
cd backend
.\.venv\Scripts\pytest tests -v
```

### Test Suite Modules:
- `tests/test_hardening_security.py`: Admin API key authentication, Bearer auth, CORS policies, synthetic flag enforcement, batch manifest import, and strict Gemini exception handling.
- `tests/test_security.py`: URL syntax validation (LinkedIn & Instagram), handle extraction, SSRF IP blocking, and untrusted input sanitization.
- `tests/test_ranking.py`: Directional scoring, Jaccard hobby/interest overlap, harmonic reciprocal mean penalty, and tie-breaking determinism.
- `tests/test_api.py`: FastAPI routes, health probe, duplicate URL rejection (409 Conflict), and consent requirements.
- `tests/test_dating_flow.py`: Full multi-agent dating simulation harness, alternating conversation turns, independent post-date evaluation scorecards, and ranking updates.

---

## 9. Production Deployment Guide

### A. Backend on Render.com
The repository includes a ready-to-use [`render.yaml`](./render.yaml) blueprint:
1. Connect this GitHub repository in Render.
2. Select **New Blueprint Instance**.
3. Render automatically provisions the `auramatch-backend` Python service and a managed `auramatch-postgres` database.
4. Set the secret `GEMINI_API_KEY` in the Render environment variables dashboard.

### B. Frontend on Vercel
The repository includes [`frontend/vercel.json`](./frontend/vercel.json):
1. Import the repository in Vercel.
2. Set Root Directory to `frontend`.
3. Add Environment Variable:
   - `NEXT_PUBLIC_API_URL`: `https://your-backend.onrender.com/api/v1`
   - `NEXT_PUBLIC_ADMIN_KEY`: `<your-admin-secret>`
4. Deploy!

---

## 10. Technical Evaluation Storyboard (3-Minute Video)

| Timecode | Screen / Route | Technical Narrative & Focus |
|---|---|---|
| **0:00–0:25** | `/demo` Route | **Dataset Provenance & Scale:** Showcase the 25 participants, both official URLs, dynamic pair counting ($N(N-1)/2 = 300$ pairs), and explicit synthetic fixture tags vs. verified cohorts. |
| **0:25–0:55** | `/participants/[id]` | **Traceable Profile Analysis:** Open participant profile. Display explicit facts, observed professional signals, calibrated probabilistic inferences with confidence %, explicit unknowns, and raw quote provenance. |
| **0:55–1:55** | `/dates/live` | **Genuine Agent-to-Agent Dating:** Execute a live date between two autonomous agents. Demonstrate alternating multi-turn dialogue, question/topic extraction, and expand the **Inspect Decision Strategy** drawer showing real decision factors. Show independent post-date evaluation scorecards. |
| **1:55–2:35** | `/rankings` | **Explainable Compatibility Engine:** Inspect ranked matches. Explain why Candidate #1 outranks Candidate #2 using harmonic reciprocal scoring, engagement, and lifestyle alignment. Demonstrate live weight customization. |
| **2:35–3:00** | `/dates` & `/admin` | **Persistence & Infrastructure:** Demonstrate session replay mode. Open `/admin` showing admin key authentication, token tracking, system health, and database connection status. |
