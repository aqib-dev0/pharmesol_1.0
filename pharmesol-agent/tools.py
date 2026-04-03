"""Mock follow-up tools for the Pharmesol sales agent.
In production these would integrate with SendGrid (email)
and Google Calendar / Calendly (scheduling).
For this simulation they log to stdout."""


def mock_send_followup_email(pharmacy_name: str, contact_name: str, email: str, summary: str) -> dict:
    """Send a follow-up email after the call.

    In production: POST to the SendGrid API with a templated email,
    CC the assigned account executive, and log the send event to HubSpot.
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

    In production: create a Google Calendar event via the Calendar API,
    send a Calendly invite link to the contact, and update the HubSpot deal stage.
    """
    print("[CALLBACK SCHEDULED]")
    print(f"  Pharmacy: {pharmacy_name}")
    print(f"  Contact: {contact_name}")
    print(f"  Preferred time: {preferred_time}")
    print(f"  Notes: {notes}")
    print()
    return {"status": "scheduled", "pharmacy": pharmacy_name, "time": preferred_time}


def mock_log_lead(pharmacy_name: str, rx_volume: str, pain_points: str, outcome: str) -> dict:
    """Log the lead and call outcome to the CRM.

    In production: POST to the HubSpot Contacts and Deals API,
    tag the lead with the appropriate lifecycle stage, and trigger
    the assigned rep's follow-up task queue.
    """
    print("[LEAD LOGGED]")
    print(f"  Pharmacy: {pharmacy_name}")
    print(f"  Rx Volume: {rx_volume}")
    print(f"  Pain points: {pain_points}")
    print(f"  Outcome: {outcome}")
    print()
    return {"status": "logged", "pharmacy": pharmacy_name}
