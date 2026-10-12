import pytest
import uuid
from app.core.config import settings

def test_full_dating_and_ranking_flow(client):
    uid = uuid.uuid4().hex[:6]
    # 1. Ingest Participant Alpha
    resp_a = client.post("/api/v1/participants", json={
        "name": f"Sarah Connor {uid}",
        "age": 29,
        "gender": "Female",
        "target_gender": "Male",
        "location": "San Francisco, CA",
        "linkedin_url": f"https://www.linkedin.com/in/sarah-connor-{uid}",
        "instagram_url": f"https://www.instagram.com/sarah_runs_{uid}",
        "consent_confirmed": True
    })
    assert resp_a.status_code == 201
    part_a = resp_a.json()
    assert part_a["id"] is not None
    assert part_a["simulation_eligible"] is False
    assert part_a["consent_status"] == "declared"

    # 2. Ingest Participant Beta
    resp_b = client.post("/api/v1/participants", json={
        "name": f"Kyle Reese {uid}",
        "age": 31,
        "gender": "Male",
        "target_gender": "Female",
        "location": "San Francisco, CA",
        "linkedin_url": f"https://www.linkedin.com/in/kyle-reese-{uid}",
        "instagram_url": f"https://www.instagram.com/kyle_survival_{uid}",
        "consent_confirmed": True
    })
    assert resp_b.status_code == 201
    part_b = resp_b.json()
    assert part_b["id"] is not None
    assert part_b["simulation_eligible"] is False

    # 3. Verify Profiles are Analyzed
    prof_a = client.get(f"/api/v1/participants/{part_a['id']}/profile")
    assert prof_a.status_code == 200
    assert "summary" in prof_a.json()

    # 4. Attempt date before verification -> must be rejected with 400
    unverified_date = client.post("/api/v1/dates", json={
        "participant_a_id": part_a["id"],
        "participant_b_id": part_b["id"],
        "max_turns": 4
    })
    assert unverified_date.status_code == 400
    assert "eligible" in unverified_date.json()["detail"].lower()

    # Admin verifies consent & eligibility for both participants
    verify_a = client.post(
        f"/api/v1/participants/{part_a['id']}/verify",
        headers={"X-Admin-Key": settings.ADMIN_API_KEY}
    )
    assert verify_a.status_code == 200
    assert verify_a.json()["simulation_eligible"] is True

    verify_b = client.post(
        f"/api/v1/participants/{part_b['id']}/verify",
        headers={"X-Admin-Key": settings.ADMIN_API_KEY}
    )
    assert verify_b.status_code == 200
    assert verify_b.json()["simulation_eligible"] is True

    # 5. Execute Dating Session Between Them
    date_resp = client.post("/api/v1/dates", json={
        "participant_a_id": part_a["id"],
        "participant_b_id": part_b["id"],
        "max_turns": 4
    })
    assert date_resp.status_code == 201
    date_data = date_resp.json()
    assert date_data["status"] in ("completed", "incompatible")
    assert len(date_data["messages"]) == 4
    assert len(date_data["evaluations"]) == 2
    assert date_data["outcome_status"] is not None
    assert date_data["outcome_summary"] is not None

    # Check privacy: internal thought MUST be redacted (None) in public API response
    for msg in date_data["messages"]:
        assert len(msg["content"]) > 0
        assert msg["internal_thought"] is None

    # 6. Verify Rankings Reflect the Persisted Date
    rankings_resp = client.get(f"/api/v1/participants/{part_a['id']}/rankings")
    assert rankings_resp.status_code == 200
    rankings_data = rankings_resp.json()
    target_ids = [r["target_participant_id"] for r in rankings_data["rankings"]]
    assert part_b["id"] in target_ids

def test_incompatible_gender_date_rejected_with_400(client):
    uid = uuid.uuid4().hex[:6]
    # Ingest two female participants who both state target_gender = Male
    resp_1 = client.post("/api/v1/participants", json={
        "name": f"Shreya {uid}",
        "age": 27,
        "gender": "Female",
        "target_gender": "Male",
        "location": "Mumbai",
        "linkedin_url": f"https://www.linkedin.com/in/shreya-{uid}",
        "instagram_url": f"https://www.instagram.com/shreya_{uid}",
        "consent_confirmed": True
    })
    part_1 = resp_1.json()

    resp_2 = client.post("/api/v1/participants", json={
        "name": f"Priya {uid}",
        "age": 26,
        "gender": "Female",
        "target_gender": "Male",
        "location": "Bengaluru",
        "linkedin_url": f"https://www.linkedin.com/in/priya-{uid}",
        "instagram_url": f"https://www.instagram.com/priya_{uid}",
        "consent_confirmed": True
    })
    part_2 = resp_2.json()

    # Admin verifies both
    for pid in [part_1["id"], part_2["id"]]:
        client.post(f"/api/v1/participants/{pid}/verify", headers={"X-Admin-Key": settings.ADMIN_API_KEY})

    # Attempt to pair them -> must return 400 with Gender preference mismatch, preventing 0-turn zombie session
    date_resp = client.post("/api/v1/dates", json={
        "participant_a_id": part_1["id"],
        "participant_b_id": part_2["id"],
        "max_turns": 4
    })
    assert date_resp.status_code == 400
    assert "gender preference mismatch" in date_resp.json()["detail"].lower()

