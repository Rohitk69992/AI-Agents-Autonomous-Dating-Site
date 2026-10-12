# AuraMatch AI — Production-Ready Agentic Dating Platform

> **200-Character Overview:**
> Autonomous multi-agent dating platform where AI agents date on behalf of consenting users using LinkedIn & Instagram profile evidence to produce explainable rankings.

---

## 1. Executive Summary & Core Mission

AuraMatch AI is a full-stack, production-grade agentic dating platform where:
1. **Each participant is represented by an autonomous AI agent.**
2. **Profiles originate strictly from verified public LinkedIn and Instagram profiles**, subject to explicit authorization and consent.
3. **Information extracted is partitioned into**:
   - Explicit facts (direct quotes with URL attribution)
   - Observed public professional & hobby signals
   - Model-generated probabilistic inferences with numerical confidence (0.0–1.0)
   - Unknown and insufficiently supported characteristics (preventing hallucinations)
4. **Autonomous agents participate in genuine, multi-turn coffee dates** across an observable state machine. Agents probe mutual compatibility, ask authentic questions, discover common ground or friction, and independently record post-date scorecards.
5. **Compatibility is calculated through explainable multi-component mathematics** (preference alignment, shared interests, lifestyle fit, date interaction engagement, and values), with directional scores and harmonic reciprocal scores—never arbitrary black-box percentages.
6. **A permanent demonstration route (`/demo`)** loads a 25-participant consenting benchmark with 300 possible pairs, persisted transcripts, and complete ranking coverage that survives deployment restarts.

---

## 2. Technical Architecture & Data Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Next.js 14 Frontend UI                          │
│  - 9 Routes: Dashboard, Ingest, Directory, Profile Analysis,           │
│    Live Simulation, History, Rankings, 25-Participant Demo, Operations │
│  - SSE Streaming for real-time agent turn updates                      │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │ HTTP / SSE REST API
┌───────────────────────────────────▼────────────────────────────────────┐
│                         FastAPI Python Backend                         │
│  - SSRF-safe URL validation & normalization                            │
│  - Data Acquisition Adapters (LinkedIn, Instagram, Direct Import)      │
│  - Profile Analyzer (Strict non-inference of sensitive data)          │
│  - Agent Dating Harness (Observable state machine with thought traces) │
│  - Compatibility Engine (Directional & harmonic reciprocal math)       │
│  - Durable Background Job Queue & Metrics Observability                │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │
            ┌───────────────────────┴───────────────────────┐
            ▼                                               ▼
┌───────────────────────────────┐               ┌───────────────────────────────┐
│     Persistence Layer         │               │      LLM Provider Engine      │
│  - SQLAlchemy 2.0 ORM         │               │  - Google Gemini API          │
│  - SQLite (Zero-config dev)   │               │    (gemini-2.5-flash)         │
│  - PostgreSQL (Production)    │               │  - Deterministic Offline Mode │
└───────────────────────────────┘               └───────────────────────────────┘
```

---

## 3. The 9 Product Pages

| Page | Route | Description |
|---|---|---|
| **1. Overview Dashboard** | `/` | Persisted statistics: participants, analyzed count, pairs, sessions, completion %, and cost/latency metrics. |
| **2. Participant Ingestion** | `/ingest` | Real-time URL validation, SSRF protection, duplicate detection, and authorized batch JSON import. |
| **3. Participant Directory** | `/participants` | Searchable directory with source links, demographic badges, and consent records. |
| **4. Profile Analysis** | `/participants/[id]` | Supported hobbies, career focus, inferences with confidence, unknowns, and quote-level evidence traceability. |
| **5. Live Dating Simulation** | `/dates/live` | Interactive pair dating with alternating dialogue, observable agent internal reasoning, and post-date evaluations. |
| **6. Session History** | `/dates` | Persisted session ledger with tokens, costs, latency, and replay mode (`REPLAY MODE` badge). |
| **7. Compatibility Rankings** | `/rankings` | Ordered candidates, score breakdowns (Preferences, Interests, Lifestyle, Date Flow, Confidence), and configurable weights drawer. |
| **8. Completed Demonstration** | `/demo` | Permanent showcase of the 25-consenting-participant benchmark run, 300 possible pairs, and transcripts. |
| **9. Operations & Admin** | `/admin` | LLM configuration status, token/cost tracking, health probes, background queue manager, and demo re-seeder. |

---

## 4. Multi-Component Mathematical Ranking Methodology

Unlike simple LLM similarity guessing, compatibility is calculated deterministically:

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
Because attraction is not symmetric, the reciprocal score uses the harmonic mean, severely penalizing one-sided matches:
$$S_{\text{reciprocal}}(A, B) = \frac{2 \cdot S(A \to B) \cdot S(B \to A)}{S(A \to B) + S(B \to A) + \epsilon}$$

### C. Deterministic Tie-Breaking
1. `reciprocal_score` (Descending)
2. `confidence_score` (Descending, based on verified evidence count)
3. `individual_score` (Descending)
4. `target_participant_id` (Ascending lexicographical sort)

---

## 5. Security, Privacy & Integrity Protections

- **SSRF Defense:** External URLs submitted during ingestion are validated via strict hostname resolution preventing private IP / cloud metadata access (`127.0.0.0/8`, `169.254.0.0/16`, `10.0.0.0/8`, etc.).
- **Strict Non-Inference Rules:** The profile analyzer strictly forbids guessing sensitive personal attributes (religion, political beliefs, financial wealth, health conditions, or physical appearance). Unstated attributes are explicitly classified as `unknowns`.
- **Untrusted Input Isolation:** Profile content is treated strictly as data payloads and never as system prompt instructions.
- **Credential Hygiene:** API keys are server-side only; zero secrets or tokens are exposed to frontend bundles or client logs.
- **Right to be Forgotten:** Deleting a participant permanently cascades across evidence items, sessions, and rankings.

---

## 6. Local Quickstart

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm

### Automated Launch (PowerShell)
```powershell
.\start_all.ps1
```

### Manual Launch

#### 1. Backend Setup
```bash
cd backend
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
cp ../.env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be live at `http://localhost:8000/api/v1/docs`.

#### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Website interface will be live at `http://localhost:3000`.

---

## 7. Testing Suite Execution

The application includes unit, integration, and end-to-end dating simulation tests:
```bash
cd backend
.\.venv\Scripts\pytest -v
```
**Test Coverage Includes:**
- `test_security.py`: LinkedIn & Instagram URL regex, handle extraction, SSRF blocks, input sanitization.
- `test_ranking.py`: Jaccard overlap, harmonic mean reciprocity penalty, empty input edge cases.
- `test_api.py`: FastAPI endpoints, health checks, participant CRUD, duplicate URL 409 rejection, consent verification 400 rejection.
- `test_dating_flow.py`: Full end-to-end integration test (ingestion $\to$ analysis $\to$ 4-turn dating simulation with thought bubbles $\to$ independent evaluations $\to$ updated rankings).

---

## 8. Three-Minute Technical Video Storyboard

| Timecode | Visual / Screen | Narrative & Focus |
|---|---|---|
| **0:00–0:25** | `/demo` Route | **The 25-Participant Consenting Dataset:** Showcase the 25 participants, each with both official LinkedIn and Instagram URLs. Highlight mutual consent status and 300 candidate pairs matrix. |
| **0:25–0:55** | `/participants/[id]` | **Traceable Profile Analysis:** Open Elena Rostova's profile. Show explicit hobbies (trail running, sourdough), career focus, calibrated inferences (85% confidence), and explicit unknowns. Point out raw quote provenance. |
| **0:55–1:55** | `/dates/live` | **Genuine Agent-to-Agent Dating:** Simulate a date between Elena and Marcus. Reveal the alternating turns, highlighted topics/questions, and expand the **Agent Internal Reasoning** thought bubble. Show independent post-date scorecards. |
| **1:55–2:35** | `/rankings` | **Explainable Compatibility Engine:** Inspect Elena's ranked candidates. Show why Candidate #1 outranks Candidate #2 (harmonic reciprocal score, engagement in date, lifestyle fit). Demonstrate the live scoring weights adjustment drawer. |
| **2:35–3:00** | `/dates` & `/admin` | **Persistence & Operations:** Navigate to Session History in Replay Mode. Open Operations dashboard showing token usage, estimated cost, and server health. Demonstrate persistence across page reloads. |

---

## 9. Deployment Guidelines

- **Frontend:** Deployable on Vercel or any Next.js Node container with `NEXT_PUBLIC_API_URL` pointing to backend.
- **Backend:** Deployable on Render, Railway, AWS ECS, or Fly.io using `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- **Database:** Connect managed PostgreSQL by setting `DATABASE_URL=postgresql://user:pass@host:5432/dbname`.
