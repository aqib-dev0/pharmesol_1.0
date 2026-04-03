# PROGRESS.md
## Build progress tracker -- update this file as you complete each item

---

## Status: COMPLETE (iteration 2 -- terminal visibility + production annotations added)

---

## Files

| File | Status | Notes |
|------|--------|-------|
| config.py | [x] done | All constants, placeholder API key |
| pharmacy_api.py | [x] done | Handles field normalization for inconsistent API |
| knowledge_base.py | [x] done | 12 chunks, keyword retrieval with defaults |
| tools.py | [x] done | 3 mock tools with production docstrings |
| agent.py | [x] done | Prompt assembly, LLM call, context extraction |
| main.py | [x] done | Full conversation loop with clean exit handling |
| README.md | [x] done | Setup, assumptions, architecture, 3-more-hours |

---

## Checklist

### config.py
- [x] All constants defined
- [x] MOCK_CALLER_PHONE set to a number that exists in the mockapi
- [x] Module docstring present

### pharmacy_api.py
- [x] fetch_all_pharmacies() works and returns list
- [x] identify_pharmacy() matches on phone number flexibly
- [x] Handles API failure gracefully (returns None, does not crash)
- [x] Tested against the live mockapi URL

### knowledge_base.py
- [x] At least 10 chunks covering all topics in spec (12 chunks)
- [x] retrieve_relevant_chunks() returns relevant content for test queries
- [x] Defaults to first 2 chunks when no keyword match found
- [x] Each chunk is 2-4 sentences, not a wall of text

### tools.py
- [x] mock_send_followup_email() prints formatted output and returns dict
- [x] mock_schedule_callback() prints formatted output and returns dict
- [x] mock_log_lead() prints formatted output and returns dict
- [x] All functions have docstrings explaining production equivalent

### agent.py
- [x] build_system_prompt() assembles all 4 sections correctly
- [x] Pharmacy context injected correctly when found
- [x] Pharmacy context handles None (unknown caller) correctly
- [x] Knowledge chunks injected as numbered list
- [x] get_llm_response() calls OpenAI correctly
- [x] get_llm_response() handles exceptions with safe fallback
- [x] extract_conversation_context() scans history and returns dict

### main.py
- [x] Startup banner prints correctly
- [x] Pharmacy identified on startup (or not, handled gracefully)
- [x] Opening message references pharmacy name and Rx volume if known
- [x] Conversation loop runs correctly
- [x] Knowledge chunks refreshed on each turn
- [x] EXIT_PHRASES trigger clean shutdown
- [x] Follow-up tools called on exit
- [x] No crashes on empty input

### README.md
- [x] Setup instructions are accurate and minimal
- [x] Assumptions are explicit and numbered
- [x] "3 more hours" answer is substantive (not just a feature list)

---

## Known issues / blockers

None.

---

## Decisions made during implementation

- System prompt rebuilt on each turn (not just once) so knowledge chunks stay relevant to the current topic.
- `get_pharmacy_display()` absorbs all API field inconsistencies; nothing outside pharmacy_api.py ever sees a raw API dict.
- `extract_conversation_context()` uses regex heuristics, no extra LLM call -- keeps end-of-call cleanup fast.
- 12 knowledge chunks (spec said "at least 10") -- the extra two cover staffing/capacity and demo/next steps, both critical for a sales agent.
- `import re` inside `extract_conversation_context()` -- only needed there, avoids a top-level import for a single use.
