import ast
from datetime import datetime, timezone


def get_timestamp_utc() -> int:
    dt_utc = datetime.now(timezone.utc)
    utc_timestamp = int(dt_utc.timestamp())
    return utc_timestamp


def text_to_dict(text: str) -> dict:
    clean_text = (
        text.replace("null", "None").replace("false", "False").replace("true", "True")
    )
    return ast.literal_eval(clean_text)
