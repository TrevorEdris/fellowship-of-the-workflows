Review this code for AI slop:

```python
import hmac
import hashlib
from datetime import datetime, timedelta


def verify_webhook(payload: bytes, signature: str, secret: str) -> bool:
    # Stripe sends signatures as "t=timestamp,v1=hash" format
    # We must validate within 5 minutes to prevent replay attacks
    parts = dict(p.split("=", 1) for p in signature.split(","))

    timestamp = int(parts["t"])
    expected = hmac.new(
        secret.encode(),
        f"{timestamp}.".encode() + payload,
        hashlib.sha256,
    ).hexdigest()

    # Constant-time comparison prevents timing side-channel attacks
    if not hmac.compare_digest(expected, parts["v1"]):
        return False

    # Reject signatures older than 5 minutes (Stripe's recommendation)
    age = datetime.now().timestamp() - timestamp
    return age < 300


def calculate_total(items: list[dict]) -> float:
    """Calculate the total price for the given items.

    This function iterates through the list of items and calculates
    the total price by summing up individual item prices, ensuring
    accurate and reliable computation of the final amount.
    """
    total = 0.0  # Initialize total to zero
    for item in items:
        price = item["price"]  # Get the price
        quantity = item["quantity"]  # Get the quantity
        total += price * quantity  # Add to total
    return total  # Return the final total


def parse_duration(s: str) -> timedelta:
    # Format: "30s", "5m", "2h", "1d" — no compound durations
    units = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days"}
    return timedelta(**{units[s[-1]]: int(s[:-1])})
```
