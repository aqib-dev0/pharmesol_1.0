"""Handles pharmacy identification via the Pharmesol mock API.
In production this would be a CRM lookup."""

import re
import requests
from config import PHARMACY_API_URL


def fetch_all_pharmacies() -> list:
    """Fetch all pharmacy records from the mock API. Returns empty list on failure."""
    try:
        response = requests.get(PHARMACY_API_URL, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[WARNING] Could not reach pharmacy API: {e}")
        return []


def _normalize_phone(phone: str) -> str:
    """Strip all non-digit characters from a phone number for comparison."""
    return re.sub(r"\D", "", phone)


def identify_pharmacy(phone_number: str) -> dict | None:
    """Look up a pharmacy by phone number. Returns the raw API dict or None."""
    print(f"[CRM Lookup] searching for phone: {phone_number}...", end=" ", flush=True)
    normalized_input = _normalize_phone(phone_number)
    pharmacies = fetch_all_pharmacies()
    for pharmacy in pharmacies:
        record_phone = _normalize_phone(pharmacy.get("phone", ""))
        if record_phone and record_phone == normalized_input:
            print(f"match found: {pharmacy.get('name', 'unknown')}")
            return pharmacy
    print("no match -- unknown caller")
    return None


def get_pharmacy_display(pharmacy: dict) -> dict:
    """Normalize a raw API record into a clean display dict used throughout the system.

    The mock API has inconsistent field names across records. This function
    abstracts those quirks so the rest of the codebase never sees raw API dicts.
    """
    # Location: prefer city+state, fall back to address, then unknown
    if pharmacy.get("city") and pharmacy.get("state"):
        location = f"{pharmacy['city']}, {pharmacy['state']}"
    elif pharmacy.get("address"):
        location = pharmacy["address"]
    else:
        location = "unknown"

    # Rx volume: prefer prescriptions list sum, then flat rxVolume field
    if isinstance(pharmacy.get("prescriptions"), list):
        rx_volume = sum(p.get("count", 0) for p in pharmacy["prescriptions"])
    else:
        rx_volume = int(pharmacy.get("rxVolume", 0))

    return {
        "name": pharmacy.get("name", "Unknown Pharmacy"),
        "phone": pharmacy.get("phone", ""),
        "email": pharmacy.get("email") or None,
        "location": location,
        "rx_volume": rx_volume,
        "contact_name": pharmacy.get("contactPerson", "the team"),
    }
