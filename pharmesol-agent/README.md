# Pharmesol Inbound Sales Agent

A text-based simulation of an AI phone agent for Pharmesol's inbound pharmacy sales calls.

---

## Setup

```bash
pip install openai requests
python main.py
```

Add your OpenAI API key to `config.py` before running:
```python
OPENAI_API_KEY = "sk-..."
```

---

## Assumptions

1. **Phone number matching is the entry point.** The simulation assumes callers are identified by their inbound phone number, which maps to a CRM/API record. This mirrors how real IVR systems work -- the phone number is the first signal the agent has.

2. **Conversation state lives in memory for the session only.** There is no persistence between runs. Each `python main.py` is a fresh call. This was an explicit constraint in the brief and the right call for a simulation.

3. **Knowledge retrieval is keyword-based, not semantic.** The spec called for simple keyword matching rather than embeddings. The implementation scores chunks by keyword overlap and returns the top matches. The design deliberately mirrors what a vector DB would do so the swap is obvious.

4. **The system prompt is rebuilt on each turn.** Rather than injecting all knowledge upfront, the relevant chunks are re-selected based on the caller's latest message. This keeps the context window tight and ensures the most relevant product information is always in scope.

5. **The LLM response is authoritative for conversation flow.** The agent doesn't try to hard-code specific responses to specific questions. The system prompt + knowledge chunks constrain the model's output; the model handles phrasing. This is how a real production agent would work.

6. **Mock tools fire unconditionally on exit.** In production, tool calls would depend on what was collected during the call. Here they always fire with whatever context was extractable -- this keeps the demo path clean and shows the full system working end-to-end.

7. **The mockapi is treated as read-only.** Pharmacy records are fetched on startup and not cached between runs. Network failures degrade gracefully -- the agent still runs, it just can't identify the caller.

---

## Architecture Notes

**`config.py`** — Single source of truth for all constants. Nothing is a magic string in any other file. If a value needs to change, it changes here.

**`pharmacy_api.py`** — Handles the external API call and the normalization of raw API data. In production, this would be a CRM or CDP lookup. The `get_pharmacy_display()` function exists specifically to absorb the API's inconsistent field names so the rest of the codebase only ever sees clean, predictable dicts.

**`knowledge_base.py`** — Simulates what would be a vector database in production. The `KNOWLEDGE_CHUNKS` list is what would be embedded and stored in pgvector or Pinecone. The `retrieve_relevant_chunks()` function is what would be a cosine similarity search. The structure is intentionally written to make this swap obvious.

**`tools.py`** — Simulates what would be SendGrid (email), Google Calendar/Calendly (scheduling), and HubSpot (CRM write-back) in production. Each function has the correct signature and docstring for a real integration. They print instead of send.

**`agent.py`** — The core LLM interface. `build_system_prompt()` assembles the full context the model needs: role, rules, caller info, and relevant knowledge. `get_llm_response()` is a thin wrapper that handles the API call and failure gracefully. `extract_conversation_context()` does post-call analysis on the transcript.

**`main.py`** — The conversation loop. Readable in two minutes. Calls the other modules in the right order and doesn't contain any logic that belongs elsewhere.

---

## Connection to design document

- `knowledge_base.py` is the RAG layer from the design document. In production this
  is semantic retrieval over embedded product docs stored in pgvector. The function
  signature of `retrieve_relevant_chunks()` is intentionally production-compatible.

- `pharmacy_api.py` simulates the CRM lookup that fires on call start. In production
  this is a HubSpot or Salesforce lookup returning the full lead record including
  funnel stage and previous interaction notes.

- `tools.py` `mock_log_lead()` simulates CRM write-back after each call. This closes
  the context loop -- future calls benefit from accumulated lead history.

- Lakera Guard sits between caller input and the LLM. In production every caller
  utterance passes through Lakera before the LLM sees it, catching prompt injection
  attempts from adversarial callers.

- The two-memory-layer design (CRM for structured data + vector DB for past transcript
  context) is partially implemented: CRM lookup is live, vector DB retrieval is noted
  in `knowledge_base.py` as the production path.

---

## If I had 3 more hours

The single most impactful addition would be the voice layer. This is a text simulation, but Pharmesol is a phone product — the actual value proposition lives in how the agent sounds and responds in real time. The path is well-defined: connect Twilio's Programmable Voice to receive the inbound call, stream audio to Deepgram for real-time STT, pass the transcript through the existing agent logic unchanged, then send the response to ElevenLabs for synthesis and play it back via Twilio. Critically, `main.py`'s conversation loop barely changes — the voice layer is pure I/O wrapping the same prompt assembly and LLM call that already works. This is an afternoon of work that turns a demo into a shippable product.

The second thing is replacing keyword matching with real semantic retrieval. The structure in `knowledge_base.py` is already production-compatible — `retrieve_relevant_chunks()` has a signature designed for exactly this swap. The change is: embed each chunk once with `text-embedding-3-small` at startup, store vectors in pgvector, and replace the scoring loop with a cosine similarity query. This matters because keyword matching breaks the moment a caller uses different language for the same concept — "we're stretched thin" doesn't match "staffing" the way a similarity search would. The retrieval quality improvement directly affects how relevant Aria's answers are.

Third, I'd replace `detect_abuse_patterns()` with a real Lakera Guard API call. The current implementation is keyword-based — it catches obvious patterns but misses anything more subtle. Lakera's ML model is trained specifically on adversarial prompt injection, including paraphrased attempts that no keyword list would catch. The swap is literally one function call: replace the loop in `agent.py` with `lakera_client.moderate(user_input)`. Given that this is a publicly listed phone number that will receive calls from people who have no intent to buy, this is a non-negotiable upgrade before any real traffic.

Finally, I'd add an evaluation loop. Right now there is no way to know if the agent is actually working — whether it's hallucinating features, failing to move calls toward a demo, or sounding unnatural in ways that cause callers to hang up. The fix is to log every conversation turn to a structured store after the call, then run an async scoring pass that checks three things: did the agent claim anything not in the knowledge base (hallucination), did the call move toward a concrete next step (goal completion), and did the responses sound like a real person rather than a script (naturalness score via a second LLM call). Without this loop running on real calls, every other improvement is a guess.
