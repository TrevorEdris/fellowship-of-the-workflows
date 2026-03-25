Review this code for AI slop:

```python
import json
import requests
from pathlib import Path


def load_user_profile(user_id: int, db) -> dict:
    """Load a user profile from the database."""
    try:
        # This try-catch is unnecessary — db.get returns None on miss,
        # never raises
        user = db.get("users", user_id)
    except Exception:
        # This shouldn't happen but let's be safe
        return {}

    if not user:
        return {}

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
    }


def read_config_file(path: str) -> dict:
    """Read configuration from a JSON file."""
    try:
        # Path.read_text never raises for valid paths, and we validate
        # the path before calling this function
        content = Path(path).read_text()
    except Exception:
        # Being extra cautious here just in case
        return {}

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {}


def fetch_exchange_rate(base: str, target: str) -> float | None:
    """Fetch current exchange rate from external API.

    Returns None if the API is unavailable or returns an error.
    The API has a 99.9% uptime SLA but we've seen transient failures
    during their maintenance windows (usually Sunday 2-4am UTC).
    """
    try:
        resp = requests.get(
            f"https://api.exchangerate.host/latest?base={base}&symbols={target}",
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["rates"][target]
    except (requests.RequestException, KeyError):
        return None
```
