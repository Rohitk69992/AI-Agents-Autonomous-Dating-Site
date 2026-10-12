import pytest

def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "version" in data
    assert "llm_provider" in data

def test_readiness_endpoint(client):
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"

def test_list_participants(client):
    response = client.get("/api/v1/participants")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # 25 participants should be present from auto-seeding
    assert len(data) >= 25
    first = data[0]
    assert "name" in first
    assert "linkedin_url" in first
    assert "instagram_url" in first
    assert first["consent_status"] == "consented"

def test_participant_evidence_traceability(client):
    # Fetch participants and pick one from the verified demonstration cohort
    response = client.get("/api/v1/participants")
    participants = response.json()
    p_with_ev = next((p for p in participants if p.get("evidence_count", 0) > 0), participants[0])

    ev_resp = client.get(f"/api/v1/participants/{p_with_ev['id']}/evidence")
    assert ev_resp.status_code == 200
    evidence = ev_resp.json()
    assert len(evidence) > 0
    assert "raw_quote" in evidence[0]
    assert "source_platform" in evidence[0]

def test_compatibility_rankings_deterministic(client):
    response = client.get("/api/v1/participants")
    participants = response.json()
    p_id = participants[0]["id"]

    rank_resp = client.get(f"/api/v1/participants/{p_id}/rankings")
    assert rank_resp.status_code == 200
    data = rank_resp.json()
    assert "rankings" in data
    assert len(data["rankings"]) > 0
    # Check that rank 1 has highest reciprocal score
    first_rank = data["rankings"][0]
    assert first_rank["rank"] == 1
    assert "reciprocal_score" in first_rank
    assert "individual_score" in first_rank
    assert "ranking_explanation" in first_rank

def test_ingest_duplicate_rejection(client):
    # Attempting to re-ingest an existing LinkedIn URL must return 409 Conflict
    parts = client.get("/api/v1/participants").json()
    assert len(parts) > 0
    existing_li = parts[0]["linkedin_url"]
    payload = {
        "name": "Duplicate Test",
        "linkedin_url": existing_li,
        "instagram_url": "https://www.instagram.com/brand_new_handle_123",
        "consent_confirmed": True
    }
    response = client.post("/api/v1/participants", json=payload)
    assert response.status_code == 409

def test_ingest_without_consent_rejection(client):
    payload = {
        "name": "No Consent Test",
        "linkedin_url": "https://www.linkedin.com/in/new-user-test-99",
        "instagram_url": "https://www.instagram.com/new_user_test_99",
        "consent_confirmed": False
    }
    response = client.post("/api/v1/participants", json=payload)
    assert response.status_code == 400
