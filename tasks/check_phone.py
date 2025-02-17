import re
from fastapi import BackgroundTasks

def validate_phone_number(phone_number: str) -> bool:
    """Check if the phone number is valid (10 digits, only numbers)."""
    return bool(re.fullmatch(r"\d{10}", phone_number))
