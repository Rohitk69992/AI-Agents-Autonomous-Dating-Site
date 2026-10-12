import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db.models import Participant, EvidenceItem, AnalyzedProfile
from app.db.seed_demo import seed_database, DEMO_PARTICIPANTS

def test_seed_dataset_specification():
    # Verify exactly 25 synthetic participant definitions
    assert len(DEMO_PARTICIPANTS) == 25
    ids = [p["id"] for p in DEMO_PARTICIPANTS]
    assert len(set(ids)) == 25, "All participant IDs must be unique"
    
    # Verify Indian locations and adult ages
    indian_cities = ["Bengaluru", "Mumbai", "Delhi", "Hyderabad", "Pune", "Chennai", "Kolkata"]
    for p in DEMO_PARTICIPANTS:
        assert 22 <= p["age"] <= 35, f"Age {p['age']} outside 22-35 range for {p['name']}"
        assert any(city in p["location"] for city in indian_cities), f"Location {p['location']} must be in an Indian city"
        assert p["linkedin_url"].startswith("https://www.linkedin.com/in/fictional-")
        assert p["instagram_url"].startswith("https://www.instagram.com/fictional_")
        assert len(p["evidence"]) >= 3
        assert "analyzed_profile" in p
        assert len(p["analyzed_profile"]["summary"]) > 20

def test_seed_creates_exactly_25_synthetic_profiles_on_clean_db():
    # Use isolated SQLite in-memory engine
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    TestSession = sessionmaker(bind=test_engine)
    db = TestSession()

    try:
        # Initial seed
        res = seed_database(db=db, run_simulation=False)
        assert res["created_participants"] == 25
        assert res["total_participants"] == 25

        # Query database directly
        all_parts = db.query(Participant).all()
        assert len(all_parts) == 25

        # Verify flags: honest synthetic reporting
        for p in all_parts:
            assert p.is_synthetic is True, f"{p.name} must be flagged as is_synthetic=True"
            assert p.consent_verified is False, "Synthetic profile cannot have consent_verified=True"
            assert p.source_verified is False, "Synthetic profile cannot have source_verified=True"
            assert p.simulation_eligible is True, "Synthetic demo profile must be simulation_eligible"
            assert p.analyzed_profile is not None
            assert len(p.evidence_items) >= 3
    finally:
        db.close()

def test_seed_idempotency_creates_no_duplicates():
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    TestSession = sessionmaker(bind=test_engine)
    db = TestSession()

    try:
        # First run
        res1 = seed_database(db=db, run_simulation=False)
        assert res1["created_participants"] == 25

        # Second run on same DB -> exactly 0 new records created
        res2 = seed_database(db=db, run_simulation=False)
        assert res2["created_participants"] == 0
        assert res2["existing_participants"] == 25
        assert res2["total_participants"] == 25

        total_in_db = db.query(Participant).count()
        assert total_in_db == 25, "Idempotent seeding must not duplicate records"
    finally:
        db.close()

def test_seed_does_not_delete_or_overwrite_real_participants():
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    TestSession = sessionmaker(bind=test_engine)
    db = TestSession()

    try:
        # Insert a real, verified consenting participant
        real_p = Participant(
            id="real-participant-uuid-001",
            name="Dr. Sunita Rao",
            age=32,
            gender="Female",
            target_gender="Male",
            location="Bengaluru, Karnataka",
            linkedin_url="https://www.linkedin.com/in/real-sunita-rao-unique",
            linkedin_handle="real-sunita-rao-unique",
            instagram_url="https://www.instagram.com/real_sunita_photos",
            instagram_handle="real_sunita_photos",
            consent_status="consented",
            consent_verified=True,
            source_verified=True,
            is_synthetic=False,
            simulation_eligible=True,
            status="analyzed",
            analysis_status="analyzed"
        )
        db.add(real_p)
        db.commit()

        # Run demo seeding
        res = seed_database(db=db, run_simulation=False)
        assert res["created_participants"] == 25

        # Verify real participant is completely untouched and preserved
        queried_real = db.query(Participant).filter(Participant.id == "real-participant-uuid-001").first()
        assert queried_real is not None
        assert queried_real.name == "Dr. Sunita Rao"
        assert queried_real.is_synthetic is False
        assert queried_real.consent_verified is True
        assert queried_real.source_verified is True

        # Total participants is 25 synthetic + 1 real = 26
        assert db.query(Participant).count() == 26
    finally:
        db.close()

def test_api_directory_listing_and_pagination(client):
    # GET /participants returns seeded profiles
    resp = client.get("/api/v1/participants?skip=0&limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 10
    first_p = data[0]
    assert "id" in first_p
    assert "name" in first_p
    assert "is_synthetic" in first_p
    assert "analyzed_profile" in first_p

    # Second page
    resp_page2 = client.get("/api/v1/participants?skip=10&limit=10")
    assert resp_page2.status_code == 200
    assert len(resp_page2.json()) == 10

def test_api_search_by_name_and_location(client):
    # Search by Indian name
    resp_name = client.get("/api/v1/participants?search=Aarav")
    assert resp_name.status_code == 200
    results = resp_name.json()
    assert len(results) >= 1
    assert any("Aarav Sharma" in p["name"] for p in results)

    # Search by Indian city
    resp_city = client.get("/api/v1/participants?search=Mumbai")
    assert resp_city.status_code == 200
    results_city = resp_city.json()
    assert len(results_city) >= 1
    assert all("Mumbai" in p["location"] for p in results_city)

    # Filter by status
    resp_status = client.get("/api/v1/participants?status_filter=analyzed")
    assert resp_status.status_code == 200
    assert len(resp_status.json()) >= 20
