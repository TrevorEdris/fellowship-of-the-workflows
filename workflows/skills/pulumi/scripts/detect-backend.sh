#!/usr/bin/env bash
# detect-backend.sh — Detect the configured Pulumi state backend
# Outputs backend type and URL for informational context

set -euo pipefail

detect_backend() {
  # Check if pulumi is available
  if ! command -v pulumi &>/dev/null; then
    echo "pulumi not found in PATH"
    return
  fi

  # Try to get backend info from pulumi whoami
  WHOAMI_OUTPUT=$(pulumi whoami -v 2>/dev/null || echo "")

  if [[ -z "$WHOAMI_OUTPUT" ]]; then
    echo "Not logged in to any Pulumi backend"
    return
  fi

  echo "$WHOAMI_OUTPUT"
  echo ""

  # Detect backend type
  if echo "$WHOAMI_OUTPUT" | grep -q "app.pulumi.com"; then
    echo "Backend type: Pulumi Cloud (managed)"
    echo "  -> Team-safe: Yes (concurrency locking, secrets encryption, audit log)"
  elif echo "$WHOAMI_OUTPUT" | grep -q "s3://"; then
    echo "Backend type: AWS S3"
    echo "  -> Team-safe: Yes (requires DynamoDB locking table)"
  elif echo "$WHOAMI_OUTPUT" | grep -q "gs://"; then
    echo "Backend type: Google Cloud Storage"
    echo "  -> Team-safe: Yes (built-in GCS object locking)"
  elif echo "$WHOAMI_OUTPUT" | grep -q "azblob://"; then
    echo "Backend type: Azure Blob Storage"
    echo "  -> Team-safe: Yes (requires Azure lease configuration)"
  elif echo "$WHOAMI_OUTPUT" | grep -q "file://\|/home\|/Users"; then
    echo "Backend type: Local filesystem"
    echo "  -> WARNING: Local backend has no concurrency locking."
    echo "  -> NOT SAFE for shared teams or production environments."
    echo "  -> Switch with: pulumi login s3://my-bucket (or gcs:// or Pulumi Cloud)"
  else
    echo "Backend type: Unknown"
  fi

  echo ""

  # List available stacks if logged in
  echo "Available stacks:"
  pulumi stack ls --all 2>/dev/null || echo "(none or not accessible)"
}

detect_backend
