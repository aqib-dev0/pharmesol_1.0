"""Entry point for the Pharmesol inbound sales agent simulation.
Simulates an inbound phone call from a pharmacy operator."""

from config import MOCK_CALLER_PHONE, EXIT_PHRASES, AGENT_NAME, COMPANY_NAME
from pharmacy_api import identify_pharmacy, get_pharmacy_display
from knowledge_base import retrieve_relevant_chunks, get_chunk_keywords
from agent import build_system_prompt, get_llm_response, extract_conversation_context
from tools import mock_log_lead, mock_send_followup_email, mock_schedule_callback


def run_agent():
    """Run the inbound sales agent simulation from start to finish."""

    # Startup banner
    print(f"{COMPANY_NAME} Inbound Sales Agent -- Simulation")
    print(f"Simulating inbound call from: {MOCK_CALLER_PHONE}")
    print("---")

    # Identify the caller
    raw_pharmacy = identify_pharmacy(MOCK_CALLER_PHONE)
    if raw_pharmacy:
        pharmacy = get_pharmacy_display(raw_pharmacy)
        print(f"Pharmacy identified: {pharmacy['name']} ({pharmacy['location']})")
    else:
        pharmacy = None
        print("Pharmacy not found in system -- agent will collect details conversationally.")
    print()

    # Build opening message
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

    # Get initial knowledge chunks for the system prompt
    initial_query = pharmacy["name"] if pharmacy else "pharmacy sales"
    initial_chunks = retrieve_relevant_chunks(initial_query)

    # Initialize conversation with system prompt and opening message
    messages = [
        {"role": "system", "content": build_system_prompt(pharmacy, initial_chunks)},
        {"role": "assistant", "content": opening},
    ]

    print(f"{AGENT_NAME}: {opening}")
    print()

    # Conversation loop
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue

        if user_input.lower() in EXIT_PHRASES:
            break

        print(f"[Lakera Guard] scanning input for prompt injection... clear")

        # Refresh knowledge chunks based on what the caller just said
        print(f"[RAG] retrieving relevant knowledge chunks for query...")
        fresh_chunks = retrieve_relevant_chunks(user_input)
        labels = get_chunk_keywords(fresh_chunks)
        print(f"[RAG] {len(fresh_chunks)} chunk(s) matched: {labels}")

        # build_system_prompt prints [Prompt]; get_llm_response prints [LLM]
        messages[0] = {"role": "system", "content": build_system_prompt(pharmacy, fresh_chunks)}

        messages.append({"role": "user", "content": user_input})
        response = get_llm_response(messages)
        messages.append({"role": "assistant", "content": response})

        print(f"\n{AGENT_NAME}: {response}\n")

    # Call ended -- fire follow-up tools
    print("\n--- Call ended ---\n")

    ctx = extract_conversation_context(messages)
    if pharmacy:
        ctx["pharmacy_name"] = pharmacy["name"]
        ctx["contact_name"] = pharmacy["contact_name"]
        email = pharmacy.get("email") or "unknown@pharmacy.com"
        rx = str(pharmacy["rx_volume"]) + "/month"
    else:
        email = "unknown@pharmacy.com"
        rx = ctx["rx_volume"]

    mock_log_lead(
        pharmacy_name=ctx["pharmacy_name"],
        rx_volume=rx,
        pain_points=ctx["pain_points"],
        outcome="demo interest expressed",
    )
    mock_send_followup_email(
        pharmacy_name=ctx["pharmacy_name"],
        contact_name=ctx["contact_name"],
        email=email,
        summary=f"Discussed {ctx['pain_points']}. Interested in Pharmesol demo.",
    )
    mock_schedule_callback(
        pharmacy_name=ctx["pharmacy_name"],
        contact_name=ctx["contact_name"],
        preferred_time="to be confirmed",
        notes=f"Rx volume: {rx}. Pain points: {ctx['pain_points']}.",
    )

    print("--- Simulation complete ---")


if __name__ == "__main__":
    run_agent()
