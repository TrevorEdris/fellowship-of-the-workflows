Review this code for security vulnerabilities:

```python
import os
import tempfile
from flask import Flask, request, send_file, jsonify

app = Flask(__name__)

UPLOAD_DIR = "/var/app/uploads"
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".docx"}

@app.route("/download/<filename>")
def download_file(filename):
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404
    return send_file(filepath)

@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided"}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": f"Extension {ext} not allowed"}), 400

    safe_name = f"{os.urandom(16).hex()}{ext}"
    dest = os.path.join(UPLOAD_DIR, safe_name)

    if not os.path.abspath(dest).startswith(os.path.abspath(UPLOAD_DIR)):
        return jsonify({"error": "Invalid path"}), 400

    file.save(dest)
    return jsonify({"filename": safe_name})

@app.route("/export")
def export_report():
    data = generate_report()
    tmp_path = f"/tmp/report_{request.args.get('id', 'default')}.csv"
    with open(tmp_path, "w") as f:
        f.write(data)
    return send_file(tmp_path)
```
