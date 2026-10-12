import datetime
import json
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.db.models import (
    Participant, EvidenceItem, AnalyzedProfile, DemonstrationRun,
    EligibleCandidatePair, DatingSession
)
from app.core.security import validate_and_normalize_linkedin_url, validate_and_normalize_instagram_url
from app.dating.harness import execute_dating_session
from app.ranking.engine import calculate_rankings_for_participant

logger = logging.getLogger(__name__)

# Exactly 25 realistic, fully synthetic development fixtures with diverse Indian urban demographics
DEMO_PARTICIPANTS: List[Dict[str, Any]] = [
    {
        "id": "part-demo-01",
        "name": "Aarav Sharma",
        "age": 28,
        "gender": "Male",
        "target_gender": "Female",
        "location": "Bengaluru, Karnataka",
        "linkedin_url": "https://www.linkedin.com/in/fictional-aarav-sharma-tech",
        "instagram_url": "https://www.instagram.com/fictional_aarav_wanderlust",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Lead AI Systems Architect at an autonomous robotics laboratory in Indiranagar.", "confidence": 1.0},
            {"platform": "linkedin", "category": "interest", "type": "explicit_statement", "quote": "Fascinated by neural-symbolic reasoning, open-source AI benchmarks, and ethical autonomous agents.", "confidence": 0.95},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Weekend trail gravel cycling in Turahalli Forest and amateur astrophotography in Coorg.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Specialty pour-over coffee enthusiast, sourdough baker, and mindful morning meditator.", "confidence": 0.9}
        ],
        "analyzed_profile": {
            "summary": "Deep-thinking robotics systems architect based in Bengaluru who pairs cutting-edge technological inquiry with outdoor cycling, artisanal coffee rituals, and mindful living.",
            "career_interests": ["Autonomous Robotics", "Neural-Symbolic AI", "Open Source Engineering"],
            "demonstrated_hobbies": ["Trail Gravel Cycling", "Astrophotography", "Sourdough Baking"],
            "stated_interests": ["Space Exploration", "Science Fiction", "Specialty Pour-over Coffee"],
            "lifestyle_preferences": ["Early morning cyclist", "Mindful minimalist", "Cozy weekend home cook"],
            "communication_preferences": ["Thoughtful and reflective", "Intellectually curious listener", "Authentic and direct"],
            "relationship_preferences": ["Emotionally grounded partner", "Values deep conversations and shared outdoor adventures"],
            "explicit_facts": ["Professional AI systems architect in Bengaluru", "Active outdoor cyclist and astrophotographer"],
            "inferences_with_confidence": [
                {"claim": "Appreciates peaceful nature escapes over crowded nightlife", "confidence": 0.9, "basis": "Weekend cycling in Turahalli and stargazing trips to Coorg"},
                {"claim": "Methodical, patient problem solver", "confidence": 0.85, "basis": "Robotics architecture combined with artisanal coffee and baking pursuits"}
            ],
            "uncertainties_and_unknowns": ["Long-term international relocation preferences"]
        }
    },
    {
        "id": "part-demo-02",
        "name": "Ananya Iyer",
        "age": 26,
        "gender": "Female",
        "target_gender": "Male",
        "location": "Bengaluru, Karnataka",
        "linkedin_url": "https://www.linkedin.com/in/fictional-ananya-iyer-design",
        "instagram_url": "https://www.instagram.com/fictional_ananya_creates",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Senior UX Architect specializing in assistive technologies and accessible design systems.", "confidence": 1.0},
            {"platform": "linkedin", "category": "interest", "type": "explicit_statement", "quote": "Advocate for ethical product design, human dignity in tech, and neuroinclusive interfaces.", "confidence": 0.95},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Carnatic classical violin practice, Sunday watercolor plein-air sketching in Cubbon Park.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "South Indian filter coffee purist, botanical houseplant parent, loves cozy monsoon reading.", "confidence": 0.95}
        ],
        "analyzed_profile": {
            "summary": "Creative and empathetic design architect from Bengaluru dedicated to accessible interfaces, classical Carnatic violin, and tranquil nature sketching.",
            "career_interests": ["Assistive Technology", "Neuroinclusive UX Design", "Design Systems"],
            "demonstrated_hobbies": ["Carnatic Classical Violin", "Watercolor Plein-Air Sketching", "Ceramics"],
            "stated_interests": ["Typography", "Indian Classical Music", "Sustainable Architecture"],
            "lifestyle_preferences": ["Filter coffee ritual", "Plant enthusiast", "Appreciates quiet monsoon evenings"],
            "communication_preferences": ["Empathetic and perceptive", "Expressive with warm humor", "Active listener"],
            "relationship_preferences": ["Equal creative partnership", "Mutual respect, emotional depth, and humor"],
            "explicit_facts": ["Senior UX architect with accessibility focus", "Practicing Carnatic violinist"],
            "inferences_with_confidence": [
                {"claim": "Values cultural roots alongside modern design sensibilities", "confidence": 0.92, "basis": "Blends classical Carnatic violin with cutting-edge tech design"},
                {"claim": "Warm, detail-oriented collaborator", "confidence": 0.88, "basis": "Human-first accessibility work and watercolor practice"}
            ],
            "uncertainties_and_unknowns": ["Willingness to relocate outside South India"]
        }
    },
    {
        "id": "part-demo-03",
        "name": "Rohan Verma",
        "age": 30,
        "gender": "Male",
        "target_gender": "Female",
        "location": "Mumbai, Maharashtra",
        "linkedin_url": "https://www.linkedin.com/in/fictional-rohan-verma-fin",
        "instagram_url": "https://www.instagram.com/fictional_rohan_strides",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Quantitative Risk Researcher modeling systemic financial volatility at Bandra Kurla Complex.", "confidence": 1.0},
            {"platform": "linkedin", "category": "interest", "type": "explicit_statement", "quote": "Interested in algorithmic game theory, behavioral economics, and open financial data pipelines.", "confidence": 0.95},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Dawn half-marathon training along Marine Drive, vinyl jazz enthusiast.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Disciplined daily runner, sourdough pizza experimenter, loves hosting dinner parties.", "confidence": 0.9}
        ],
        "analyzed_profile": {
            "summary": "Analytically sharp quantitative researcher in Mumbai who pairs intense intellectual curiosity in economics with long-distance running, vintage jazz, and culinary dinner hosting.",
            "career_interests": ["Quantitative Finance", "Algorithmic Game Theory", "Behavioral Economics"],
            "demonstrated_hobbies": ["Marathon Running", "Vinyl Jazz Collecting", "Artisanal Pizza Making"],
            "stated_interests": ["Urban Architecture", "Economic History", "Street Photography"],
            "lifestyle_preferences": ["Early morning runner along Marine Drive", "Social dinner host", "Disciplined weekday schedule"],
            "communication_preferences": ["Articulate and witty", "Enjoys sharp intellectual banter", "Direct and candid"],
            "relationship_preferences": ["Intellectually driven companion", "Values ambition, loyalty, and lively banter"],
            "explicit_facts": ["Works in quantitative finance in Mumbai BKC", "Active half-marathon runner"],
            "inferences_with_confidence": [
                {"claim": "Thrives on structured routines and high-performance habits", "confidence": 0.9, "basis": "Quantitative research combined with rigorous distance training"}
            ],
            "uncertainties_and_unknowns": ["Weekend availability during peak financial quarter-ends"]
        }
    },
    {
        "id": "part-demo-04",
        "name": "Priya Patel",
        "age": 27,
        "gender": "Female",
        "target_gender": "Male",
        "location": "Mumbai, Maharashtra",
        "linkedin_url": "https://www.linkedin.com/in/fictional-priya-patel-media",
        "instagram_url": "https://www.instagram.com/fictional_priya_frames",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Independent Documentary Filmmaker and Investigative Culture Journalist focusing on coastal heritage.", "confidence": 1.0},
            {"platform": "linkedin", "category": "interest", "type": "explicit_statement", "quote": "Passionate about indigenous oral archives, film preservation, and community media cooperatives.", "confidence": 0.95},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "35mm manual film photography, architectural walks across South Mumbai colonial quarters.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Sea swimmer at Juhu, Irani café bun maska lover, spontaneous weekend traveler.", "confidence": 0.9}
        ],
        "analyzed_profile": {
            "summary": "Passionate documentary filmmaker and visual storyteller exploring Mumbai's coastal subcultures through analogue film, sea swimming, and heritage walks.",
            "career_interests": ["Documentary Filmmaking", "Investigative Journalism", "Cultural Archiving"],
            "demonstrated_hobbies": ["35mm Film Photography", "Heritage Architecture Walks", "Open Water Sea Swimming"],
            "stated_interests": ["Cinema History", "Oral Storytelling", "Coastal Ecology"],
            "lifestyle_preferences": ["Spontaneous weekend explorer", "Irani café regular", "Unfiltered cultural immersion"],
            "communication_preferences": ["Natural storyteller", "Warm and emotionally perceptive", "Authentic conversationalist"],
            "relationship_preferences": ["Warm, open-minded partner", "Appreciates art, cinema, and heartfelt late-night talks"],
            "explicit_facts": ["Independent documentary filmmaker in Mumbai", "Practicing 35mm film photographer"],
            "inferences_with_confidence": [
                {"claim": "Deeply empathetic and observant of diverse human experiences", "confidence": 0.94, "basis": "Career dedicated to grassroots oral histories and documentary filmmaking"}
            ],
            "uncertainties_and_unknowns": ["Travel schedule predictability during film production cycles"]
        }
    },
    {
        "id": "part-demo-05",
        "name": "Vikram Malhotra",
        "age": 32,
        "gender": "Male",
        "target_gender": "Female",
        "location": "Delhi NCR",
        "linkedin_url": "https://www.linkedin.com/in/fictional-vikram-malhotra-clean",
        "instagram_url": "https://www.instagram.com/fictional_vikram_peaks",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Clean Energy Policy Consultant advising public utility grid decarbonization across North India.", "confidence": 1.0},
            {"platform": "linkedin", "category": "interest", "type": "explicit_statement", "quote": "Advocating for renewable energy storage, distributed microgrids, and equitable sustainability policies.", "confidence": 0.95},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "High-altitude trekking in Ladakh, competitive squash player, non-fiction book club convener.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Early riser, winter rooftop gardener, loves slow Sunday conversations over adrak chai.", "confidence": 0.9}
        ],
        "analyzed_profile": {
            "summary": "Purpose-driven clean energy strategist in Delhi NCR who balances serious policy work with Himalayan high-altitude summits, squash, and literary book clubs.",
            "career_interests": ["Grid Decarbonization", "Renewable Energy Policy", "Sustainability Transition"],
            "demonstrated_hobbies": ["Himalayan Trekking", "Squash", "Book Club Organizing"],
            "stated_interests": ["Geopolitics", "Environmental Law", "Indian Classical Sitar"],
            "lifestyle_preferences": ["Early riser", "Winter gardener", "Enjoys quiet tea rituals and slow weekends"],
            "communication_preferences": ["Measured and thoughtful", "Diplomatic and respectful", "Deeply engaged listener"],
            "relationship_preferences": ["Committed, values-aligned partner", "Growth-oriented with shared empathy and social consciousness"],
            "explicit_facts": ["Clean energy policy consultant in Delhi NCR", "Experienced Himalayan high-altitude trekker"],
            "inferences_with_confidence": [
                {"claim": "Resilient, patient, and grounded under pressure", "confidence": 0.91, "basis": "Combines high-stakes utility policy with demanding mountain expeditions"}
            ],
            "uncertainties_and_unknowns": ["Preference between urban Delhi apartment vs outskirts farmhouse living"]
        }
    },
    {
        "id": "part-demo-06",
        "name": "Meera Nair",
        "age": 29,
        "gender": "Female",
        "target_gender": "Male",
        "location": "Delhi NCR",
        "linkedin_url": "https://www.linkedin.com/in/fictional-meera-nair-bio",
        "instagram_url": "https://www.instagram.com/fictional_meera_nature",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Computational Biologist researching rare genetic disease variants and precision therapeutics.", "confidence": 1.0},
            {"platform": "linkedin", "category": "interest", "type": "explicit_statement", "quote": "Focusing on statistical genomics, open scientific reproducibility, and ethical biomedical data.", "confidence": 0.95},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Birdwatching at Asola Bhatti Sanctuary, botanical watercolor painting, National Museum visits.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Lover of artisanal teas, quiet libraries, gentle morning walks, and historic architecture.", "confidence": 0.95}
        ],
        "analyzed_profile": {
            "summary": "Reflective computational genomics scientist based in Delhi NCR with a gentle reverence for natural history, avian birdwatching, botanical art, and historical museums.",
            "career_interests": ["Computational Biology", "Rare Disease Genomics", "Bioinformatics"],
            "demonstrated_hobbies": ["Avian Birdwatching", "Botanical Watercolors", "Museum & Heritage Exploration"],
            "stated_interests": ["Evolutionary Biology", "Ancient History", "Tea Culture"],
            "lifestyle_preferences": ["Gentle early morning rhythm", "Library and book lover", "Prefers peaceful natural spaces"],
            "communication_preferences": ["Quietly observant", "Insightful and sincere", "Gentle, dry humor"],
            "relationship_preferences": ["Kind, intellectually curious partner", "Values emotional gentleness, honesty, and shared calm moments"],
            "explicit_facts": ["Computational biologist working on genomic disease variants", "Regular birdwatcher at Delhi sanctuaries"],
            "inferences_with_confidence": [
                {"claim": "Deeply reflective, steady, and unpretentious", "confidence": 0.93, "basis": "Scientific rigor combined with quiet botanical and birding interests"}
            ],
            "uncertainties_and_unknowns": ["Tolerance for loud or frantic social gatherings"]
        }
    },
    {
        "id": "part-demo-07",
        "name": "Kabir Sen",
        "age": 31,
        "gender": "Male",
        "target_gender": "Female",
        "location": "Hyderabad, Telangana",
        "linkedin_url": "https://www.linkedin.com/in/fictional-kabir-sen-chips",
        "instagram_url": "https://www.instagram.com/fictional_kabir_tastes",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Principal Silicon Verification Engineer designing next-gen neural processing chipsets in HITEC City.", "confidence": 1.0},
            {"platform": "linkedin", "category": "interest", "type": "explicit_statement", "quote": "Hardware verification methodologies, RISC-V computing architecture, and open silicon initiatives.", "confidence": 0.95},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Culinary gastronomy explorer testing regional Hyderabadi biryani spices, acoustic blues guitar.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Indoor rock bouldering regular, weekend cookouts for friends, craft beverage taster.", "confidence": 0.9}
        ],
        "analyzed_profile": {
            "summary": "Enthusiastic semiconductor engineer in Hyderabad who loves microarchitecture by day, and spends evenings exploring culinary spices, bouldering, and fingerstyle blues guitar.",
            "career_interests": ["Semiconductor Verification", "Neural Processing Hardware", "RISC-V Architectures"],
            "demonstrated_hobbies": ["Spice & Regional Gastronomy", "Acoustic Blues Guitar", "Rock Bouldering"],
            "stated_interests": ["Audio Acoustics", "Culinary History", "Hardware Hacking"],
            "lifestyle_preferences": ["Social weekend cook", "Active bouldering enthusiast", "Enjoys warm dinner gatherings"],
            "communication_preferences": ["Warm and hearty", "Humorous, humble, and approachable", "Engaging conversationalist"],
            "relationship_preferences": ["Supportive, fun-loving companion", "Enjoys food adventures, shared laughter, and genuine warmth"],
            "explicit_facts": ["Lead silicon verification engineer in Hyderabad", "Acoustic guitar player and rock boulderer"],
            "inferences_with_confidence": [
                {"claim": "Warm, hospitable, and highly collaborative", "confidence": 0.9, "basis": "Frequent weekend cooking for friends and open-source hardware participation"}
            ],
            "uncertainties_and_unknowns": ["Long-term willingness to move away from primary tech hubs"]
        }
    },
    {
        "id": "part-demo-08",
        "name": "Neha Gupta",
        "age": 25,
        "gender": "Female",
        "target_gender": "Male",
        "location": "Hyderabad, Telangana",
        "linkedin_url": "https://www.linkedin.com/in/fictional-neha-gupta-product",
        "instagram_url": "https://www.instagram.com/fictional_neha_reads",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Product Manager building digital therapeutics and remote maternal health platforms.", "confidence": 1.0},
            {"platform": "linkedin", "category": "interest", "type": "explicit_statement", "quote": "Passionate about healthcare access, behavioral nudges in product design, and patient privacy.", "confidence": 0.95},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Competitive badminton at Gachibowli stadium, sci-fi book reviewer, café enthusiast.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "High energy, structured planner, weekend park runner, loves specialty iced lattes.", "confidence": 0.9}
        ],
        "analyzed_profile": {
            "summary": "Dynamic, vibrant healthtech product manager in Hyderabad who balances impactful work with high-octane badminton games, science fiction reading, and sunny café afternoons.",
            "career_interests": ["Healthtech Product Management", "Behavioral Design", "Digital Therapeutics"],
            "demonstrated_hobbies": ["Competitive Badminton", "Sci-Fi Book Reviewing", "Weekend 5k Running"],
            "stated_interests": ["Behavioral Psychology", "Urban Mobility", "Specialty Coffee"],
            "lifestyle_preferences": ["Energetic, organized schedule", "Fitness enthusiast", "Enjoys café coworking and weekend park outings"],
            "communication_preferences": ["Enthusiastic and clear", "Quick-witted and optimistic", "Direct and proactive"],
            "relationship_preferences": ["Motivated, uplifting partner", "Shares mutual curiosity, playful banter, and active lifestyle"],
            "explicit_facts": ["Healthcare product manager in Hyderabad", "Badminton tournament participant"],
            "inferences_with_confidence": [
                {"claim": "Goal-driven and exceptionally positive", "confidence": 0.91, "basis": "Healthtech product focus combined with competitive sports and book curation"}
            ],
            "uncertainties_and_unknowns": ["Balance between corporate ambition and slow leisure time"]
        }
    },
    {
        "id": "part-demo-09",
        "name": "Aditya Kulkarni",
        "age": 29,
        "gender": "Male",
        "target_gender": "Female",
        "location": "Pune, Maharashtra",
        "linkedin_url": "https://www.linkedin.com/in/fictional-aditya-kulkarni-auto",
        "instagram_url": "https://www.instagram.com/fictional_aditya_rides",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Electric Vehicle Powertrain Simulation Lead developing high-efficiency battery packs in Hinjewadi.", "confidence": 1.0},
            {"platform": "linkedin", "category": "interest", "type": "explicit_statement", "quote": "Battery thermal management, clean mobility decarbonization, and embedded firmware testing.", "confidence": 0.95},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Motorcycle touring across the Sahyadri ghats, drummer in a local indie alternative rock band.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Spontaneous weekend camper, board game night strategist, filter coffee and misal pav fan.", "confidence": 0.9}
        ],
        "analyzed_profile": {
            "summary": "Energetic EV powertrain engineer based in Pune who loves mechanical precision, indie rock drumming, motorcycle expeditions across the Sahyadris, and board games.",
            "career_interests": ["Electric Mobility", "Powertrain Thermal Simulation", "Battery Tech"],
            "demonstrated_hobbies": ["Motorcycle Touring in Sahyadris", "Indie Rock Drumming", "Strategic Board Games"],
            "stated_interests": ["Acoustics & Live Sound", "Automotive Design", "DIY Electronics"],
            "lifestyle_preferences": ["Weekend adventurer", "Music rehearsal regular", "Unpretentious local foodie"],
            "communication_preferences": ["Playful and warm", "Authentic and spontaneous", "Collaborative team player"],
            "relationship_preferences": ["Spontaneous, fun-loving partner", "Shares love for live music, road trips, and open laughter"],
            "explicit_facts": ["EV battery simulation engineer in Pune", "Drummer in an active indie band"],
            "inferences_with_confidence": [
                {"claim": "Values shared real-world experiences and teamwork", "confidence": 0.89, "basis": "Band membership, motorcycle group touring, and cooperative board gaming"}
            ],
            "uncertainties_and_unknowns": ["Willingness to adapt to non-outdoorsy leisure preferences"]
        }
    },
    {
        "id": "part-demo-10",
        "name": "Tanvi Joshi",
        "age": 27,
        "gender": "Female",
        "target_gender": "Male",
        "location": "Pune, Maharashtra",
        "linkedin_url": "https://www.linkedin.com/in/fictional-tanvi-joshi-brand",
        "instagram_url": "https://www.instagram.com/fictional_tanvi_art",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Brand Strategist and Creative Director for sustainable, zero-waste consumer wellness brands.", "confidence": 1.0},
            {"platform": "linkedin", "category": "interest", "type": "explicit_statement", "quote": "Focusing on regenerative commerce, ethical consumer narratives, and circular product design.", "confidence": 0.95},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Wheel pottery throwing at Koregaon Park studio, cultivating balcony edible microgreens.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Aesthetic minimalist, Saturday farmers market visitor, French cinema and jazz lover.", "confidence": 0.95}
        ],
        "analyzed_profile": {
            "summary": "Creative and mindful brand strategist in Pune who champions ecological sustainability, wheel-thrown ceramics, artisanal teas, and thoughtful slow design.",
            "career_interests": ["Sustainable Brand Strategy", "Circular Design", "Regenerative Marketing"],
            "demonstrated_hobbies": ["Ceramic Pottery Wheel Throwing", "Balcony Microgreen Gardening", "Artisan Tea Brewing"],
            "stated_interests": ["Typography", "French Cinema", "Modernist Interior Architecture"],
            "lifestyle_preferences": ["Slow and conscious living", "Farmers market shopper", "Aesthetic and uncluttered home"],
            "communication_preferences": ["Articulate, graceful, and warm", "Deeply perceptive listener", "Values authenticity"],
            "relationship_preferences": ["Conscious, kind-hearted companion", "Grounded in emotional maturity, shared values, and creativity"],
            "explicit_facts": ["Brand director for sustainable lifestyle brands in Pune", "Practicing potter with home ceramic wheel"],
            "inferences_with_confidence": [
                {"claim": "Deeply intentional in both personal and professional choices", "confidence": 0.93, "basis": "Cohesive alignment across circular brand work, slow ceramics, and mindful consumption"}
            ],
            "uncertainties_and_unknowns": ["Patience with highly chaotic or unpredictable lifestyle routines"]
        }
    },
    {
        "id": "part-demo-11",
        "name": "Siddharth Menon",
        "age": 33,
        "gender": "Male",
        "target_gender": "Female",
        "location": "Chennai, Tamil Nadu",
        "linkedin_url": "https://www.linkedin.com/in/fictional-siddharth-menon-systems",
        "instagram_url": "https://www.instagram.com/fictional_sid_ocean",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Principal Distributed Cloud Architect engineering ultra-low-latency financial streaming pipelines.", "confidence": 1.0},
            {"platform": "linkedin", "category": "interest", "type": "explicit_statement", "quote": "Distributed consensus algorithms, high-throughput memory engines, and resilient cloud architectures.", "confidence": 0.95},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Morning surfing sessions at Covelong Point, classical keyboard, sourdough bread baking.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Calm coastal lifestyle, early morning wave chaser, traditional Madras filter coffee aficionado.", "confidence": 0.9}
        ],
        "analyzed_profile": {
            "summary": "Composed, highly accomplished distributed systems engineer in Chennai who starts his mornings catching waves at Covelong Point, plays keyboard, and values deep quiet calm.",
            "career_interests": ["Distributed Systems", "Cloud Infrastructure", "High-Throughput Engines"],
            "demonstrated_hobbies": ["Surfing at Covelong Point", "Classical Piano & Keyboard", "Sourdough Bread Crafting"],
            "stated_interests": ["Marine Ecology", "Audio Engineering", "Modern Architecture"],
            "lifestyle_preferences": ["Coastal sunrise routine", "Calm and composed demeanor", "Unwavering filter coffee ritual"],
            "communication_preferences": ["Measured, calm, and thoughtful", "Low-drama and loyal", "Empathetic listener"],
            "relationship_preferences": ["Emotionally steady, independent partner", "Mutual intellectual respect, shared peace, and ocean love"],
            "explicit_facts": ["Principal cloud systems architect in Chennai", "Regular surfer at Covelong Point"],
            "inferences_with_confidence": [
                {"claim": "Exceptionally steady under emotional and intellectual stress", "confidence": 0.92, "basis": "Combines high-reliability distributed systems work with ocean wave surfing"}
            ],
            "uncertainties_and_unknowns": ["Willingness to live far from coastal water bodies"]
        }
    },
    {
        "id": "part-demo-12",
        "name": "Pooja Rao",
        "age": 28,
        "gender": "Female",
        "target_gender": "Male",
        "location": "Chennai, Tamil Nadu",
        "linkedin_url": "https://www.linkedin.com/in/fictional-pooja-rao-legal",
        "instagram_url": "https://www.instagram.com/fictional_pooja_steps",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Intellectual Property and Tech Policy Counsel specializing in generative AI governance and copyright.", "confidence": 1.0},
            {"platform": "linkedin", "category": "interest", "type": "explicit_statement", "quote": "Digital rights in emerging economies, fair attribution in machine learning, and algorithmic accountability.", "confidence": 0.95},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Bharatanatyam dancer performing during the December Margazhi season, jogging along Elliot's Beach.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Avid cryptic crossword solver, weekend heritage walker, South Indian culinary enthusiast.", "confidence": 0.9}
        ],
        "analyzed_profile": {
            "summary": "Sharpminded tech policy attorney and classical Bharatanatyam dancer in Chennai who brings cultural depth, intellectual rigor, and beachside jogs into daily life.",
            "career_interests": ["AI Governance & Tech Law", "Intellectual Property", "Digital Rights"],
            "demonstrated_hobbies": ["Bharatanatyam Classical Dance", "Beachside Jogging", "Cryptic Crosswords"],
            "stated_interests": ["Indian Legal History", "Performing Arts", "Maritime Archaeology"],
            "lifestyle_preferences": ["Culturally rooted routine", "Morning runner on Elliot's Beach", "Avid reader and quizzer"],
            "communication_preferences": ["Eloquent and sharp-witted", "Warm and deeply respectful", "Loves substantive debate"],
            "relationship_preferences": ["Intellectually stimulating partner", "Values integrity, shared cultural appreciation, and humor"],
            "explicit_facts": ["Technology policy attorney in Chennai", "Trained classical Bharatanatyam performer"],
            "inferences_with_confidence": [
                {"claim": "Disciplined and articulate with deep cultural anchoring", "confidence": 0.94, "basis": "Rigorous legal career alongside high-level Margazhi season dance performances"}
            ],
            "uncertainties_and_unknowns": ["Demanding legal schedule during court session months"]
        }
    },
    {
        "id": "part-demo-13",
        "name": "Arjun Reddy",
        "age": 30,
        "gender": "Male",
        "target_gender": "Female",
        "location": "Bengaluru, Karnataka",
        "linkedin_url": "https://www.linkedin.com/in/fictional-arjun-reddy-agri",
        "instagram_url": "https://www.instagram.com/fictional_arjun_agri",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Co-founder & CTO at an Agritech startup building solar-powered IoT telemetry for regenerative farmers.", "confidence": 1.0},
            {"platform": "linkedin", "category": "interest", "type": "explicit_statement", "quote": "Rural IoT connectivity, sensor telemetry, soil microbiology, and climate adaptation in agriculture.", "confidence": 0.95},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Calisthenics workout park enthusiast, rooftop organic tomato and chilli gardening, podcast host.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Hands-on tinkerer, early riser, loves simple home-cooked South Indian meals and road trips.", "confidence": 0.9}
        ],
        "analyzed_profile": {
            "summary": "Grounded agritech founder and engineer in Bengaluru dedicated to rural IoT innovations, rooftop permaculture, calisthenics, and wholesome sustainable living.",
            "career_interests": ["Agritech Startups", "IoT Telemetry Systems", "Soil Microbiology"],
            "demonstrated_hobbies": ["Calisthenics Training", "Rooftop Permaculture", "Agricultural Podcasting"],
            "stated_interests": ["Renewable Power", "Supply Chain Transparency", "Rural Economics"],
            "lifestyle_preferences": ["Early riser", "Hands-on maker and builder", "Values simple, healthy home meals"],
            "communication_preferences": ["Candid, honest, and direct", "Down-to-earth and pragmatic", "Active problem-solver"],
            "relationship_preferences": ["Kind-hearted, resilient partner", "Shares grounded life vision, real-world purpose, and laughter"],
            "explicit_facts": ["Co-founder of an agritech hardware startup", "Maintains productive rooftop organic garden"],
            "inferences_with_confidence": [
                {"claim": "Hardworking, practical, and unpretentious", "confidence": 0.91, "basis": "Hardware startup builder working directly with farmers and rural systems"}
            ],
            "uncertainties_and_unknowns": ["Frequent regional field travel to rural farms"]
        }
    },
    {
        "id": "part-demo-14",
        "name": "Divya Krishnan",
        "age": 26,
        "gender": "Female",
        "target_gender": "Male",
        "location": "Bengaluru, Karnataka",
        "linkedin_url": "https://www.linkedin.com/in/fictional-divya-krishnan-data",
        "instagram_url": "https://www.instagram.com/fictional_divya_moves",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Data Scientist & Algorithm Auditor researching recommender system fairness and serendipity.", "confidence": 1.0},
            {"platform": "linkedin", "category": "interest", "type": "explicit_statement", "quote": "Algorithmic bias mitigation, graph neural networks, and user agency in digital platforms.", "confidence": 0.95},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Social Salsa and Bachata dancer, specialty coffee home brewer, indoor rock boulderer.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Social butterfly, weekend brunch enthusiast, loves indie music gigs in Koramangala.", "confidence": 0.9}
        ],
        "analyzed_profile": {
            "summary": "Bright and lively recommender systems data scientist in Bengaluru who pairs algorithmic curiosity with Latin salsa dance, bouldering, and vibrant social brunches.",
            "career_interests": ["Algorithmic Fairness", "Recommender Systems", "Graph Neural Networks"],
            "demonstrated_hobbies": ["Salsa & Bachata Social Dancing", "Rock Bouldering", "Specialty Coffee Brewing"],
            "stated_interests": ["Music Theory", "Data Privacy", "Indie Music Gigs"],
            "lifestyle_preferences": ["Vibrant weekend social life", "Fitness and movement focused", "Enjoys exploring cozy Bengaluru cafes"],
            "communication_preferences": ["Warm, expressive, and engaging", "Inquisitive and quick to laugh", "Transparent"],
            "relationship_preferences": ["Fun, emotionally mature partner", "Loves music, movement, shared adventures, and mutual growth"],
            "explicit_facts": ["Data scientist at tech company in Bengaluru", "Active social salsa dancer and boulderer"],
            "inferences_with_confidence": [
                {"claim": "High interpersonal energy combined with sharp analytical acumen", "confidence": 0.92, "basis": "Recommender data science alongside active Latin dance community leadership"}
            ],
            "uncertainties_and_unknowns": ["Comfort with partner having completely introverted weekend preferences"]
        }
    },
    {
        "id": "part-demo-15",
        "name": "Varun Kapoor",
        "age": 31,
        "gender": "Male",
        "target_gender": "Female",
        "location": "Delhi NCR",
        "linkedin_url": "https://www.linkedin.com/in/fictional-varun-kapoor-fin",
        "instagram_url": "https://www.instagram.com/fictional_varun_cooks",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Fintech Growth Director & Early-Stage Venture Scout evaluating cross-border B2B platforms.", "confidence": 1.0},
            {"platform": "linkedin", "category": "interest", "type": "explicit_statement", "quote": "Cross-border payment rails, digital financial inclusion, and tech angel investing.", "confidence": 0.95},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Gourmet Awadhi slow cooking, tennis player at Delhi Gymkhana, vintage mechanical watch collector.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Cosmopolitan host, winter terrace BBQ organizer, lover of historical biographies.", "confidence": 0.9}
        ],
        "analyzed_profile": {
            "summary": "Sophisticated fintech director and culinary host in Delhi NCR who enjoys traditional Awadhi slow cooking, tennis, horology, and engaging conversations on business and history.",
            "career_interests": ["Fintech Growth", "Venture Investing", "Cross-Border Payments"],
            "demonstrated_hobbies": ["Awadhi Gourmet Cooking", "Tennis", "Vintage Horology Collecting"],
            "stated_interests": ["Economic History", "Modern Indian Art", "Travel Photography"],
            "lifestyle_preferences": ["Cosmopolitan dinner party host", "Active tennis player", "Appreciates craftsmanship and detail"],
            "communication_preferences": ["Charismatic and courteous", "Attentive and engaging", "Enjoys storytelling"],
            "relationship_preferences": ["Ambitious, warm-hearted equal partner", "Appreciates culinary arts, travel, and strong family ties"],
            "explicit_facts": ["Fintech director and venture scout in Delhi", "Active tennis player at Delhi clubs"],
            "inferences_with_confidence": [
                {"claim": "Generous and detail-oriented host", "confidence": 0.9, "basis": "Dedication to complex multi-hour traditional cooking and hosting friends"}
            ],
            "uncertainties_and_unknowns": ["Work travel frequency across Asian financial hubs"]
        }
    },
    {
        "id": "part-demo-16",
        "name": "Riya Banerjee",
        "age": 27,
        "gender": "Female",
        "target_gender": "Male",
        "location": "Kolkata, West Bengal",
        "linkedin_url": "https://www.linkedin.com/in/fictional-riya-banerjee-lit",
        "instagram_url": "https://www.instagram.com/fictional_riya_words",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Senior Literary Editor & Cultural Archivist at an independent university publishing press.", "confidence": 1.0},
            {"platform": "linkedin", "category": "interest", "type": "explicit_statement", "quote": "Translation studies, South Asian postcolonial literature, and community library preservation.", "confidence": 0.95},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Browsing rare first editions on College Street, singing Rabindrasangeet, tram photography.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Slow living advocate, Darjeeling first-flush tea lover, rainy evening book enthusiast.", "confidence": 0.95}
        ],
        "analyzed_profile": {
            "summary": "Gentle, intellectually rich literary editor in Kolkata with deep roots in cultural history, College Street book hunts, Rabindrasangeet vocals, and slow tea afternoons.",
            "career_interests": ["Literary Publishing", "Translation Studies", "Cultural Archiving"],
            "demonstrated_hobbies": ["Rare Book Collecting", "Rabindrasangeet Vocals", "Analogue Tram Photography"],
            "stated_interests": ["Postcolonial Literature", "Culinary History of Bengal", "Cinema of Satyajit Ray"],
            "lifestyle_preferences": ["Slow and contemplative lifestyle", "Tea connoisseur", "Cherishes quiet intellectual spaces"],
            "communication_preferences": ["Poetic and articulate", "Gentle, attentive, and deeply perceptive", "Values emotional honesty"],
            "relationship_preferences": ["Kindred intellectual soul", "Values gentleness, depth of character, and quiet companionship"],
            "explicit_facts": ["Literary editor in Kolkata publishing house", "Classical Bengali music vocalist"],
            "inferences_with_confidence": [
                {"claim": "Deeply reflective and emotionally sensitive", "confidence": 0.95, "basis": "Immersion in literary translation, classical vocal music, and archival heritage"}
            ],
            "uncertainties_and_unknowns": ["Openness to moving to hyper-fast commercial cities"]
        }
    },
    {
        "id": "part-demo-17",
        "name": "Nikhil Deshmukh",
        "age": 29,
        "gender": "Male",
        "target_gender": "Female",
        "location": "Mumbai, Maharashtra",
        "linkedin_url": "https://www.linkedin.com/in/fictional-nikhil-deshmukh-game",
        "instagram_url": "https://www.instagram.com/fictional_nikhil_pixels",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Lead Technical Animator & Virtual Production Artist for real-time game engines.", "confidence": 1.0},
            {"platform": "linkedin", "category": "interest", "type": "explicit_statement", "quote": "Procedural character rigging, real-time raytracing, and generative animation pipelines.", "confidence": 0.95},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Building custom mechanical keyboards, comic book sketching, bouldering in Navi Mumbai.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Night owl creator, Japanese ramen and street food lover, sci-fi cinema marathon runner.", "confidence": 0.9}
        ],
        "analyzed_profile": {
            "summary": "Creative and technical gaming animator in Mumbai who enjoys building artisanal mechanical keyboards, sketching comic art, bouldering, and sci-fi film marathons.",
            "career_interests": ["Game Engine Animation", "Virtual Production", "Procedural Graphics"],
            "demonstrated_hobbies": ["Mechanical Keyboard Crafting", "Comic Art Sketching", "Indoor Bouldering"],
            "stated_interests": ["Sci-Fi Worldbuilding", "Japanese Animation", "Cyber-Physical Art"],
            "lifestyle_preferences": ["Night owl creative rhythm", "Casual and relaxed vibe", "Enjoys hands-on DIY projects"],
            "communication_preferences": ["Playful, sincere, and humble", "Easy-going conversationalist", "Great listener"],
            "relationship_preferences": ["Down-to-earth, genuine partner", "Shares laughs, creative sparks, and comfortable quiet moments"],
            "explicit_facts": ["Technical animator in gaming studio", "Custom keyboard artisan and illustrator"],
            "inferences_with_confidence": [
                {"claim": "Patient and meticulous craftsman", "confidence": 0.9, "basis": "Hand-soldering custom mechanical keyboards and fine animation rigging"}
            ],
            "uncertainties_and_unknowns": ["Morning routine compatibility with an early riser"]
        }
    },
    {
        "id": "part-demo-18",
        "name": "Shreya Mehra",
        "age": 28,
        "gender": "Female",
        "target_gender": "Male",
        "location": "Mumbai, Maharashtra",
        "linkedin_url": "https://www.linkedin.com/in/fictional-shreya-mehra-eco",
        "instagram_url": "https://www.instagram.com/fictional_shreya_flow",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Circular Supply Chain Consultant helping consumer brands eliminate single-use plastics.", "confidence": 1.0},
            {"platform": "linkedin", "category": "interest", "type": "explicit_statement", "quote": "Extended producer responsibility, ocean plastic recycling, and closed-loop material logistics.", "confidence": 0.95},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Certified Vinyasa yoga teacher, sea kayaking off Mandwa, vintage thrifting explorer.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Plant-based home cook, sunset coastal watcher, mindful consumer living clutter-free.", "confidence": 0.9}
        ],
        "analyzed_profile": {
            "summary": "Conscious circular economy leader and certified yoga instructor in Mumbai who embraces ocean kayaking, plant-based culinary experiments, and mindful minimalism.",
            "career_interests": ["Circular Supply Chains", "Environmental Consulting", "Plastic Elimination"],
            "demonstrated_hobbies": ["Vinyasa Yoga Teaching", "Sea Kayaking at Mandwa", "Vintage Thrifting"],
            "stated_interests": ["Marine Conservation", "Mindful Living", "Holistic Wellness"],
            "lifestyle_preferences": ["Plant-based lifestyle", "Clutter-free and minimalist home", "Active morning movement"],
            "communication_preferences": ["Centering and uplifting", "Deeply empathetic and attentive", "Honest and compassionate"],
            "relationship_preferences": ["Conscious, emotionally mature partner", "Committed to personal growth, kindness, and sustainable living"],
            "explicit_facts": ["Circular supply chain consultant in Mumbai", "Certified Vinyasa yoga instructor"],
            "inferences_with_confidence": [
                {"claim": "Possesses strong emotional equilibrium and vitality", "confidence": 0.92, "basis": "Combines daily yoga practice and ocean sports with professional sustainability mission"}
            ],
            "uncertainties_and_unknowns": ["Dietary flexibility when dining at strictly non-vegetarian venues"]
        }
    },
    {
        "id": "part-demo-19",
        "name": "Rahul Singhania",
        "age": 34,
        "gender": "Male",
        "target_gender": "Female",
        "location": "Bengaluru, Karnataka",
        "linkedin_url": "https://www.linkedin.com/in/fictional-rahul-singhania-med",
        "instagram_url": "https://www.instagram.com/fictional_rahul_pulse",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Pediatric Surgeon & Tele-ICU Technology Researcher improving remote infant surgical care.", "confidence": 1.0},
            {"platform": "linkedin", "category": "interest", "type": "explicit_statement", "quote": "Tele-robotic surgery protocols, equitable pediatric healthcare, and clinical bioethics.", "confidence": 0.95},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Marathon distance runner, acoustic fingerstyle guitar player, weekend animal shelter volunteer.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Compassionate, disciplined life rhythm, nature retreat lover, values quiet evenings.", "confidence": 0.9}
        ],
        "analyzed_profile": {
            "summary": "Dedicated pediatric surgeon and digital healthcare innovator in Bengaluru who grounds intense clinical demands with marathon running, acoustic guitar, and animal shelter work.",
            "career_interests": ["Pediatric Surgery", "Tele-ICU Innovation", "Clinical Bioethics"],
            "demonstrated_hobbies": ["Marathon Running", "Fingerstyle Acoustic Guitar", "Animal Rescue Volunteering"],
            "stated_interests": ["Medical Ethics", "Wilderness Medicine", "Classical Literature"],
            "lifestyle_preferences": ["Disciplined and resilient", "Values restorative quiet weekends", "Nature retreat traveler"],
            "communication_preferences": ["Calm, reassuring, and warm", "Patient and deep listener", "Sincere and supportive"],
            "relationship_preferences": ["Compassionate, resilient companion", "Values family, deep mutual loyalty, kindness, and empathy"],
            "explicit_facts": ["Pediatric surgeon practicing in Bengaluru", "Completed multiple full marathons"],
            "inferences_with_confidence": [
                {"claim": "Exceptional patience and emotional fortitude", "confidence": 0.95, "basis": "Demanding pediatric surgical career paired with marathon discipline and rescue volunteering"}
            ],
            "uncertainties_and_unknowns": ["Emergency on-call duty frequency on weekends"]
        }
    },
    {
        "id": "part-demo-20",
        "name": "Ishita Bhatia",
        "age": 25,
        "gender": "Female",
        "target_gender": "Male",
        "location": "Delhi NCR",
        "linkedin_url": "https://www.linkedin.com/in/fictional-ishita-bhatia-ai",
        "instagram_url": "https://www.instagram.com/fictional_ishita_vibes",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "NLP Dialogue Systems Researcher specializing in conversational grounding and humor detection.", "confidence": 1.0},
            {"platform": "linkedin", "category": "interest", "type": "explicit_statement", "quote": "Computational linguistics, pragmatic inference in LLMs, and conversational AI safety.", "confidence": 0.95},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Stand-up comedy open mic performer, cafe hopping in Hauz Khas, French pastry baking.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "High energy, witty conversationalist, weekend spontaneous road tripper, coffee lover.", "confidence": 0.9}
        ],
        "analyzed_profile": {
            "summary": "Sparkling and quick-witted conversational NLP researcher in Delhi who does stand-up comedy open mics, bakes French pastries, and loves spontaneous road trips.",
            "career_interests": ["Computational Linguistics", "Conversational AI Safety", "Humor Understanding"],
            "demonstrated_hobbies": ["Stand-up Comedy Open Mics", "Pastry & Choux Baking", "Café Exploration in Hauz Khas"],
            "stated_interests": ["Pragmatics & Semantics", "Podcast Production", "Classic Comedy Shows"],
            "lifestyle_preferences": ["Spontaneous and fun-loving", "High intellectual energy", "Enjoys lively conversations with friends"],
            "communication_preferences": ["Playfully witty and expressive", "Sharp, clever, and energetic", "Deeply authentic"],
            "relationship_preferences": ["Partner who loves laughter and smart banter", "Can tease and be teased, shares intellectual curiosity"],
            "explicit_facts": ["Dialogue systems NLP researcher in Delhi", "Active comedy open mic performer"],
            "inferences_with_confidence": [
                {"claim": "Quick-thinking, confident, and highly verbal", "confidence": 0.93, "basis": "Combines linguistics research with live stand-up comedy performance"}
            ],
            "uncertainties_and_unknowns": ["Patience for long periods of quiet non-verbal routine"]
        }
    },
    {
        "id": "part-demo-21",
        "name": "Karthik Sundaram",
        "age": 30,
        "gender": "Male",
        "target_gender": "Female",
        "location": "Hyderabad, Telangana",
        "linkedin_url": "https://www.linkedin.com/in/fictional-karthik-sundaram-cloud",
        "instagram_url": "https://www.instagram.com/fictional_karthik_trails",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Cloud Security Operations Architect specializing in zero-trust enterprise infrastructure.", "confidence": 1.0},
            {"platform": "linkedin", "category": "interest", "type": "explicit_statement", "quote": "Threat modeling, cryptography protocols, and cloud access governance.", "confidence": 0.95},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Mountain biking across rocky Hyderabad trails, badminton player, specialty coffee roasting.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Methodical, dependable, loves early Sunday trail rides and wholesome homemade South Indian cooking.", "confidence": 0.9}
        ],
        "analyzed_profile": {
            "summary": "Dependable and calm cloud security architect in Hyderabad who loves navigating rugged mountain bike trails, home roasting coffee beans, and badminton.",
            "career_interests": ["Cloud Infrastructure Security", "Zero-Trust Architecture", "Cryptography"],
            "demonstrated_hobbies": ["Mountain Biking", "Badminton", "Home Coffee Roasting"],
            "stated_interests": ["Cybersecurity Ethics", "Landscape Photography", "Outdoor Trails"],
            "lifestyle_preferences": ["Active weekend mornings", "Methodical and dependable habits", "Enjoys cooking traditional recipes"],
            "communication_preferences": ["Calm and grounded", "Logical, honest, and caring", "Thoughtful listener"],
            "relationship_preferences": ["Kind, steady life partner", "Values trust, emotional safety, shared healthy habits, and warmth"],
            "explicit_facts": ["Cloud security architect based in Hyderabad", "Mountain biker on Hyderabad trails"],
            "inferences_with_confidence": [
                {"claim": "Highly reliable, loyal, and level-headed", "confidence": 0.91, "basis": "Zero-trust security responsibilities coupled with disciplined athletic hobbies"}
            ],
            "uncertainties_and_unknowns": ["Willingness to take highly impulsive unplanned vacations"]
        }
    },
    {
        "id": "part-demo-22",
        "name": "Sneha Mukherjee",
        "age": 29,
        "gender": "Female",
        "target_gender": "Male",
        "location": "Kolkata, West Bengal",
        "linkedin_url": "https://www.linkedin.com/in/fictional-sneha-mukherjee-art",
        "instagram_url": "https://www.instagram.com/fictional_sneha_curates",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Contemporary Art Curator & Gallery Exhibition Manager bridging modern art with indigenous crafts.", "confidence": 1.0},
            {"platform": "linkedin", "category": "interest", "type": "explicit_statement", "quote": "Visual semiotics, South Asian modernist movements, and public art preservation.", "confidence": 0.95},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Terracotta sculpture sculpting, heritage architecture walks, listening to classic Hindustani vinyl.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Immersed in artistic culture, loves twilight terrace adda discussions over Darjeeling tea.", "confidence": 0.95}
        ],
        "analyzed_profile": {
            "summary": "Cultured and expressive art curator in Kolkata who champions indigenous craft traditions, terracotta sculpture, Hindustani classical music, and warm terrace conversations.",
            "career_interests": ["Art Curatorship", "Modern Indian Art History", "Indigenous Crafts"],
            "demonstrated_hobbies": ["Terracotta Sculpture", "Heritage Architecture Walks", "Hindustani Classical Vinyl Collecting"],
            "stated_interests": ["Visual Semiotics", "Museum Studies", "Artisan Cooperatives"],
            "lifestyle_preferences": ["Artistically rich environment", "Enjoys Kolkata evening adda culture", "Slow tea lover"],
            "communication_preferences": ["Expressive, nuanced, and warm", "Deeply cultured and engaging", "Values sensitivity"],
            "relationship_preferences": ["Creative, emotionally available partner", "Respects artistic passion, deep dialogue, and kindness"],
            "explicit_facts": ["Contemporary art gallery curator in Kolkata", "Practicing terracotta sculptor"],
            "inferences_with_confidence": [
                {"claim": "Deep aesthetic sensibility and emotional intelligence", "confidence": 0.94, "basis": "Dedicated curation career and tactile terracotta craft practices"}
            ],
            "uncertainties_and_unknowns": ["Comfort with corporate or highly finance-dominated environments"]
        }
    },
    {
        "id": "part-demo-23",
        "name": "Devendra Patel",
        "age": 31,
        "gender": "Male",
        "target_gender": "Female",
        "location": "Pune, Maharashtra",
        "linkedin_url": "https://www.linkedin.com/in/fictional-devendra-patel-aerospace",
        "instagram_url": "https://www.instagram.com/fictional_dev_skies",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Aerospace Avionics Systems Engineer developing fault-tolerant satellite telemetry.", "confidence": 1.0},
            {"platform": "linkedin", "category": "interest", "type": "explicit_statement", "quote": "Orbital flight dynamics, radiation-hardened computing, and deep-space communication.", "confidence": 0.95},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Glider pilot training in Hadapsar, astrophotography in the Western Ghats, competitive chess.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Calm demeanor, curious mind, loyal partner, loves stargazing nights and quiet coffee mornings.", "confidence": 0.9}
        ],
        "analyzed_profile": {
            "summary": "Intellectually curious aerospace engineer in Pune who trains as a glider pilot, photographs distant nebulae from the Western Ghats, and plays strategic chess.",
            "career_interests": ["Aerospace Avionics", "Satellite Telemetry", "Deep-Space Systems"],
            "demonstrated_hobbies": ["Glider Pilot Flight Training", "Deep-Sky Astrophotography", "Chess"],
            "stated_interests": ["Orbital Mechanics", "Cosmology", "History of Aviation"],
            "lifestyle_preferences": ["Calm, patient demeanor", "Night sky observer", "Enjoys quiet mornings and strategic games"],
            "communication_preferences": ["Humble, thoughtful, and analytical", "Great listener", "Warm and dependable"],
            "relationship_preferences": ["Intellectually curious, supportive companion", "Values loyalty, quiet companionship, and shared awe of the world"],
            "explicit_facts": ["Aerospace avionics engineer in Pune", "Trained glider pilot student and astrophotographer"],
            "inferences_with_confidence": [
                {"claim": "High focus, patient, and methodically dependable", "confidence": 0.93, "basis": "Spacecraft flight avionics responsibility combined with aviation and astrophotography"}
            ],
            "uncertainties_and_unknowns": ["Frequency of weekend astrophotography expeditions during new moon weeks"]
        }
    },
    {
        "id": "part-demo-24",
        "name": "Natasha Fernandez",
        "age": 27,
        "gender": "Female",
        "target_gender": "Any",
        "location": "Mumbai, Maharashtra",
        "linkedin_url": "https://www.linkedin.com/in/fictional-natasha-fernandez-music",
        "instagram_url": "https://www.instagram.com/fictional_natasha_tunes",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Independent Music Producer & Spatial Audio Sound Designer for games and interactive exhibits.", "confidence": 1.0},
            {"platform": "linkedin", "category": "interest", "type": "explicit_statement", "quote": "Binaural recording, psychoacoustics, vintage analog synthesis, and open-source audio DSP.", "confidence": 0.95},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Scuba diving in Netrani Island, playing bass guitar in jazz fusion trios, vintage synth collecting.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Free-spirited coastal lover, night owl in the studio, appreciates genuine vulnerability.", "confidence": 0.95}
        ],
        "analyzed_profile": {
            "summary": "Creative, free-spirited sound designer and music producer in Mumbai who plays jazz bass, dives coastal reefs, and crafts immersive spatial audio landscapes.",
            "career_interests": ["Spatial Audio Design", "Music Production", "Interactive Audio Systems"],
            "demonstrated_hobbies": ["Scuba Diving", "Jazz Bass Guitar", "Vintage Analog Synthesis"],
            "stated_interests": ["Psychoacoustics", "Marine Conservation", "Film Soundtracks"],
            "lifestyle_preferences": ["Night owl studio workflow", "Coastal weekend retreats", "Appreciates open creative expression"],
            "communication_preferences": ["Warm, open, and authentic", "Emotionally in tune with others", "Spontaneous and fun"],
            "relationship_preferences": ["Empathetic, authentic partner of any gender", "Values artistic freedom, emotional intimacy, and mutual growth"],
            "explicit_facts": ["Spatial audio designer and producer in Mumbai", "Certified scuba diver and bassist"],
            "inferences_with_confidence": [
                {"claim": "High creative sensitivity and emotional empathy", "confidence": 0.93, "basis": "Subtle spatial acoustic design paired with collaborative jazz improvisation and marine diving"}
            ],
            "uncertainties_and_unknowns": ["Studio work schedule variability"]
        }
    },
    {
        "id": "part-demo-25",
        "name": "Sameer Khan",
        "age": 28,
        "gender": "Non-binary",
        "target_gender": "Any",
        "location": "Bengaluru, Karnataka",
        "linkedin_url": "https://www.linkedin.com/in/fictional-sameer-khan-climate",
        "instagram_url": "https://www.instagram.com/fictional_sameer_wild",
        "evidence": [
            {"platform": "linkedin", "category": "professional", "type": "explicit_statement", "quote": "Urban Ecology Researcher & Rewilding Consultant restoring native biodiversity corridors in South India.", "confidence": 1.0},
            {"platform": "linkedin", "category": "interest", "type": "explicit_statement", "quote": "Urban wildlife corridors, native flora micro-habitats, and participatory community conservation.", "confidence": 0.95},
            {"platform": "instagram", "category": "hobby", "type": "observed_activity", "quote": "Urban foraging & botanical walks in Lalbagh, hand-built ceramics, indie cooperative board games.", "confidence": 0.95},
            {"platform": "instagram", "category": "lifestyle", "type": "explicit_statement", "quote": "Eco-minimalist, daily bicycle commuter, community kitchen volunteer, loves monsoon scents.", "confidence": 0.95}
        ],
        "analyzed_profile": {
            "summary": "Thoughtful non-binary urban ecologist and rewilding consultant in Bengaluru dedicated to native urban biodiversity corridors, bicycle commuting, hand-built pottery, and communal living.",
            "career_interests": ["Urban Rewilding", "Ecological Restoration", "Community Conservation"],
            "demonstrated_hobbies": ["Botanical Foraging Walks", "Hand-Built Ceramics", "Cooperative Board Games"],
            "stated_interests": ["Urban Wildlife Corridors", "Indigenous Botany", "Speculative Climate Fiction"],
            "lifestyle_preferences": ["Daily bicycle commuter", "Eco-minimalist lifestyle", "Community kitchen volunteer"],
            "communication_preferences": ["Gentle, inclusive, and thoughtful", "Attentive and non-judgmental", "Authentic and compassionate"],
            "relationship_preferences": ["Kind, collaborative partner of any gender", "Grounded in empathy, shared social consciousness, and joy"],
            "explicit_facts": ["Urban ecology consultant in Bengaluru", "Bicycle commuter and community volunteer"],
            "inferences_with_confidence": [
                {"claim": "Compassionate, patient, and deeply community-oriented", "confidence": 0.95, "basis": "Rewilding public initiatives, cooperative gaming, and community volunteering"}
            ],
            "uncertainties_and_unknowns": ["Long-term willingness to own personal motor vehicles"]
        }
    }
]

def seed_database(db: Session = None, run_simulation: bool = True) -> Dict[str, Any]:
    """
    Safely and idempotently seed the 25 synthetic development fixtures into the database.
    Does not delete or overwrite real participant records.
    Returns summary statistics: {'created': X, 'existing': Y, 'total': 25}
    """
    should_close = False
    if db is None:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        should_close = True

    try:
        logger.info(f"Seeding {len(DEMO_PARTICIPANTS)} synthetic development fixtures...")
        
        created_count = 0
        existing_count = 0
        participant_objs = []

        for pdata in DEMO_PARTICIPANTS:
            # Idempotently check if participant already exists by id or normalized/raw unique urls
            _, norm_li, li_handle = validate_and_normalize_linkedin_url(pdata["linkedin_url"])
            _, norm_ig, ig_handle = validate_and_normalize_instagram_url(pdata["instagram_url"])

            p = db.query(Participant).filter(
                (Participant.id == pdata["id"]) |
                (Participant.linkedin_url == norm_li) |
                (Participant.instagram_url == norm_ig) |
                (Participant.linkedin_url == pdata["linkedin_url"]) |
                (Participant.instagram_url == pdata["instagram_url"])
            ).first()

            if not p:
                
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
                    status="analyzed",
                    analysis_status="analyzed"
                )
                db.add(p)
                db.commit()
                db.refresh(p)
                created_count += 1

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
            else:
                existing_count += 1
                if p.is_synthetic:
                    # Refresh existing synthetic demo fixture attributes with latest specification
                    _, norm_li, li_handle = validate_and_normalize_linkedin_url(pdata["linkedin_url"])
                    _, norm_ig, ig_handle = validate_and_normalize_instagram_url(pdata["instagram_url"])
                    p.name = pdata["name"]
                    p.age = pdata["age"]
                    p.gender = pdata["gender"]
                    p.target_gender = pdata["target_gender"]
                    p.location = pdata["location"]
                    p.linkedin_url = norm_li
                    p.linkedin_handle = li_handle
                    p.instagram_url = norm_ig
                    p.instagram_handle = ig_handle
                    p.consent_status = "consented"
                    p.consent_verified = False
                    p.source_verified = False
                    p.simulation_eligible = True
                    p.status = "analyzed"
                    p.analysis_status = "analyzed"

                    # Refresh evidence items
                    db.query(EvidenceItem).filter(EvidenceItem.participant_id == p.id).delete()
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

                    # Refresh analyzed profile
                    if "analyzed_profile" in pdata:
                        prof_data = pdata["analyzed_profile"]
                        if p.analyzed_profile:
                            ap = p.analyzed_profile
                            ap.summary = prof_data["summary"]
                            ap.career_interests = prof_data.get("career_interests", [])
                            ap.demonstrated_hobbies = prof_data.get("demonstrated_hobbies", [])
                            ap.stated_interests = prof_data.get("stated_interests", [])
                            ap.lifestyle_preferences = prof_data.get("lifestyle_preferences", [])
                            ap.communication_preferences = prof_data.get("communication_preferences", [])
                            ap.relationship_preferences = prof_data.get("relationship_preferences", [])
                            ap.explicit_facts = prof_data.get("explicit_facts", [])
                            ap.inferences_with_confidence = prof_data.get("inferences_with_confidence", [])
                            ap.uncertainties_and_unknowns = prof_data.get("uncertainties_and_unknowns", [])
                        else:
                            ap = AnalyzedProfile(
                                participant_id=p.id,
                                summary=prof_data["summary"],
                                career_interests=prof_data.get("career_interests", []),
                                demonstrated_hobbies=prof_data.get("demonstrated_hobbies", []),
                                stated_interests=prof_data.get("stated_interests", []),
                                lifestyle_preferences=prof_data.get("lifestyle_preferences", []),
                                communication_preferences=prof_data.get("communication_preferences", []),
                                relationship_preferences=prof_data.get("relationship_preferences", []),
                                explicit_facts=prof_data.get("explicit_facts", []),
                                inferences_with_confidence=prof_data.get("inferences_with_confidence", []),
                                uncertainties_and_unknowns=prof_data.get("uncertainties_and_unknowns", []),
                                model_version="synthetic-ground-truth",
                                analyzed_at=datetime.datetime.utcnow()
                            )
                            db.add(ap)
                    db.commit()

            # Populate analyzed profile if not already present
            if not p.analyzed_profile:
                if "analyzed_profile" in pdata:
                    prof_data = pdata["analyzed_profile"]
                    ap = AnalyzedProfile(
                        participant_id=p.id,
                        summary=prof_data["summary"],
                        career_interests=prof_data.get("career_interests", []),
                        demonstrated_hobbies=prof_data.get("demonstrated_hobbies", []),
                        stated_interests=prof_data.get("stated_interests", []),
                        lifestyle_preferences=prof_data.get("lifestyle_preferences", []),
                        communication_preferences=prof_data.get("communication_preferences", []),
                        relationship_preferences=prof_data.get("relationship_preferences", []),
                        explicit_facts=prof_data.get("explicit_facts", []),
                        inferences_with_confidence=prof_data.get("inferences_with_confidence", []),
                        uncertainties_and_unknowns=prof_data.get("uncertainties_and_unknowns", []),
                        model_version="synthetic-ground-truth",
                        analyzed_at=datetime.datetime.utcnow()
                    )
                    db.add(ap)
                    p.status = "analyzed"
                    p.analysis_status = "analyzed"
                    db.commit()
                    db.refresh(p)
                else:
                    analyze_participant_profile(db, p.id)

            participant_objs.append(p)

        logger.info(f"Processed {len(participant_objs)} participants (Created: {created_count}, Existing: {existing_count}).")

        # Initialize demonstration run record
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

        simulated_count = 0
        if run_simulation:
            logger.info("Executing representative dating sessions and calculating persistent rankings...")
            eligible_pairs = [p for p in pair_records if p.is_eligible]

            # Simulate up to 20 representative eligible pairs so rankings and live dates are populated
            for pair in eligible_pairs[:20]:
                if pair.pair_status not in ("completed", "skipped"):
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
            db.commit()
            logger.info("Demonstration benchmark seeding and simulations completed successfully.")

        return {
            "status": "success",
            "created_participants": created_count,
            "existing_participants": existing_count,
            "total_participants": len(participant_objs),
            "simulated_sessions": simulated_count,
            "run_id": run_id
        }

    finally:
        if should_close:
            db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    result = seed_database(run_simulation=True)
    print(json.dumps(result, indent=2))
