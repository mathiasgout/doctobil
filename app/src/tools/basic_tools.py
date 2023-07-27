from datetime import datetime, timezone


def get_timestamp_utc() -> int:
    dt_utc = datetime.now(timezone.utc)
    utc_timestamp = int(dt_utc.timestamp())
    return utc_timestamp
