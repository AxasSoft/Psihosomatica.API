from datetime import datetime, timezone, date, time
from typing import Optional


def to_unix_timestamp(dt: datetime | date | None) -> Optional[int]:
    if dt is None:
        return None
    if isinstance(dt, date) and not isinstance(dt, datetime):
        dt = datetime.combine(dt, time.min)
    return int(dt.timestamp())


def from_unix_timestamp(stamp: Optional[int]):

    if stamp is None:
        return None

    return datetime.fromtimestamp(stamp)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
