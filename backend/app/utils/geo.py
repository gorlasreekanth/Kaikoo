from fastapi import Request
from app.config import settings

# Timezones that map to the APAC region.
# Covers the Indian subcontinent, Southeast Asia, East Asia, and Oceania —
# locations closer to ap-south-1 than to us-east-1.
_APAC_TIMEZONES = frozenset({
    # South Asia
    "Asia/Kolkata", "Asia/Calcutta", "Asia/Colombo", "Asia/Dhaka",
    "Asia/Kathmandu", "Asia/Karachi", "Asia/Thimphu",
    # Southeast Asia
    "Asia/Singapore", "Asia/Bangkok", "Asia/Jakarta", "Asia/Ho_Chi_Minh",
    "Asia/Manila", "Asia/Kuala_Lumpur",
    # East Asia
    "Asia/Tokyo", "Asia/Seoul", "Asia/Shanghai", "Asia/Hong_Kong",
    "Asia/Taipei",
    # Oceania
    "Australia/Sydney", "Australia/Melbourne", "Australia/Perth",
    "Pacific/Auckland",
})


def detect_region(request: Request) -> str:
    """Return a region key based on the X-Timezone header sent by the frontend.

    Falls back to settings.default_region when the header is missing or
    doesn't match a known timezone.
    """
    tz = request.headers.get("X-Timezone", "")
    if tz in _APAC_TIMEZONES:
        return "apac"
    return settings.default_region
