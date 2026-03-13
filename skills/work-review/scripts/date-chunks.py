#!/usr/bin/env python3
"""
Splits a date range into 2-week chunks to avoid API rate limits.

Usage: date-chunks.py <start-date> <end-date> [chunk-days]

Arguments:
    start-date  Start of date range (YYYY-MM-DD)
    end-date    End of date range (YYYY-MM-DD)
    chunk-days  Optional chunk size in days (default: 14)

Output: JSON array of {start, end} date pairs

Example:
    $ python date-chunks.py 2026-01-01 2026-02-15
    [
      {"start": "2026-01-01", "end": "2026-01-14"},
      {"start": "2026-01-15", "end": "2026-01-28"},
      {"start": "2026-01-29", "end": "2026-02-11"},
      {"start": "2026-02-12", "end": "2026-02-15"}
    ]
"""
from datetime import datetime, timedelta
import sys
import json


def chunk_dates(start: str, end: str, chunk_days: int = 14) -> list:
    """
    Split a date range into chunks of specified size.
    
    Args:
        start: Start date as YYYY-MM-DD string
        end: End date as YYYY-MM-DD string
        chunk_days: Number of days per chunk (default 14)
    
    Returns:
        List of dicts with 'start' and 'end' keys
    """
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    chunks = []
    
    current = start_dt
    while current <= end_dt:
        chunk_end = min(current + timedelta(days=chunk_days - 1), end_dt)
        chunks.append({
            "start": current.strftime("%Y-%m-%d"),
            "end": chunk_end.strftime("%Y-%m-%d")
        })
        current = chunk_end + timedelta(days=1)
    
    return chunks


def main():
    if len(sys.argv) < 3:
        print("Usage: date-chunks.py <start-date> <end-date> [chunk-days]")
        print("Example: date-chunks.py 2026-01-01 2026-02-15")
        sys.exit(1)
    
    start = sys.argv[1]
    end = sys.argv[2]
    chunk_days = int(sys.argv[3]) if len(sys.argv) > 3 else 14
    
    try:
        chunks = chunk_dates(start, end, chunk_days)
        print(json.dumps(chunks, indent=2))
    except ValueError as e:
        print(f"Error parsing dates: {e}")
        print("Dates must be in YYYY-MM-DD format")
        sys.exit(1)


if __name__ == "__main__":
    main()
