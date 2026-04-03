"""Central configuration and constants for the Pharmesol sales agent."""

import os

# Load .env file if present (without python-dotenv dependency)
_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_TEMPERATURE = 0.4
OPENAI_MAX_TOKENS = 180

PHARMACY_API_URL = "https://67e14fb758cc6bf785254550.mockapi.io/pharmacies"
MOCK_CALLER_PHONE = "+1-555-123-4567"

EXIT_PHRASES = ["exit", "quit", "bye", "goodbye", "end call"]

AGENT_NAME = "Aria"
COMPANY_NAME = "Pharmesol"
