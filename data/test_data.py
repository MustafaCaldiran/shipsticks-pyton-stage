"""
Centralized test data repository.

All scenarios, credentials, and variation data live here so that:
  - Tests stay free of magic strings
  - A single edit updates every test that uses the value
  - Scenario-driven parameterization is trivial

Design note: scenarios use a flat dict (not a dataclass) intentionally —
it keeps parameterization simple and diffs readable in PRs.
"""

import os
import secrets
from copy import deepcopy


# ---------------------------------------------------------------------------
# Dynamic helpers
# ---------------------------------------------------------------------------

def generate_email(domain: str = "example.com") -> str:
    """Return a unique email address for each sign-up test run."""
    tag = secrets.token_hex(3)[:5]
    return f"test+{tag}@{domain}"


# ---------------------------------------------------------------------------
# Booking scenarios
# ---------------------------------------------------------------------------
# Each scenario is a self-contained dict that describes ONE booking path.
# Tests iterate over these so adding a new scenario = one new dict entry.

SCENARIOS: dict[str, dict] = {
    "challenge": {
        "shipment_type": "One-way",
        "origin": "1234 Main Street, Los Angeles, CA, USA",
        "destination": "4321 Main St, Miami Lakes, FL, USA",
        "item_type": "Golf Bag (Standard)",
        "item_category": "Golf Bags",
        "item_size": "Standard",
        "items": [{"category": "Golf Bags", "quantity": 1, "sizes": ["Standard"]}],
        "service_level": "Ground",
        "delivery_date": "Wednesday, April 15, 2026",
        "coverage_amount": "$2,500.00 ($8.99)",
        "pickup_method": "haveThemPickedUp",
    },
    "two_golf_bags_ground": {
        "shipment_type": "One-way",
        "origin": "1234 Main Street, Los Angeles, CA, USA",
        "destination": "4321 Main St, Miami Lakes, FL, USA",
        "items": [{"category": "Golf Bags", "quantity": 2, "sizes": ["Standard", "Staff/XL"]}],
        "service_level": "Ground",
        "delivery_date": "Wednesday, April 15, 2026",
    },
}


# ---------------------------------------------------------------------------
# Auth credentials
# ---------------------------------------------------------------------------

AUTH_DATA = {
    "login": {
        "email": os.getenv("AUTH_EMAIL", "john@gmail.com"),
        "password": os.getenv("AUTH_PASSWORD", "Password"),
    },
    "sign_up": {
        "first_name": "John",
        "last_name": "Doe",
        "country": "United States of America",
        "how_did_you_hear": "Influencer",
        "phone_number": "151-351-3515",
    },
    "payment": {
        "first_name": "John",
        "last_name": "Doe",
        "card_number": "4242424242424242",
        "expiration_date": "12/28",
        "cvc": "123",
        "billing_country": "United States of America",
        "zip_code": "90001",
    },
}


# ---------------------------------------------------------------------------
# Variation pools (for future parameterized expansion)
# ---------------------------------------------------------------------------

VARIATIONS = {
    "origins": [
        "1234 Main Street, Los Angeles, CA, USA",
        "100 Universal City Plaza, Universal City, CA, USA",
        "1600 Amphitheatre Parkway, Mountain View, CA, USA",
    ],
    "destinations": [
        "4321 Main St, Miami Lakes, FL, USA",
        "1 Ocean Drive, Miami Beach, FL, USA",
        "2450 Biscayne Bay Blvd, Miami, FL, USA",
    ],
    "item_types": {
        "golf_bags": ["Standard", "Staff/XL"],
        "luggage": ["Carry On", "Checked", "Oversized"],
    },
    "service_levels": [
        "Ground",
        "Three Day Express",
        "Next Day Express",
        "Second Day Express",
    ],
}

INVALID_DATA = {
    "addresses": ["Invalid Address XYZ123", "!@#$%^&*()", ""],
}

TIMING = {
    "autocomplete_timeout": 10_000,
    "page_load_timeout": 30_000,
    "typing_delay": 50,
}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def get_sign_up_data() -> dict:
    """Return a fresh copy of sign-up data with a unique email."""
    data = deepcopy(AUTH_DATA["sign_up"])
    data["email"] = generate_email()
    data["password"] = "SecurePass123!"
    return data


def get_scenario_entries(selected_names: list[str] | None = None) -> list[tuple[str, dict]]:
    """
    Return (name, scenario) pairs filtered by *selected_names*.
    If the list is empty / None, return ALL scenarios.
    """
    if not selected_names:
        return list(SCENARIOS.items())

    entries = []
    for name in selected_names:
        if name not in SCENARIOS:
            raise KeyError(f"Unknown scenario: '{name}'. Available: {list(SCENARIOS.keys())}")
        entries.append((name, SCENARIOS[name]))
    return entries
