import pytest
from app.core.config import settings
from app.llm.provider import get_llm_provider, OfflineMockProvider, GeminiLLMProvider

def test_admin_auth_required_for_seed_demo(client):
    # Without admin key -> 401 Unauthorized
    resp = client.post("/api/v1/admin/seed-demo")
    assert resp.status_code == 401
    assert "admin authentication required" in resp.json()["detail"].lower()

    # With invalid admin key -> 403 Forbidden
    resp = client.post("/api/v1/admin/seed-demo", headers={"X-Admin-Key": "wrong-key"})
    assert resp.status_code == 403
    assert "invalid admin credentials" in resp.json()["detail"].lower()

    # With valid admin key -> 200 OK
    resp = client.post("/api/v1/admin/seed-demo", headers={"X-Admin-Key": settings.ADMIN_API_KEY})
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"

def test_admin_auth_bearer_token(client):
    # Authorization: Bearer <key> syntax supported
    resp = client.post(
        "/api/v1/admin/config",
        headers={"Authorization": f"Bearer {settings.ADMIN_API_KEY}"},
        json={"max_turns": 8}
    )
    assert resp.status_code == 200
    assert resp.json()["max_turns"] == 8

def test_delete_participant_requires_admin_auth(client):
    # First get a participant
    list_resp = client.get("/api/v1/participants")
    participants = list_resp.json()
    assert len(participants) > 0
    p_id = participants[0]["id"]

    # Delete without admin key -> 401
    del_resp = client.delete(f"/api/v1/participants/{p_id}")
    assert del_resp.status_code == 401

    # Delete with invalid key -> 403
    del_resp = client.delete(f"/api/v1/participants/{p_id}", headers={"X-Admin-Key": "bad-key"})
    assert del_resp.status_code == 403

def test_synthetic_data_integrity_flagging(client):
    # Ensure seeded participants are accurately flagged as synthetic
    resp = client.get("/api/v1/participants")
    assert resp.status_code == 200
    participants = resp.json()
    synthetic_count = sum(1 for p in participants if p.get("is_synthetic") is True)
    assert synthetic_count >= 20, "Seed demonstration records must be explicitly flagged as synthetic fixtures"

    # Evidence items must also have is_synthetic set
    first_p = participants[0]
    ev_resp = client.get(f"/api/v1/participants/{first_p['id']}/evidence")
    assert ev_resp.status_code == 200
    evidence = ev_resp.json()
    assert all(e["is_synthetic"] is True for e in evidence)

def test_manifest_import_real_participants(client):
    # Import a verified real manifest participant
    payload = {
        "manifest_id": "verified-real-manifest-test",
        "run_immediate_analysis": True,
        "participants": [
            {
                "name": "Jordan Taylor",
                "age": 29,
                "gender": "Non-binary",
                "target_gender": "Any",
                "location": "Seattle, WA",
                "linkedin_url": "https://www.linkedin.com/in/jordan-taylor-real",
                "instagram_url": "https://www.instagram.com/jordan_real_photos",
                "consent_verified": True,
                "source_verified": True,
                "evidence": [
                    {
                        "platform": "linkedin",
                        "category": "professional",
                        "type": "explicit_statement",
                        "quote": "Robotics perception researcher working on spatial AI.",
                        "confidence": 1.0
                    },
                    {
                        "platform": "instagram",
                        "category": "hobby",
                        "type": "observed_activity",
                        "quote": "Kayaking Puget Sound and film photography.",
                        "confidence": 0.95
                    }
                ]
            }
        ]
    }

    # Without admin key -> 401
    resp = client.post("/api/v1/participants/import-manifest", json=payload)
    assert resp.status_code == 401

    # With admin key -> 200
    resp = client.post(
        "/api/v1/participants/import-manifest",
        json=payload,
        headers={"X-Admin-Key": settings.ADMIN_API_KEY}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["imported_count"] == 1
    assert len(data["imported_participant_ids"]) == 1

    # Verify the imported record is NOT synthetic and has verified consent
    p_id = data["imported_participant_ids"][0]
    p_resp = client.get(f"/api/v1/participants/{p_id}")
    assert p_resp.status_code == 200
    p_data = p_resp.json()
    assert p_data["is_synthetic"] is False
    assert p_data["consent_verified"] is True
    assert p_data["source_verified"] is True

def test_strict_gemini_mode_raises_when_missing_key(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    with pytest.raises(RuntimeError) as exc_info:
        get_llm_provider()
    assert "LLM_PROVIDER is configured as 'gemini', but no GEMINI_API_KEY" in str(exc_info.value)

def test_offline_mock_provider_explicit_reporting(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "offline_mock")
    provider = get_llm_provider()
    assert isinstance(provider, OfflineMockProvider)
    resp = provider.generate("Profile Analysis", "Analyze this test prompt")
    assert resp.provider == "offline_mock"
    assert resp.structured_data is not None

def test_cors_preflight_and_headers(client):
    # Origin from allowed list
    resp = client.get("/", headers={"Origin": "http://localhost:3000"})
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert resp.headers.get("access-control-allow-credentials") == "true"
