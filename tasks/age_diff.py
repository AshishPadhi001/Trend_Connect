from datetime import datetime
from fastapi import BackgroundTasks

def age_difference(dob):
    """Compute age difference."""
    now = datetime.utcnow()
    dob_datetime = datetime.combine(dob, datetime.min.time())  # Convert date to datetime
    age_diff = now - dob_datetime
    years = age_diff.days // 365
    months = (age_diff.days % 365) // 30
    days = (age_diff.days % 365) % 30
    hours, remainder = divmod(age_diff.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return years, months, days, hours, minutes
