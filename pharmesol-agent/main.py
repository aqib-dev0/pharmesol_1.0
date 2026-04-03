"""Entry point for the Pharmesol inbound sales agent simulation.
Simulates an inbound phone call from a pharmacy operator."""

from config import MOCK_CALLER_PHONE, EXIT_PHRASES, AGENT_NAME, COMPANY_NAME
from pharmacy_api import identify_pharmacy, get_pharmacy_display
from knowledge_base import (
    retrieve_relevant_chunks, get_chunk_keywords,
    vector_search_prior_context, store_transcript_chunks,
)
from agent import (
    build_system_prompt, get_llm_response, extract_conversation_context,
    detect_abuse_patterns, detect_out_of_scope,
    track_conversation_goals, detect_call_outcome,
)
from tools import mock_log_lead, mock_send_followup_email, mock_schedule_callback, mock_escalate_to_human

SAFE_FALLBACK = (
    "I appreciate you reaching out! I'm here to help pharmacy teams learn about Pharmesol. "
    "Is there something I can help you with today?"
)


def _format_goals(goals: dict) -> str:
    """Format the goals dict as a compact status line for terminal output."""
    icons = {k: "✓" if v else "✗" for k, v in goals.items()}
    remaining = sum(1 for v in goals.values() if not v)
    parts = "  ".join(f"{k}={icons[k]}" for k in goals)
    return f"{parts}  — {5 - remaining}/5 gathered"


def run_agent():
    """Run the inbound sales agent simulation from start to finish."""

    # ── Startup banner ──────────────────────────────────────────────────────
    print(f"{COMPANY_NAME} Inbound Sales Agent -- Simulation")
    print(f"Simulating inbound call from: {MOCK_CALLER_PHONE}")
    print("---")

    # ── Step 1: Structured memory (CRM lookup) ───────────────────────────────
    # identify_pharmacy() prints [CRM Lookup] itself
    raw_pharmacy = identify_pharmacy(MOCK_CALLER_PHONE)
    if raw_pharmacy:
        pharmacy = get_pharmacy_display(raw_pharmacy)
        print(f"Pharmacy identified: {pharmacy['name']} ({pharmacy['location']})")
    else:
        pharmacy = None
        print("Pharmacy not found in system -- agent will collect details conversationally.")

    # ── Step 2: Vector memory (prior call transcripts) ───────────────────────
    print(f"[Vector DB] searching prior call transcripts for {MOCK_CALLER_PHONE}...", end=" ", flush=True)
    prior_chunks = vector_search_prior_context(MOCK_CALLER_PHONE)
    if prior_chunks:
        print(f"{len(prior_chunks)} chunk(s) found — prior context loaded")
    else:
        print("0 chunk(s) found (first call)")

    # ── Step 3: Merge structured + vector context ────────────────────────────
    print("[Memory] merging structured CRM data + vector context into system prompt...")
    if pharmacy:
        print(f"[Memory] CRM → name={pharmacy['name']} | location={pharmacy['location']} | rx_volume={pharmacy['rx_volume']}/month")
    else:
        print("[Memory] CRM → no record found | will collect identity conversationally")
    if prior_chunks:
        print(f"[Memory] Vector → {len(prior_chunks)} prior transcript chunk(s) available")
    else:
        print("[Memory] Vector → no prior transcript context")
    print()

    # ── Build opening message ────────────────────────────────────────────────
    if pharmacy:
        opening = (
            f"Hey, {pharmacy['name']}! This is {AGENT_NAME} from {COMPANY_NAME} -- "
            f"thanks for calling in. What can I help you with today?"
        )
    else:
        opening = (
            f"Hi, thanks for calling {COMPANY_NAME}, this is {AGENT_NAME}. "
            "Could I start by getting your pharmacy's name and roughly how many "
            "prescriptions you're filling each month?"
        )

    initial_chunks = retrieve_relevant_chunks(pharmacy["name"] if pharmacy else "pharmacy sales")
    messages = [
        {"role": "system", "content": build_system_prompt(pharmacy, initial_chunks)},
        {"role": "assistant", "content": opening},
    ]

    print(f"{AGENT_NAME}: {opening}\n")

    # ── Conversation loop ────────────────────────────────────────────────────
    turn = 0
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue
        if user_input.lower() in EXIT_PHRASES:
            break

        turn += 1

        # ── Layer 1: Lakera Guard (prompt injection detection) ────────────────
        flag = detect_abuse_patterns(user_input)
        if flag:
            print(f"[Lakera Guard] scanning input for prompt injection... FLAGGED — '{flag}'")
            print(f"[Safety] safe fallback triggered — LLM call bypassed")
            print(f"\n{AGENT_NAME}: {SAFE_FALLBACK}\n")
            messages.append({"role": "user", "content": user_input})
            messages.append({"role": "assistant", "content": SAFE_FALLBACK})
            continue
        print(f"[Lakera Guard] scanning input for prompt injection... clear")

        # ── Layer 2: Out-of-scope detection ──────────────────────────────────
        oos = detect_out_of_scope(user_input)
        if oos:
            print(f"[Safety] out-of-scope topic detected: {oos} — agent will redirect gracefully")

        # ── RAG: retrieve relevant product knowledge ─────────────────────────
        print(f"[RAG] retrieving relevant knowledge chunks for query...")
        fresh_chunks = retrieve_relevant_chunks(user_input)
        labels = get_chunk_keywords(fresh_chunks)
        print(f"[RAG] {len(fresh_chunks)} chunk(s) matched: {labels}")

        # ── Goals: track what's been gathered so far ─────────────────────────
        goals = track_conversation_goals(messages)
        print(f"[Goals] {_format_goals(goals)}")

        # ── Assemble prompt + call LLM ────────────────────────────────────────
        # build_system_prompt prints [Prompt]; get_llm_response prints [LLM]
        messages[0] = {"role": "system", "content": build_system_prompt(pharmacy, fresh_chunks)}
        messages.append({"role": "user", "content": user_input})
        response = get_llm_response(messages)
        messages.append({"role": "assistant", "content": response})

        # ── Short-term memory: session state ─────────────────────────────────
        print(f"[Short-term] session memory: {len(messages)} messages (turn {turn})")

        print(f"\n{AGENT_NAME}: {response}\n")

    # ── Call ended ────────────────────────────────────────────────────────────
    print("\n--- Call ended ---\n")

    # ── Outcome detection ─────────────────────────────────────────────────────
    print("[Outcome] analyzing conversation transcript...", end=" ", flush=True)
    outcome = detect_call_outcome(messages)
    print(f"detected: {outcome}")

    ctx = extract_conversation_context(messages)
    if pharmacy:
        ctx["pharmacy_name"] = pharmacy["name"]
        ctx["contact_name"]  = pharmacy["contact_name"]
        email = pharmacy.get("email") or "unknown@pharmacy.com"
        rx = str(pharmacy["rx_volume"]) + "/month"
    else:
        email = "unknown@pharmacy.com"
        rx = ctx["rx_volume"]

    # ── CRM write-back (structured memory update) ─────────────────────────────
    print(f"[CRM Write] updating lead record: {ctx['pharmacy_name']}")
    print(f"  rx_volume={rx} | pms={ctx.get('pms', 'unknown')} | pain_points={ctx['pain_points']} | outcome={outcome}")

    if outcome == "graceful escalation":
        mock_escalate_to_human(ctx["pharmacy_name"], ctx["contact_name"], notes=ctx["pain_points"])
    else:
        mock_log_lead(ctx["pharmacy_name"], rx, ctx["pain_points"], outcome)
        mock_send_followup_email(
            ctx["pharmacy_name"], ctx["contact_name"], email,
            summary=f"Discussed {ctx['pain_points']}. Outcome: {outcome}.",
        )
        mock_schedule_callback(
            ctx["pharmacy_name"], ctx["contact_name"],
            preferred_time="to be confirmed",
            notes=f"Rx volume: {rx}. PMS: {ctx.get('pms','unknown')}. Pain points: {ctx['pain_points']}.",
        )

    # ── Vector DB write-back (long-term memory update) ────────────────────────
    print(f"[Vector DB] chunking call transcript ({len(messages)} messages)...", end=" ", flush=True)
    n_chunks = store_transcript_chunks(MOCK_CALLER_PHONE, messages)
    print(f"{n_chunks} chunk(s) embedded and stored")
    print(f"[Long-term] {ctx['pharmacy_name']} context persisted — next call will load prior transcript context")

    print("\n--- Simulation complete ---")


if __name__ == "__main__":
    run_agent()
