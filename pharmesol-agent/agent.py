"""Core agent logic: prompt assembly, LLM calls, and conversation management
for the Pharmesol inbound sales agent."""

from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_MAX_TOKENS, AGENT_NAME, COMPANY_NAME


def build_system_prompt(pharmacy: dict | None, knowledge_chunks: list) -> str:
    """Assemble the full system prompt for the LLM.

    The prompt has four sections: role definition, hard rules, pharmacy context,
    and relevant product knowledge. Keeping all of these in one place makes it
    easy to see exactly what the agent knows and why.
    """
    print(f"[Prompt] assembling system prompt ({len(knowledge_chunks)} RAG chunks injected)")

    # 1. Role definition
    role = (
        f"You are {AGENT_NAME}, a warm and knowledgeable sales agent at {COMPANY_NAME}. "
        "You're on an inbound phone call with a pharmacy operator. "
        "You are not a chatbot -- you speak naturally, like a real person would on the phone. "
        "Keep responses concise: one or two sentences when possible, three at most."
    )

    # 2. Hard rules
    rules = (
        "Follow these rules without exception:\n"
        "1. Never fabricate pricing, timelines, or features not in your knowledge base.\n"
        "2. Never make clinical claims or give medical advice.\n"
        "3. If asked something out of scope, acknowledge it honestly and redirect to what you can help with.\n"
        "4. This is a phone call -- be concise. No bullet points, no long lists.\n"
        "5. Always be steering the conversation toward booking a demo or scheduling a callback.\n"
        "6. When you know the pharmacy's name, use it naturally -- not on every sentence, just where it fits.\n"
        "7. Follow the caller's lead. Do not run the conversation like a form. If the caller "
        "jumps to scheduling, go there. Weave in qualifying questions naturally when there "
        "is an opening, or ask them briefly at the end framed as helping the team prepare. "
        "Never ask more than one question per turn."
    )

    # 3. Pharmacy context
    if pharmacy:
        context = (
            f"Caller context:\n"
            f"  Pharmacy: {pharmacy['name']}\n"
            f"  Location: {pharmacy['location']}\n"
            f"  Rx volume: approximately {pharmacy['rx_volume']} prescriptions/month\n"
            f"  Contact: {pharmacy['contact_name']}\n"
        )
    else:
        context = (
            "Caller context:\n"
            "  This caller is not in our system. Greet them warmly and collect their pharmacy name "
            "and monthly prescription volume through natural conversation -- don't make it feel like a form."
        )

    # 4. Product knowledge
    knowledge = "What you know about Pharmesol:\n"
    for i, chunk in enumerate(knowledge_chunks, 1):
        knowledge += f"{i}. {chunk}\n"

    return "\n\n".join([role, rules, context, knowledge])


def get_llm_response(messages: list) -> str:
    """Call the OpenAI API and return the assistant's response text.

    Uses the full conversation history so the model has context on every turn.
    Falls back to a safe string if the API call fails -- the conversation should
    never crash due to a transient API error.
    """
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        # Production: caller input passes through Lakera Guard before reaching the LLM.
        # See lakera.ai -- detects prompt injection from adversarial callers.
        # if lakera_client.moderate(user_input).flagged: return safe_fallback_response()

        print(f"[LLM] sending prompt to {OPENAI_MODEL}... ", end="", flush=True)
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=OPENAI_TEMPERATURE,
            max_tokens=OPENAI_MAX_TOKENS,
        )
        print("response received")
        return completion.choices[0].message.content
    except Exception as e:
        print(f"[ERROR] LLM call failed: {e}")
        return "I'm sorry, I didn't catch that -- could you say that again?"


def extract_conversation_context(messages: list) -> dict:
    """Scan conversation history and extract key facts about the caller.

    Uses simple string heuristics -- no LLM call. Good enough to populate
    the follow-up tools at end of call. In production this would be a
    structured extraction call with a dedicated schema.
    """
    full_text = " ".join(
        m["content"] for m in messages if m["role"] in ("user", "assistant")
    ).lower()

    context = {
        "pharmacy_name": "unknown",
        "rx_volume": "unknown",
        "pain_points": "not captured",
        "contact_name": "the team",
    }

    # Pharmacy name: look for patterns like "at X pharmacy" or "X pharmacy"
    import re
    name_match = re.search(r"(?:at|from|this is)\s+([\w\s]+pharmacy)", full_text)
    if name_match:
        context["pharmacy_name"] = name_match.group(1).title()

    # Rx volume: look for numbers near "prescription" or "rx"
    vol_match = re.search(r"(\d[\d,]*)\s*(?:prescriptions?|rx)", full_text)
    if vol_match:
        context["rx_volume"] = vol_match.group(1) + "/month"

    # Pain points: look for common problem keywords
    pain_keywords = ["will-call", "refill", "staff", "short", "pickup", "after hours", "coverage", "wait"]
    found = [kw for kw in pain_keywords if kw in full_text]
    if found:
        context["pain_points"] = ", ".join(found)

    return context
