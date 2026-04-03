# CLAUDE.md

## How to run

```bash
# 1. Install dependencies (one time)
pip install openai requests

# 2. Set your OpenAI API key
export OPENAI_API_KEY="sk-..."

# 3. Run the agent
cd pharmesol-agent
python main.py
```

## How to test different paths

```bash
# Test identified caller (HealthFirst Pharmacy, New York NY)
# MOCK_CALLER_PHONE is already set to +1-555-123-4567 in config.py -- just run it.
python main.py

# Test unidentified caller (no match in mockapi)
# Edit config.py: MOCK_CALLER_PHONE = "+1-000-000-0000"
python main.py

# Scripted run (no interactive input needed)
printf "Tell me about refill automation\nDo you integrate with PioneerRx?\nbye\n" | python main.py

# Test out-of-scope handling
printf "What is the clinical dosage for metformin?\nbye\n" | python main.py
```

---

## What this project is

A text-based simulation of an inbound pharmacy sales agent for Pharmesol.
This is a take-home interview task. The brief explicitly says: focus on clarity,
structure, and core behavior -- not completeness or production readiness.

Do not over-engineer. No web framework, no database, no async. Keep it simple.

---

## Project structure to build

```
pharmesol-agent/
  main.py             # entry point and conversation loop
  agent.py            # LLM calls and prompt assembly
  pharmacy_api.py     # mockapi lookup by phone number
  knowledge_base.py   # in-memory RAG -- Pharmesol product knowledge
  tools.py            # mock follow-up tools (email, callback)
  config.py           # constants and configuration
  README.md           # setup instructions and written questions
```

---

## Constraints -- read before writing any code

- Python only. No web framework. No database. No async/await.
- Use the OpenAI Python SDK (openai>=1.0.0). Model: gpt-4o-mini.
- Conversation loop is a simple while True with input(). Nothing fancier.
- The knowledge base is a plain Python list of dicts in knowledge_base.py. No vector DB.
- Mock tools just print/log. They have proper signatures and docstrings but do nothing real.
- No .env file needed -- API key goes in config.py as a constant (this is an interview task, not production).
- All files must have a module-level docstring explaining what the file does.
- Functions must have docstrings.
- Keep each file under 150 lines. If a file is getting long, something is wrong.

---

## Behavior spec

### On call start
1. Look up the caller phone number against the mockapi (pharmacy_api.py).
2. If found: greet by pharmacy name, reference their location and Rx volume.
3. If not found: greet generically, collect pharmacy name and Rx volume conversationally.

### During conversation
- Mention the pharmacy name naturally throughout when known.
- Highlight Pharmesol value props that match the caller's Rx volume.
- If caller asks something out of scope (clinical questions, competitor pricing,
  anything Pharmesol does not do): respond safely, acknowledge the question,
  redirect without hallucinating an answer.
- Keep the conversation moving toward booking a demo or scheduling a callback.

### Ending the call
- When user types "exit", "quit", "bye", or "goodbye": trigger follow-up tools.
- Call mock_send_followup_email() and mock_schedule_callback() with relevant details.
- Print a clean summary of what was logged.

---

## LLM / prompt rules

- System prompt must be assembled in agent.py in a dedicated function: build_system_prompt().
- System prompt injects: pharmacy context (from API lookup) + relevant knowledge base chunks.
- Knowledge base retrieval is simple keyword matching -- no embeddings needed.
  Match caller message against chunk keywords, return top 2-3 chunks.
- Full conversation history is passed to the LLM on every turn (OpenAI messages array).
- Temperature: 0.4. Low enough to be consistent, high enough to sound natural.
- Max tokens per response: 180. Agent should be concise -- this is a phone call simulation.

---

## What good code looks like here

- A teammate should be able to read main.py and understand the whole system in 2 minutes.
- agent.py should make it obvious how the prompt is assembled and why.
- knowledge_base.py should make it obvious how RAG would work in production even though
  this is in-memory.
- tools.py should look like real tools that just happen to print instead of send.
- No magic strings scattered across files -- all constants in config.py.

---

## Do not do these things

- Do not add Flask, FastAPI, or any web framework.
- Do not add a database or any file-based persistence.
- Do not use async/await.
- Do not add tests (out of scope for a 2-hour task).
- Do not add type hints everywhere -- only where they genuinely help readability.
- Do not add logging configuration -- print() is fine for a simulation.
- Do not install more than: openai, requests. That is all that is needed.
- Do not create more files than listed in the project structure above.
