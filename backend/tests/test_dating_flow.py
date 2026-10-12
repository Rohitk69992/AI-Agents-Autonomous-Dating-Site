import pytest
import uuid

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

    # 3. Verify Profiles are Analyzed
    prof_a = client.get(f"/api/v1/participants/{part_a['id']}/profile")
    assert prof_a.status_code == 200
    assert "summary" in prof_a.json()

    # 4. Execute a Real Dating Session Between Them
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

    # Check that messages have internal thought and spoken content
    for msg in date_data["messages"]:
        assert len(msg["content"]) > 0
        assert msg["internal_thought"] is not None

    # 5. Verify Rankings Reflect the Persisted Date
    rankings_resp = client.get(f"/api/v1/participants/{part_a['id']}/rankings")
    assert rankings_resp.status_code == 200
    rankings_data = rankings_resp.json()
    target_ids = [r["target_participant_id"] for r in rankings_data["rankings"]]
    assert part_b["id"] in target_ids
