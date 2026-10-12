import datetime
import json
import logging
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.db.models import (
    Participant, EvidenceItem, AnalyzedProfile, DemonstrationRun,
    EligibleCandidatePair, DatingSession
)
from app.core.security import validate_and_normalize_linkedin_url, validate_and_normalize_instagram_url
from app.analysis.analyzer import analyze_participant_profile
from app.dating.harness import execute_dating_session
from app.ranking.engine import calculate_rankings_for_participant

logger = logging.getLogger(__name__)

# Official 25-participant consenting demonstration dataset
DEMO_PARTICIPANTS = [
    {
        "id": "part-demo-01",
        "name": "Elena Rostova",
        "age": 28,
        "gender": "Female",
        "target_gender": "Male",
        "location": "San Francisco, CA",
        "linkedin_url": "https://www.linkedin.com/in/elena-rostova-ai",
        "instagram_url": "https://www.instagram.com/elena_explores",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Lead Research Engineer at Frontier AI Lab focusing on multimodal agent architectures.", "confidence": 1.0},
            {"platform": "linkedin", "category": "interest", "type": "explicit_statement", "quote": "Passionate about open-source research and ethical autonomous agent benchmarks.", "confidence": 0.95},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Weekend trail runner in Marin Headlands. Training for Big Sur Marathon.", "confidence": 0.9},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Filter coffee purist, sourdough experimenter, and alpine camper.", "confidence": 0.95}
        ]
    },
    {
        "id": "part-demo-02",
        "name": "Marcus Vance",
        "age": 31,
        "gender": "Male",
        "target_gender": "Female",
        "location": "San Francisco, CA",
        "linkedin_url": "https://www.linkedin.com/in/marcus-vance-design",
        "instagram_url": "https://www.instagram.com/marcusvance_studio",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Principal Product Designer crafting developer tools and generative design workflows.", "confidence": 1.0},
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Mentoring early-stage founders on interface accessibility and ergonomic typography.", "confidence": 0.9},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Ceramics wheel throwing and architectural photography around the Bay Area.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Early mornings, pour-over rituals, and jazz vinyl enthusiast.", "confidence": 0.9}
        ]
    },
    {
        "id": "part-demo-03",
        "name": "Sophia Chen",
        "age": 27,
        "gender": "Female",
        "target_gender": "Male",
        "location": "Oakland, CA",
        "linkedin_url": "https://www.linkedin.com/in/sophia-chen-biotech",
        "instagram_url": "https://www.instagram.com/sophia.c.climbs",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Computational Biologist designing synthetic enzymes for renewable materials.", "confidence": 1.0},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Bouldering V6 in Bishop and Yosemite granite crack climbing.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Plant mom with 40+ tropical varieties, avid sci-fi reader, and tea collector.", "confidence": 0.9}
        ]
    },
    {
        "id": "part-demo-04",
        "name": "Liam Gallagher",
        "age": 30,
        "gender": "Male",
        "target_gender": "Female",
        "location": "Berkeley, CA",
        "linkedin_url": "https://www.linkedin.com/in/liam-gallagher-climate",
        "instagram_url": "https://www.instagram.com/liam.on.trails",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Climate Tech Director working on grid optimization and decentralized battery storage.", "confidence": 1.0},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Ultralight backpacking in the High Sierras and gravel biking along coastal ridges.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Zero-waste cooking, acoustic guitar in the evenings, and dog dad to a golden retriever.", "confidence": 0.95}
        ]
    },
    {
        "id": "part-demo-05",
        "name": "Amina Diallo",
        "age": 29,
        "gender": "Female",
        "target_gender": "Male",
        "location": "San Francisco, CA",
        "linkedin_url": "https://www.linkedin.com/in/amina-diallo-health",
        "instagram_url": "https://www.instagram.com/amina.diallo_art",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Global Health Epidemiologist analyzing preventable disease response mechanisms.", "confidence": 1.0},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Watercolor landscape painting and contemporary African literature book club host.", "confidence": 0.9},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Speaks three languages fluently; passionate about farmers markets and fermentation.", "confidence": 0.9}
        ]
    },
    {
        "id": "part-demo-06",
        "name": "Kaito Tanaka",
        "age": 32,
        "gender": "Male",
        "target_gender": "Female",
        "location": "San Jose, CA",
        "linkedin_url": "https://www.linkedin.com/in/kaito-tanaka-robotics",
        "instagram_url": "https://www.instagram.com/kaito_takes_photos",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Autonomous Robotics Hardware Engineer building quadruped search-and-rescue systems.", "confidence": 1.0},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Analog 35mm street photography and Japanese woodblock printmaking.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Minimalist home aesthetic, matcha enthusiast, and road cyclist.", "confidence": 0.9}
        ]
    },
    {
        "id": "part-demo-07",
        "name": "Zara Patel",
        "age": 26,
        "gender": "Female",
        "target_gender": "Male",
        "location": "Palo Alto, CA",
        "linkedin_url": "https://www.linkedin.com/in/zara-patel-fintech",
        "instagram_url": "https://www.instagram.com/zarapatel_runs",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Fintech Risk Analyst automating real-time fraud mitigation with graph models.", "confidence": 1.0},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Half-marathon runner and competitive salsa & bachata dancer.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Spice fanatic, board games strategist, and weekend road trip explorer.", "confidence": 0.9}
        ]
    },
    {
        "id": "part-demo-08",
        "name": "Julian Morales",
        "age": 33,
        "gender": "Male",
        "target_gender": "Female",
        "location": "San Francisco, CA",
        "linkedin_url": "https://www.linkedin.com/in/julian-morales-chef",
        "instagram_url": "https://www.instagram.com/julian_cooks_sf",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Culinary Operations Director & Farm-to-Table Hospitality Consultant.", "confidence": 1.0},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Foraging wild mushrooms in Sonoma County and dry-curing artisan charcuterie.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Natural wine champion, Spanish guitar player, and warm conversationalist.", "confidence": 0.95}
        ]
    },
    {
        "id": "part-demo-09",
        "name": "Chloe Dupont",
        "age": 31,
        "gender": "Female",
        "target_gender": "Male",
        "location": "San Francisco, CA",
        "linkedin_url": "https://www.linkedin.com/in/chloe-dupont-arch",
        "instagram_url": "https://www.instagram.com/chloe_dupont_spaces",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Sustainable Architect specializing in mass timber urban housing.", "confidence": 1.0},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Urban sketching, kayaking on Tomales Bay, and sculling.", "confidence": 0.9},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "French pastry baking on Sunday mornings, quiet book lover, mindful living.", "confidence": 0.95}
        ]
    },
    {
        "id": "part-demo-10",
        "name": "David Okafor",
        "age": 29,
        "gender": "Male",
        "target_gender": "Female",
        "location": "Oakland, CA",
        "linkedin_url": "https://www.linkedin.com/in/david-okafor-edtech",
        "instagram_url": "https://www.instagram.com/david_moves_code",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "VP of Engineering at non-profit EdTech platform bridging STEM education in underserved communities.", "confidence": 1.0},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Triathlete, basketball recreational league captain, and podcast host.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "High-energy optimist, vinyl hip-hop collector, and passionate youth mentor.", "confidence": 0.9}
        ]
    },
    {
        "id": "part-demo-11",
        "name": "Maya Lindqvist",
        "age": 27,
        "gender": "Female",
        "target_gender": "Male",
        "location": "San Francisco, CA",
        "linkedin_url": "https://www.linkedin.com/in/maya-lindqvist-data",
        "instagram_url": "https://www.instagram.com/maya_in_nature",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Data Journalist & Investigative Visualizer examining environmental policies.", "confidence": 1.0},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Wilderness survival trekker, botanical illustrator, and scuba diver.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Nordic sauna enthusiast, cold plunge advocate, and thoughtful conversationalist.", "confidence": 0.9}
        ]
    },
    {
        "id": "part-demo-12",
        "name": "Gabriel Santos",
        "age": 34,
        "gender": "Male",
        "target_gender": "Female",
        "location": "San Mateo, CA",
        "linkedin_url": "https://www.linkedin.com/in/gabriel-santos-neuro",
        "instagram_url": "https://www.instagram.com/gabriel_neuro_art",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Cognitive Neuroscientist researching human-agent interaction and attention dynamics.", "confidence": 1.0},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Classical piano (Chopin nocturnes) and high-altitude trekking in the Andes.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Deep thinker, espresso connoisseur, values emotional maturity and empathy.", "confidence": 0.95}
        ]
    },
    {
        "id": "part-demo-13",
        "name": "Rachel Kim",
        "age": 28,
        "gender": "Female",
        "target_gender": "Male",
        "location": "Sunnyvale, CA",
        "linkedin_url": "https://www.linkedin.com/in/rachel-kim-uxr",
        "instagram_url": "https://www.instagram.com/rachel_pottery_life",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Staff UX Researcher exploring neurodiverse accessibility in software platforms.", "confidence": 1.0},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Stoneware pottery artist and specialty coffee roaster.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Bilingual Korean-English, indie cinema fanatic, warm and curious conversational style.", "confidence": 0.9}
        ]
    },
    {
        "id": "part-demo-14",
        "name": "Tariq Mansoor",
        "age": 32,
        "gender": "Male",
        "target_gender": "Female",
        "location": "San Francisco, CA",
        "linkedin_url": "https://www.linkedin.com/in/tariq-mansoor-security",
        "instagram_url": "https://www.instagram.com/tariq_runs_sf",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Cybersecurity Principal Architect specializing in zero-trust cryptographic protocols.", "confidence": 1.0},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Marathoner and woodworker crafting bespoke walnut desks.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Calm, disciplined, values integrity and deep philosophical late-night debates.", "confidence": 0.9}
        ]
    },
    {
        "id": "part-demo-15",
        "name": "Ingrid Berg",
        "age": 30,
        "gender": "Female",
        "target_gender": "Male",
        "location": "Berkeley, CA",
        "linkedin_url": "https://www.linkedin.com/in/ingrid-berg-ocean",
        "instagram_url": "https://www.instagram.com/ingrid_ocean_waves",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Marine Ecologist studying coral resilience and kelp forest restoration.", "confidence": 1.0},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Surfing Ocean Beach at dawn, freediving, and wildlife cinematography.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Sun-chaser, ocean lover, loves hearty campfire cooking and folk music.", "confidence": 0.95}
        ]
    },
    {
        "id": "part-demo-16",
        "name": "Naveen Rao",
        "age": 29,
        "gender": "Male",
        "target_gender": "Female",
        "location": "Fremont, CA",
        "linkedin_url": "https://www.linkedin.com/in/naveen-rao-autonomy",
        "instagram_url": "https://www.instagram.com/naveen_astrophoto",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Perception Systems Lead for autonomous electric vehicles.", "confidence": 1.0},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Deep-sky astrophotography with custom telescope rigs in Death Valley.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Stargazer, board games strategist (Terraforming Mars), and spicy ramen seeker.", "confidence": 0.9}
        ]
    },
    {
        "id": "part-demo-17",
        "name": "Clara Vestergaard",
        "age": 28,
        "gender": "Female",
        "target_gender": "Male",
        "location": "San Francisco, CA",
        "linkedin_url": "https://www.linkedin.com/in/clara-vestergaard-law",
        "instagram_url": "https://www.instagram.com/clara_in_the_city",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Human Rights and Technology Policy Attorney at international civil liberties NGO.", "confidence": 1.0},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Modern dance performance, museum gallery hopping, and tennis player.", "confidence": 0.9},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Sharp wit, cosmopolitan worldview, enjoys lively dinner parties with rich dialogue.", "confidence": 0.95}
        ]
    },
    {
        "id": "part-demo-18",
        "name": "Mateo Rossi",
        "age": 31,
        "gender": "Male",
        "target_gender": "Female",
        "location": "San Francisco, CA",
        "linkedin_url": "https://www.linkedin.com/in/mateo-rossi-aerospace",
        "instagram_url": "https://www.instagram.com/mateo_flies_high",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Propulsion Engineer designing reusable rocket stages for orbital smallsats.", "confidence": 1.0},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Private pilot license holder, cross-country flights over Tahoe, and rock climber.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Adventurous spirit, values humor and resilience under pressure.", "confidence": 0.9}
        ]
    },
    {
        "id": "part-demo-19",
        "name": "Ananya Sharma",
        "age": 27,
        "gender": "Female",
        "target_gender": "Male",
        "location": "Mountain View, CA",
        "linkedin_url": "https://www.linkedin.com/in/ananya-sharma-ml",
        "instagram_url": "https://www.instagram.com/ananya_creates",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Machine Learning Engineer optimizing on-device diffusion models.", "confidence": 1.0},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Classical Indian Carnatic vocal music and baking sourdough pastries.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Warm family values, bookworm, tea lover, and weekend museum visitor.", "confidence": 0.9}
        ]
    },
    {
        "id": "part-demo-20",
        "name": "Elijah Washington",
        "age": 33,
        "gender": "Male",
        "target_gender": "Female",
        "location": "Oakland, CA",
        "linkedin_url": "https://www.linkedin.com/in/elijah-washington-urban",
        "instagram_url": "https://www.instagram.com/elijah_builds_community",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Urban Planning Consultant championing transit-oriented walkable neighborhoods.", "confidence": 1.0},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Jazz saxophonist performing in local Oakland lounges; road cycling enthusiast.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Charismatic community organizer, deep conversationalist, lover of soul food.", "confidence": 0.95}
        ]
    },
    {
        "id": "part-demo-21",
        "name": "Camila Fernandez",
        "age": 29,
        "gender": "Female",
        "target_gender": "Male",
        "location": "San Francisco, CA",
        "linkedin_url": "https://www.linkedin.com/in/camila-fernandez-clean",
        "instagram_url": "https://www.instagram.com/camila_on_earth",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Clean Energy Investment Associate financing utility-scale solar and storage projects.", "confidence": 1.0},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Scuba diving in kelp forests, landscape watercolors, and vintage thrifting.", "confidence": 0.9},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Values environmental sustainability, empathy, spontaneity, and lively Latin music.", "confidence": 0.95}
        ]
    },
    {
        "id": "part-demo-22",
        "name": "Siddharth Menon",
        "age": 30,
        "gender": "Male",
        "target_gender": "Female",
        "location": "San Francisco, CA",
        "linkedin_url": "https://www.linkedin.com/in/siddharth-menon-systems",
        "instagram_url": "https://www.instagram.com/sid_climbs_rocks",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Staff Distributed Systems Engineer scaling low-latency event-driven microservices.", "confidence": 1.0},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Rock climbing outdoors, sourdough artisan, and film photography.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Calm demeanor, curious mind, loyal partner, loves craft beer tastings.", "confidence": 0.9}
        ]
    },
    {
        "id": "part-demo-23",
        "name": "Hannah Novak",
        "age": 32,
        "gender": "Female",
        "target_gender": "Male",
        "location": "Palo Alto, CA",
        "linkedin_url": "https://www.linkedin.com/in/hannah-novak-genomics",
        "instagram_url": "https://www.instagram.com/hannah_outside_life",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Bioinformatics Director deciphering rare genomic variants for targeted oncology therapies.", "confidence": 1.0},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Equestrian jumping, backcountry skiing in Lake Tahoe, and botanical gardening.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Intelligent, composed, animal lover, seeks an ambitious and compassionate partner.", "confidence": 0.95}
        ]
    },
    {
        "id": "part-demo-24",
        "name": "Andre Dubois",
        "age": 35,
        "gender": "Male",
        "target_gender": "Female",
        "location": "San Francisco, CA",
        "linkedin_url": "https://www.linkedin.com/in/andre-dubois-film",
        "instagram_url": "https://www.instagram.com/andre_cinematics",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Documentary Film Producer exploring human stories at the frontier of science and ethics.", "confidence": 1.0},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "35mm black-and-white darkroom printing, sea kayaking, and motorcycle road trips.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Deep listener, emotionally grounded, passionate about art and storytelling.", "confidence": 0.95}
        ]
    },
    {
        "id": "part-demo-25",
        "name": "Linnea Larsson",
        "age": 28,
        "gender": "Female",
        "target_gender": "Male",
        "location": "San Francisco, CA",
        "linkedin_url": "https://www.linkedin.com/in/linnea-larsson-nordic",
        "instagram_url": "https://www.instagram.com/linnea_wanders",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Industrial Designer specializing in circular economy consumer electronics and biodegradable packaging.", "confidence": 1.0},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Cross-country skiing, pottery throwing, and Nordic minimalist interior design.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Values simplicity, hygge cozy evenings, nature connection, and deep honesty.", "confidence": 0.95}
        ]
    }
]

def seed_database(db: Session = None, run_simulation: bool = True):
    should_close = False
    if db is None:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        should_close = True

    try:
        logger.info(f"Seeding {len(DEMO_PARTICIPANTS)} consenting demonstration participants...")
        
        participant_objs = []
        for pdata in DEMO_PARTICIPANTS:
            # Check if participant already exists by linkedin_url
            p = db.query(Participant).filter(Participant.linkedin_url == pdata["linkedin_url"]).first()
            if not p:
                _, norm_li, li_handle = validate_and_normalize_linkedin_url(pdata["linkedin_url"])
                _, norm_ig, ig_handle = validate_and_normalize_instagram_url(pdata["instagram_url"])
                p = Participant(
                    id=pdata["id"],
                    name=pdata["name"],
                    age=pdata["age"],
                    gender=pdata["gender"],
                    target_gender=pdata["target_gender"],
                    location=pdata["location"],
                    linkedin_url=norm_li,
                    linkedin_handle=li_handle,
                    instagram_url=norm_ig,
                    instagram_handle=ig_handle,
                    consent_status="consented",
                    consent_timestamp=datetime.datetime.utcnow(),
                    consent_verified=False,
                    source_verified=False,
                    is_synthetic=True,
                    simulation_eligible=True,
                    status="pending",
                    analysis_status="analyzed"
                )
                db.add(p)
                db.commit()
                db.refresh(p)

                # Add evidence items
                for ev in pdata.get("evidence", []):
                    item = EvidenceItem(
                        participant_id=p.id,
                        source_platform=ev["platform"],
                        source_url=p.linkedin_url if ev["platform"] == "linkedin" else p.instagram_url,
                        category=ev["category"],
                        evidence_type=ev["type"],
                        raw_quote=ev["quote"],
                        confidence=ev.get("confidence", 1.0),
                        is_synthetic=True,
                        processing_version="1.0.0",
                        retrieved_at=datetime.datetime.utcnow()
                    )
                    db.add(item)
                db.commit()

            # Analyze profile if not analyzed
            if not p.analyzed_profile:
                analyze_participant_profile(db, p.id)

            participant_objs.append(p)

        logger.info(f"Successfully processed {len(participant_objs)} participants.")

        # Initialize synthetic benchmark demonstration run
        run_id = "demo-run-25-participants"
        demo_run = db.query(DemonstrationRun).filter(DemonstrationRun.id == run_id).first()
        if not demo_run:
            demo_run = DemonstrationRun(
                id=run_id,
                name="Synthetic Benchmark & Development Fixture Run (25 Fixtures)",
                status="pending",
                total_participants=len(participant_objs),
                started_at=datetime.datetime.utcnow()
            )
            db.add(demo_run)
            db.commit()
            db.refresh(demo_run)

        # Generate eligible candidate pairs
        pair_records = []
        for i in range(len(participant_objs)):
            for j in range(i + 1, len(participant_objs)):
                p_a = participant_objs[i]
                p_b = participant_objs[j]
                
                # Check gender compatibility
                eligible = True
                inelig_reason = None
                if p_a.target_gender and p_b.gender and p_a.target_gender != p_b.gender and p_a.target_gender != "Any":
                    eligible = False
                    inelig_reason = "Gender preference mismatch"
                elif p_b.target_gender and p_a.gender and p_b.target_gender != p_a.gender and p_b.target_gender != "Any":
                    eligible = False
                    inelig_reason = "Gender preference mismatch"

                pair = db.query(EligibleCandidatePair).filter(
                    EligibleCandidatePair.run_id == run_id,
                    EligibleCandidatePair.participant_a_id == p_a.id,
                    EligibleCandidatePair.participant_b_id == p_b.id
                ).first()

                if not pair:
                    pair = EligibleCandidatePair(
                        run_id=run_id,
                        participant_a_id=p_a.id,
                        participant_b_id=p_b.id,
                        is_eligible=eligible,
                        is_synthetic=True,
                        ineligibility_reason=inelig_reason,
                        pair_status="pending" if eligible else "skipped"
                    )
                    db.add(pair)
                pair_records.append(pair)
        db.commit()

        demo_run.total_eligible_pairs = sum(1 for p in pair_records if p.is_eligible)
        db.commit()

        if run_simulation:
            logger.info("Executing representative dating sessions and calculating persistent rankings...")
            # Simulate eligible pairs for key participants so full rankings are populated
            simulated_count = 0
            eligible_pairs = [p for p in pair_records if p.is_eligible]

            # Execute simulation for first batch of eligible pairs (e.g. 20 pairs)
            for pair in eligible_pairs[:20]:
                if pair.pair_status != "completed":
                    session = DatingSession(
                        run_id=run_id,
                        participant_a_id=pair.participant_a_id,
                        participant_b_id=pair.participant_b_id,
                        is_synthetic=True,
                        status="initialized"
                    )
                    db.add(session)
                    db.commit()
                    db.refresh(session)
                    pair.session_id = session.id
                    try:
                        execute_dating_session(db, session.id, max_turns=4)
                        pair.pair_status = "completed"
                        simulated_count += 1
                    except Exception as e:
                        logger.error(f"Failed dating session for pair {pair.id}: {e}")
                        pair.pair_status = "failed"
                    db.commit()

            # Calculate explainable rankings for all 25 participants
            for p in participant_objs:
                calculate_rankings_for_participant(db, p.id, run_id=run_id)

            demo_run.status = "completed"
            demo_run.completed_at = datetime.datetime.utcnow()
            demo_run.simulated_pairs = simulated_count
            demo_run.completed_sessions = simulated_count
            demo_run.execution_summary = {
                "total_participants": len(participant_objs),
                "total_eligible_pairs": demo_run.total_eligible_pairs,
                "simulated_sessions": simulated_count,
                "rankings_generated": True,
                "policy": "Representative Consenting Demonstration Benchmark"
            }
            db.commit()
            logger.info(f"Demonstration run {run_id} completed successfully.")

    finally:
        if should_close:
            db.close()

if __name__ == "__main__":
    seed_database(run_simulation=True)
