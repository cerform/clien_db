"""JSON Schema and validation helpers for INKA structured responses."""
from __future__ import annotations

import json
from jsonschema import validate, ValidationError

INKA_CONTRACT_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "next_action": {
            "type": "string",
            "enum": ["s0","s1","s2","s3","s4","s5","s6","s7","s8","s9","s10","s11","s12","repeat","human","other"]
        },
        "meta": {
            "type": "object",
            "properties": {
                "stage": {"type": "string"},
                "antirepeat_key": {"type": "string"},
                "client_profile": {"type": "object"},
                "slots": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "start": {"type": "string"},
                            "end": {"type": "string"},
                            "display": {"type": "string"}
                        },
                        "required": ["id","start","end","display"]
                    }
                },
                "selected_slot_id": {"type": "string"},
                "validation": {"type": "object"},
                "confidence": {"type": "number"},
                "booking_id": {"type": "string"},
                "confirmation": {"type": "object"},
                "follow_up": {"type": "object"},
                "reason": {"type": "string"}
            },
            "required": ["stage","antirepeat_key","client_profile"]
        }
    },
    "required": ["text","next_action","meta"],
    "additionalProperties": False
}


class ContractValidationError(Exception):
    pass


def validate_contract(payload: dict) -> None:
    """Validate a parsed payload against the INKA contract schema.

    Raises:
        ContractValidationError: with message containing validation details.
    """
    try:
        validate(instance=payload, schema=INKA_CONTRACT_SCHEMA)
    except ValidationError as e:
        raise ContractValidationError(str(e))


def load_contract_from_text(raw: str) -> dict:
    """Extract and parse first JSON object from raw model output."""
    import re

    m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if not m:
        raise ContractValidationError("No JSON object found in model output")
    try:
        payload = json.loads(m.group(0))
    except Exception as e:
        raise ContractValidationError(f"JSON parse error: {e}")
    # validate structure
    validate_contract(payload)
    return payload
