"""Mock follow-up tools for the Pharmesol sales agent.
In production these would integrate with SendGrid (email)
and Google Calendar / Calendly (scheduling).
For this simulation they log to stdout."""


def mock_send_followup_email(pharmacy_name: str, contact_name: str, email: str, summary: str) -> dict:
    """Send a follow-up email after the call.

    In production: calls SendGrid API with a templated email. Template selected based on
    call outcome -- demo booked, info requested, or escalation triggered.
    """
    print("[EMAIL QUEUED]")
    print(f"  To: {contact_name} <{email}>")
    print(f"  Subject: Great speaking with you -- Pharmesol next steps")
    print(f"  Pharmacy: {pharmacy_name}")
    print(f"  Summary: {summary}")
    print()
    return {"status": "sent", "to": email, "pharmacy": pharmacy_name}


def mock_schedule_callback(pharmacy_name: str, contact_name: str, preferred_time: str, notes: str) -> dict:
    """Schedule a follow-up callback with the pharmacy.

    In production: creates a Google Calendar event via Calendly API. Sends confirmation
    to both the pharmacy contact and the assigned Pharmesol sales rep.
    """
    print("[CALLBACK SCHEDULED]")
    print(f"  Pharmacy: {pharmacy_name}")
    print(f"  Contact: {contact_name}")
    print(f"  Preferred time: {preferred_time}")
    print(f"  Notes: {notes}")
    print()
    return {"status": "scheduled", "pharmacy": pharmacy_name, "time": preferred_time}


def mock_escalate_to_human(pharmacy_name: str, contact_name: str, notes: str) -> dict:
    """Escalate the call to a human sales rep.

    In production: fires a Slack alert to the assigned rep's channel with full
    call context, transfers the live call via Twilio, and updates the HubSpot deal
    stage to 'Escalated'. The rep picks up with the context already in front of them.
    """
    print("[ESCALATION TRIGGERED]")
    print(f"  Pharmacy: {pharmacy_name}")
    print(f"  Contact: {contact_name}")
    print(f"  Reason: caller requested human / out-of-scope question")
    print(f"  Notes: {notes}")
    print()
    return {"status": "escalated", "pharmacy": pharmacy_name}


def mock_log_lead(pharmacy_name: str, rx_volume: str, pain_points: str, outcome: str) -> dict:
    """Log the lead and call outcome to the CRM.

    In production: writes a structured lead record to HubSpot or Salesforce after every call.
    This closes the context loop -- next time this pharmacy calls, the CRM lookup returns
    enriched data including pain points and previous conversation outcomes. Also triggers
    a Slack alert to the assigned sales rep.
    """
    print("[LEAD LOGGED]")
    print(f"  Pharmacy: {pharmacy_name}")
    print(f"  Rx Volume: {rx_volume}")
    print(f"  Pain points: {pain_points}")
    print(f"  Outcome: {outcome}")
    print()
    return {"status": "logged", "pharmacy": pharmacy_name}
