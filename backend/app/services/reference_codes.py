"""Short, human-friendly load reference codes (e.g., `HH-7K2X9P`).

Used for customer-facing identifiers in receipts, support tickets, and SMS —
so they need to be both unambiguous when spoken and short enough to type.
Crockford-base32 minus I/L/O/U handles both.
"""

import secrets

_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_PREFIX = "HH-"
_SUFFIX_LEN = 8  # gives ~33 bits of entropy — plenty for non-cryptographic IDs


def generate_load_reference() -> str:
    suffix = "".join(secrets.choice(_ALPHABET) for _ in range(_SUFFIX_LEN))
    return f"{_PREFIX}{suffix}"
