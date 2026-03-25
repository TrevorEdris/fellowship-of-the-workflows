Review this code for security vulnerabilities:

```python
import requests
from flask import Flask, request, jsonify
from urllib.parse import urlparse

app = Flask(__name__)

@app.route("/preview")
def fetch_preview():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "URL required"}), 400

    try:
        resp = requests.get(url, timeout=10)
        return jsonify({
            "status": resp.status_code,
            "content_type": resp.headers.get("content-type"),
            "body": resp.text[:1000],
        })
    except requests.RequestException:
        return jsonify({"error": "Failed to fetch URL"}), 502

@app.route("/health")
def health():
    return jsonify({"status": "ok"})
```
