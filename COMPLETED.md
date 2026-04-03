# COMPLETED.md
## Definition of done for this task

This file describes what the finished implementation must look like.
Use this to verify the build is actually complete before submitting.

---

## The repo must contain exactly these files

```
pharmesol-agent/
  main.py
  agent.py
  pharmacy_api.py
  knowledge_base.py
  tools.py
  config.py
  README.md
  PROGRESS.md
  COMPLETED.md
  CLAUDE.md
  SPEC.md
```

No extra files. No __pycache__. No .env. No requirements.txt needed
(setup is just pip install openai requests).

---

## It must run with one command

```bash
python main.py
```

No setup steps beyond pip install. No configuration. No environment variables.
The API key is in config.py. The mock phone number is in config.py.

---

## The conversation must demonstrate all of these in a single run

1. Startup identifies the pharmacy from the mock API
2. Opening message greets by pharmacy name and references their Rx volume
3. A question about Pharmesol features gets a grounded answer (not hallucinated)
4. A question out of scope gets acknowledged and redirected gracefully
5. Typing "bye" ends the call cleanly
6. All three mock tools fire and print their output
7. No Python exceptions at any point

---

## Code quality checks

- [ ] Every file has a module-level docstring
- [ ] Every function has a docstring
- [ ] No function is longer than 40 lines
- [ ] No file is longer than 150 lines
- [ ] No magic strings outside config.py
- [ ] No bare except clauses (catch specific exceptions)
- [ ] The system prompt in agent.py reads like something a real engineer wrote,
      not a list of rules pasted from a requirements doc

---

## The README written questions section must answer

"If you had 3 more hours, what would you do?"

The answer must:
- Be specific, not generic
- Reference the design document decisions (voice layer, real RAG, Lakera Guard)
- Explain WHY each addition matters, not just what it is
- Be 200-300 words, not a bullet list

---

## What good output looks like during a run

```
Pharmesol Inbound Sales Agent -- Simulation
Simulating inbound call from: +1-555-847-2210
Pharmacy identified: Sunrise Pharmacy (Chicago, IL)
---

Aria: Hi, is this the team at Sunrise Pharmacy? This is Aria calling from
Pharmesol. I can see you're filling around 3,200 prescriptions a month --
quite a volume. What's bringing you to us today?

You: We're having a hard time with will-call pickups, patients just aren't
responding to our outreach

Aria: That's one of the most common things we hear from high-volume pharmacies.
Pharmesol's AI agent handles outreach across phone, text, and email automatically
-- and it learns when your specific patients actually respond. Pharmacies your
size typically see pickup rates improve significantly within the first month.
Would it be worth a quick demo to see how it works with your setup?

You: Do you integrate with PioneerRx?

Aria: Yes, we integrate directly with PioneerRx. The agent reads and writes
into your PMS in real time -- so things like refill queues, patient records,
and task modules all stay in sync without manual entry.

You: bye

--- Call ended ---

[LEAD LOGGED]
  Pharmacy: Sunrise Pharmacy
  Rx Volume: 3200/month
  Pain points: will-call pickups, patient outreach
  Outcome: demo interest expressed

[EMAIL QUEUED]
  To: follow-up@sunrisepharmacy.com
  Subject: Great speaking with you -- Pharmesol next steps
  Summary: Discussed will-call automation and PioneerRx integration...

[CALLBACK SCHEDULED]
  Pharmacy: Sunrise Pharmacy
  Preferred time: to be confirmed
  Notes: High Rx volume, PioneerRx, interested in will-call workflow

--- Simulation complete ---
```

---

## What to do if the mockapi returns no matching pharmacy

The simulation should still work. The agent greets generically and
collects pharmacy name and Rx volume through conversation. Change
MOCK_CALLER_PHONE in config.py to a number not in the API to test this path.

---

## What NOT to include

- No unit tests
- No type annotations everywhere (only where genuinely helpful)
- No logging module configuration
- No argparse or CLI flags
- No streaming responses
- No retry logic on the OpenAI call (one attempt, safe fallback on failure)
- No conversation persistence between runs
