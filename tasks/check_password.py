import re
from fastapi import BackgroundTasks

def check_password_strength(password: str) -> str:
    """Check password strength based on length and complexity."""
    if len(password) < 8:
        return "low"  # Too short

    if " " in password:
        return "low"  # No spaces allowed

    has_upper = bool(re.search(r"[A-Z]", password))
    has_lower = bool(re.search(r"[a-z]", password))
    has_digit = bool(re.search(r"\d", password))
    has_special = bool(re.search(r"[!@#$%^&*(),.?\":{}|<>]", password))

    # Weak Password
    if not (has_upper and has_lower and has_digit and has_special):
        return "medium"

    # Strong Password
    return "strong"
