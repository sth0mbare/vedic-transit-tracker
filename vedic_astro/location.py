"""Geocoding and timezone resolution for birth details.

Getting this right matters more than it looks: a birth chart is only as
accurate as the UTC instant it's computed for, and naive timezone handling
(e.g. using today's UTC offset for a birth date decades ago) silently
produces wrong charts. We resolve the IANA zone from coordinates and let
zoneinfo apply the historical offset that was actually in effect on that date.
"""

from dataclasses import dataclass
from datetime import date, datetime, time as dtime
from zoneinfo import ZoneInfo

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

_geolocator = Nominatim(user_agent="vedic-transit-tracker")
_tf = TimezoneFinder()


class LocationError(Exception):
    pass


@dataclass
class Place:
    query: str
    address: str
    latitude: float
    longitude: float
    timezone: str  # IANA tz name, e.g. "Asia/Kolkata"


def geocode_place(place_name: str) -> Place:
    """Resolve a free-text place name to coordinates + IANA timezone."""
    location = _geolocator.geocode(place_name, timeout=10)
    if location is None:
        raise LocationError(
            f"Could not find a location matching '{place_name}'. "
            "Try being more specific, e.g. 'Pune, Maharashtra, India'."
        )
    tz_name = _tf.timezone_at(lat=location.latitude, lng=location.longitude)
    if tz_name is None:
        raise LocationError(
            f"Found coordinates for '{place_name}' but could not resolve a timezone. "
            "This can happen for points over open ocean."
        )
    return Place(
        query=place_name,
        address=location.address,
        latitude=location.latitude,
        longitude=location.longitude,
        timezone=tz_name,
    )


def local_to_utc(birth_date: date, birth_time: dtime, tz_name: str) -> datetime:
    """Convert a local birth date/time to a UTC-aware datetime.

    Uses zoneinfo so the historically correct offset (including any DST
    rules in effect at the time) is applied, not just today's offset.
    """
    local_dt = datetime.combine(birth_date, birth_time, tzinfo=ZoneInfo(tz_name))
    return local_dt.astimezone(ZoneInfo("UTC"))
