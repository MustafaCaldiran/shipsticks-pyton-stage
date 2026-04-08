"""Test data kept behaviorally aligned with the JavaScript repo."""

from __future__ import annotations

import secrets
from copy import deepcopy


def generate_email(domain: str = "example.com") -> str:
    tag = secrets.token_hex(3)[:5]
    return f"test+{tag}@{domain}"


SCENARIOS: dict[str, dict] = {
    "challenge": {
        "shipmentType": "One-way",
        "origin": "1234 Main Street, Los Angeles, CA, USA",
        "destination": "4321 Main St, Miami Lakes, FL, USA",
        "itemType": "Golf Bag (Standard)",
        "itemCategory": "Golf Bags",
        "itemSize": "Standard",
        "items": [
            {
                "category": "Golf Bags",
                "quantity": 1,
                "sizes": ["Standard"],
            }
        ],
        "serviceLevel": "Ground",
        "deliveryDate": "Wednesday, April 29, 2026",
        "coverageAmount": "$2,500.00 ($8.99)",
        "pickupMethod": "haveThemPickedUp",
    },
    "two_golf_bags_ground": {
        "shipmentType": "One-way",
        "origin": "1234 Main Street, Los Angeles, CA, USA",
        "destination": "4321 Main St, Miami Lakes, FL, USA",
        "items": [
            {
                "category": "Golf Bags",
                "quantity": 2,
                "sizes": ["Standard", "Staff/XL"],
            }
        ],
        "serviceLevel": "Ground",
        "deliveryDate": "Wednesday, April 29, 2026",
    },
}

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
    "itemTypes": {
        "golfBags": ["Standard", "Staff/XL"],
        "luggage": ["Carry On", "Checked", "Oversized"],
    },
    "serviceLevels": [
        "Ground",
        "Three Day Express",
        "Next Day Express",
        "Second Day Express",
    ],
}

INVALID_DATA = {
    "addresses": [
        "Invalid Address XYZ123",
        "!@#$%^&*()",
        "",
    ],
}

TIMING = {
    "autocompleteTimeout": 10_000,
    "pageLoadTimeout": 30_000,
    "typingDelay": 50,
}

AUTH_DATA = {
    "login": {
        "email": "john@gmail.com",
        "password": "Password",
    },
    "signUp": {
        "password": "SecurePass123!",
        "firstName": "John",
        "lastName": "Doe",
        "country": "United States of America",
        "howDidYouHear": "Influencer",
        "phoneNumber": "151-351-3515",
    },
    "payment": {
        "firstName": "John",
        "lastName": "Doe",
        "cardNumber": "4242424242424242",
        "expirationDate": "12/28",
        "cvc": "123",
        "billingCountry": "United States of America",
        "zipCode": "90001",
    },
}


def _with_python_aliases(data: dict) -> dict:
    aliased = deepcopy(data)
    key_aliases = {
        "shipmentType": "shipment_type",
        "itemType": "item_type",
        "itemCategory": "item_category",
        "itemSize": "item_size",
        "serviceLevel": "service_level",
        "deliveryDate": "delivery_date",
        "coverageAmount": "coverage_amount",
        "pickupMethod": "pickup_method",
    }
    for camel_key, snake_key in key_aliases.items():
        if camel_key in aliased:
            aliased[snake_key] = aliased[camel_key]
    return aliased


def get_sign_up_data() -> dict:
    sign_up = deepcopy(AUTH_DATA["signUp"])
    sign_up["email"] = generate_email()
    sign_up["first_name"] = sign_up["firstName"]
    sign_up["last_name"] = sign_up["lastName"]
    sign_up["how_did_you_hear"] = sign_up["howDidYouHear"]
    sign_up["phone_number"] = sign_up["phoneNumber"]
    sign_up["password"] = sign_up["password"]
    return sign_up


def get_scenario_entries(selected_names: list[str] | None = None) -> list[tuple[str, dict]]:
    requested_names = [name for name in (selected_names or []) if name]
    if not requested_names:
        return [(name, _with_python_aliases(scenario)) for name, scenario in SCENARIOS.items()]

    entries = []
    for name in requested_names:
        scenario = SCENARIOS.get(name)
        if scenario is None:
            raise KeyError(f"Unknown scenario: {name}")
        entries.append((name, _with_python_aliases(scenario)))
    return entries
