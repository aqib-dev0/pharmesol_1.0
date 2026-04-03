# SPEC.md
## Pharmesol Inbound Sales Agent -- Implementation Spec

---

## config.py

Module docstring: "Central configuration and constants for the Pharmesol sales agent."

Constants to define:
- OPENAI_API_KEY: the provided key as a string
- OPENAI_MODEL: "gpt-4o-mini"
- OPENAI_TEMPERATURE: 0.4
- OPENAI_MAX_TOKENS: 180
- PHARMACY_API_URL: "https://67e14fb758cc6bf785254550.mockapi.io/pharmacies"
- MOCK_CALLER_PHONE: "+1-555-123-4567"  -- HealthFirst Pharmacy, New York NY (real record in mockapi)
- EXIT_PHRASES: list of strings ["exit", "quit", "bye", "goodbye", "end call"]
- AGENT_NAME: "Aria"  -- the sales agent's name
- COMPANY_NAME: "Pharmesol"

No functions. Just constants.

---

## pharmacy_api.py

Module docstring: "Handles pharmacy identification via the Pharmesol mock API.
                   In production this would be a CRM lookup."

### fetch_all_pharmacies() -> list[dict]
- Makes a GET request to PHARMACY_API_URL
- Returns the list of pharmacy dicts on success
- Returns empty list on any exception (network error, timeout)
- Prints a warning if the API call fails

### identify_pharmacy(phone_number: str) -> dict | None
- Calls fetch_all_pharmacies()
- Strips spaces, dashes, and parentheses from both the input and each record phone before comparing
- Returns the raw pharmacy dict if found, None if not found

### get_pharmacy_display(pharmacy: dict) -> dict
- Takes the raw API dict and normalises it into a clean display dict
- The real API has inconsistent fields across records -- handle all of these:
  - name: always present
  - email: present but may be null -- treat null as None
  - city + state: present on real pharmacy records (ids 1-5)
  - address: present on test records instead of city/state
  - prescriptions: list of {drug: str, count: int} on real records
    -- sum all counts to get total rx_volume
  - rxVolume: flat integer on some test records
  - contactPerson: present on some records
- Returns a clean dict with these keys:
  - name: str
  - phone: str
  - email: str or None
  - location: str  -- city, state if available, else address, else unknown
  - rx_volume: int -- sum of prescription counts, or rxVolume field, or 0
  - contact_name: str -- contactPerson if present, else the team
- This is the dict passed everywhere else in the system -- never pass raw API dicts

### Real pharmacy data in the mockapi (use +1-555-123-4567 as MOCK_CALLER_PHONE):
- HealthFirst Pharmacy, New York NY -- Lisinopril 42 + Atorvastatin 38 + Metformin 20 = 100 rx total
- QuickMeds Rx, Los Angeles CA -- 100 rx total
- MediCare Plus, Chicago IL -- 57 rx total
- CityPharma, Houston TX -- 65 rx total
- Wellness Hub, Miami FL -- 55 rx total

---

## knowledge_base.py

Module docstring: "In-memory knowledge base for Pharmesol product information.
                   Simulates RAG retrieval. In production this would be a vector DB
                   with embedded chunks from product docs, case studies, and FAQs."

### KNOWLEDGE_CHUNKS: list[dict]

A list of at least 10 dicts. Each dict has:
- "keywords": list of strings (used for retrieval matching)
- "content": string (the actual knowledge, 2-4 sentences max per chunk)

Chunks must cover:
1. What Pharmesol does / Jane the AI agent
2. Will-call and pickup workflow automation
3. Refill automation and after-hours coverage
4. Inbound and outbound call handling
5. PMS integrations (PioneerRx, WellSky, Liberty, Brighttree)
6. Phone system integrations (Twilio, Lumistry, SpectrumVoIP)
7. Onboarding timeline (4 weeks to go live)
8. Outcomes / metrics (85% call resolution, 86% payment rate improvement, 200+ hours saved/month)
9. HIPAA compliance and SOC 2 Type II certification
10. High Rx volume pharmacies -- specific value prop
11. Staffing / capacity -- handling volume without new hires
12. Demo and getting started

### retrieve_relevant_chunks(query: str, top_n: int = 3) -> list[str]
- Lowercases the query
- Scores each chunk: count how many of its keywords appear in the query
- Returns the content strings of the top_n highest-scoring chunks
- If no chunk scores above 0, return the first 2 chunks as defaults
  (so the agent always has some context)

---

## tools.py

Module docstring: "Mock follow-up tools for the Pharmesol sales agent.
                   In production these would integrate with SendGrid (email)
                   and Google Calendar / Calendly (scheduling).
                   For this simulation they log to stdout."

### mock_send_followup_email(pharmacy_name: str, contact_name: str, email: str, summary: str) -> dict
- Prints a formatted block showing what would be sent
- Returns a dict: {"status": "sent", "to": email, "pharmacy": pharmacy_name}

### mock_schedule_callback(pharmacy_name: str, contact_name: str, preferred_time: str, notes: str) -> dict
- Prints a formatted block showing what would be scheduled
- Returns a dict: {"status": "scheduled", "pharmacy": pharmacy_name, "time": preferred_time}

### mock_log_lead(pharmacy_name: str, rx_volume: str, pain_points: str, outcome: str) -> dict
- Prints a formatted block showing what would be logged to CRM
- Returns a dict: {"status": "logged", "pharmacy": pharmacy_name}

All three functions should have clear docstrings explaining what the production
version would do.

---

## agent.py

Module docstring: "Core agent logic: prompt assembly, LLM calls, and conversation management
                   for the Pharmesol inbound sales agent."

### build_system_prompt(pharmacy: dict | None, knowledge_chunks: list[str]) -> str
- Assembles the full system prompt as a single string
- Structure of the prompt:
  1. Role definition: Aria, a warm and knowledgeable Pharmesol sales agent.
     Not a chatbot. Speaks like a real person on a phone call.
  2. Hard rules (numbered list in the prompt):
     - Never fabricate pricing, timelines, or features not in the knowledge base
     - Never make clinical claims
     - If asked something out of scope, acknowledge and redirect
     - Keep responses concise -- this is a phone call, not an essay
     - Always steer toward booking a demo or scheduling a callback
     - Mention the pharmacy name naturally when known
  3. Pharmacy context block:
     - If pharmacy is not None: inject name, location, rxVolume, pmsSystem
     - If pharmacy is None: note that pharmacy is unidentified, collect details conversationally
  4. Product knowledge block:
     - Inject the knowledge_chunks as a numbered list under "What you know about Pharmesol:"
- Returns the full prompt string

### get_llm_response(messages: list[dict]) -> str
- Initializes the OpenAI client with OPENAI_API_KEY
- Calls client.chat.completions.create() with the messages array
- Uses OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_MAX_TOKENS from config
- Returns the response content string
- On exception: prints the error and returns a safe fallback string:
  "I'm sorry, I didn't catch that -- could you say that again?"

### extract_conversation_context(messages: list[dict]) -> dict
- Scans the conversation history (assistant and user messages)
- Tries to extract: pharmacy_name, rx_volume, pain_points, contact_name
- Uses simple string search / heuristics -- no LLM call
- Returns a dict with whatever it could find (values default to "unknown")
- This is used by tools.py when the call ends

---

## main.py

Module docstring: "Entry point for the Pharmesol inbound sales agent simulation.
                   Simulates an inbound phone call from a pharmacy operator."

### run_agent()
Main function. Implements this flow:

1. Print a startup banner:
   "Pharmesol Inbound Sales Agent -- Simulation"
   "Simulating inbound call from: {MOCK_CALLER_PHONE}"
   "---"

2. Call identify_pharmacy(MOCK_CALLER_PHONE)
   - Print whether the pharmacy was identified or not

3. Build the opening message:
   - If pharmacy identified: "Hi {pharmacy['name']}, this is Aria from Pharmesol..."
     referencing their location and Rx volume
   - If not: "Hi, thanks for calling Pharmesol, this is Aria..."

4. Initialize messages list with:
   - system message: build_system_prompt(pharmacy, initial_chunks)
   - assistant message: the opening message

5. Print the opening message as the agent's first turn

6. Enter while True loop:
   a. input("You: ")
   b. If user input stripped is empty: continue
   c. If user input lowercased is in EXIT_PHRASES: break
   d. Retrieve knowledge chunks relevant to the user's message
   e. Rebuild system prompt with updated chunks (so context stays fresh)
      -- replace messages[0] with the new system prompt
   f. Append user message to messages
   g. Call get_llm_response(messages)
   h. Append assistant response to messages
   i. Print "Aria: {response}"

7. After loop exits (call ended):
   - Print "--- Call ended ---"
   - Call extract_conversation_context(messages)
   - Call mock_log_lead() with extracted context
   - Call mock_send_followup_email() with extracted context
   - Call mock_schedule_callback() with extracted context
   - Print "--- Simulation complete ---"

### if __name__ == "__main__": call run_agent()

---

## README.md

Must include:

### Setup
```bash
pip install openai requests
python main.py
```

### Assumptions
- Numbered list of 5-7 explicit assumptions made during implementation
- Must reference the design doc decisions (natural conversation flow,
  in-memory RAG, state-scoped behavior)

### Architecture notes
- Brief paragraph on each file and why it exists
- Note that knowledge_base.py simulates what would be a vector DB in production
- Note that tools.py simulates what would be SendGrid + Calendly in production

### If I had 3 more hours
This must be a thoughtful answer, not a list of features. Cover:
1. Voice layer -- Twilio + Deepgram STT + ElevenLabs TTS
2. Real RAG -- embed knowledge chunks with OpenAI embeddings, store in pgvector
3. Lakera Guard integration for prompt injection protection on caller input
4. CRM write-back -- real HubSpot API call after each call
5. Evaluation loop -- log every conversation turn and score agent responses
   for hallucination, goal completion, and naturalness
