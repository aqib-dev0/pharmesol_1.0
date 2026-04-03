"""In-memory knowledge base for Pharmesol product information.
Simulates RAG retrieval. In production this would be a vector DB
with embedded chunks from product docs, case studies, and FAQs."""

# RAG LAYER (simulated)
# In production: chunks are embedded with OpenAI embeddings and stored in pgvector
# or Pinecone. Retrieval is semantic (cosine similarity) rather than keyword scoring.
# retrieve_relevant_chunks() has a production-compatible signature -- in production
# the internals swap keyword matching for an embedding lookup, nothing else changes.
# The knowledge base is updated when Pharmesol adds integrations, changes onboarding
# timelines, or publishes new case study results.

KNOWLEDGE_CHUNKS = [
    {
        "keywords": ["pharmesol", "jane", "ai agent", "what", "does", "who", "product"],
        "content": (
            "Pharmesol's AI agent, Jane, handles the phone work that pharmacy staff shouldn't "
            "have to do manually -- will-call pickups, refill reminders, after-hours coverage, "
            "and inbound patient calls. Jane sounds like a real person and works around the clock, "
            "so your team can focus on clinical work and patient care."
        ),
    },
    {
        "keywords": ["will-call", "pickup", "waiting", "shelf", "patient", "outreach", "notification"],
        "content": (
            "Jane automates will-call pickup outreach via phone, text, and email. "
            "She learns each patient's preferred contact method and time of day, so response "
            "rates improve over time. Pharmacies typically see will-call shelf clearance improve "
            "significantly within the first few weeks of going live."
        ),
    },
    {
        "keywords": ["refill", "refills", "automation", "after-hours", "hours", "coverage", "night"],
        "content": (
            "Pharmesol handles refill requests and inbound calls after hours without staff on duty. "
            "Jane takes refill requests, verifies patient identity, and queues them in your PMS "
            "for the morning team. No voicemails to sort through, no missed requests."
        ),
    },
    {
        "keywords": ["inbound", "outbound", "calls", "call", "phone", "answer", "volume", "handle"],
        "content": (
            "Jane handles both inbound and outbound call workflows. On the inbound side she "
            "answers patient questions, routes calls, and takes refill requests. On the outbound "
            "side she runs pickup reminders, refill nudges, and appointment confirmations -- all "
            "without tying up your staff."
        ),
    },
    {
        "keywords": ["pms", "integration", "pioneerrx", "wellsky", "liberty", "brighttree", "system"],
        "content": (
            "Pharmesol integrates directly with PioneerRx, WellSky, Liberty, and Brighttree. "
            "Jane reads and writes into your PMS in real time, so refill queues, patient records, "
            "and task modules stay in sync without any manual entry or double-keying."
        ),
    },
    {
        "keywords": ["phone", "system", "twilio", "lumistry", "spectrumvoip", "voip", "telephony"],
        "content": (
            "On the telephony side, Pharmesol connects with Twilio, Lumistry, and SpectrumVoIP. "
            "This means Jane can live inside your existing phone system -- no number porting "
            "required, no ripping out infrastructure you already have."
        ),
    },
    {
        "keywords": ["onboard", "onboarding", "setup", "go live", "start", "launch", "weeks", "timeline"],
        "content": (
            "Onboarding takes about four weeks from signed contract to go-live. "
            "The Pharmesol team handles the integration work -- you provide access to your PMS "
            "and phone system, and they do the rest. Most pharmacies are fully live within a month."
        ),
    },
    {
        "keywords": ["results", "outcomes", "metrics", "resolution", "payment", "rate", "hours", "saved", "roi"],
        "content": (
            "Pharmesol pharmacies see 85% of calls resolved by Jane without staff involvement. "
            "Payment rates improve by an average of 86% once pickup outreach is automated. "
            "Staff report saving 200+ hours per month -- time that goes back to patient care "
            "and clinical tasks."
        ),
    },
    {
        "keywords": ["hipaa", "compliance", "security", "soc2", "certified", "data", "private"],
        "content": (
            "Pharmesol is HIPAA-compliant and holds SOC 2 Type II certification. "
            "All patient data is encrypted in transit and at rest. Jane is designed from the "
            "ground up to operate within pharmacy compliance requirements, so you don't need "
            "a separate security review to get started."
        ),
    },
    {
        "keywords": ["high volume", "busy", "large", "prescriptions", "rx", "scale", "growing"],
        "content": (
            "For high-volume pharmacies filling hundreds or thousands of prescriptions a month, "
            "the ROI on Pharmesol tends to be immediate. The more calls and outreach tasks "
            "you have, the more Jane can take off your team's plate -- without adding headcount."
        ),
    },
    {
        "keywords": ["staff", "hiring", "headcount", "team", "capacity", "overloaded", "short-staffed"],
        "content": (
            "Pharmesol is not a replacement for pharmacy staff -- it handles the repetitive "
            "communication work so your pharmacists and techs can focus on what needs a human. "
            "Many pharmacy owners tell us they were considering hiring an extra tech; after "
            "going live with Pharmesol they didn't need to."
        ),
    },
    {
        "keywords": ["demo", "trial", "start", "next steps", "schedule", "callback", "see", "show", "pricing"],
        "content": (
            "The best next step is a live demo -- usually 20-30 minutes, no prep required. "
            "We'll show Jane handling real call scenarios with your pharmacy type in mind. "
            "If you want to move forward after that, onboarding can start within days. "
            "Would a demo this week or next work for you?"
        ),
    },
]


def get_chunk_keywords(chunks: list) -> str:
    """Returns topic labels for matched chunks. Used for terminal output only."""
    labels = []
    for chunk_content in chunks:
        for chunk in KNOWLEDGE_CHUNKS:
            if chunk["content"] == chunk_content:
                labels.append(chunk["keywords"][0])
                break
    return ", ".join(labels) if labels else "default chunks"


def retrieve_relevant_chunks(query: str, top_n: int = 3) -> list:
    """Return the top_n most relevant knowledge chunks for a given query.

    Scoring is simple keyword overlap -- each keyword that appears in the query
    adds one point to that chunk's score. In production this would be cosine
    similarity against embedded vectors.
    """
    query_lower = query.lower()
    scored = []
    for chunk in KNOWLEDGE_CHUNKS:
        score = sum(1 for kw in chunk["keywords"] if kw in query_lower)
        scored.append((score, chunk["content"]))

    scored.sort(key=lambda x: x[0], reverse=True)

    # If nothing matched, return the first 2 chunks as a safe default
    if scored[0][0] == 0:
        return [chunk["content"] for chunk in KNOWLEDGE_CHUNKS[:2]]

    return [content for _, content in scored[:top_n]]
