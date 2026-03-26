Review this documentation for AI slop:

```markdown
# Configuration Guide

## Overview

It's worth noting that this configuration system provides a robust and
comprehensive solution for managing application settings. By leveraging
the power of modern tooling, it seamlessly integrates with existing
workflows to deliver a streamlined and performant experience.

## Environment Variables

The application reads configuration from environment variables. Set these
before starting the service:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `LOG_LEVEL` | No | Logging verbosity (default: `info`) |

## Configuration Files

Configuration can also be loaded from YAML files. The application searches
for config files in the following locations, in order of priority:

1. `./config.local.yaml` (gitignored, for local overrides)
2. `./config.yaml` (committed defaults)
3. `/etc/myapp/config.yaml` (system-wide)

This provides a streamlined and performant experience for developers who
need to customize their local environment without affecting the committed
configuration that other team members rely on.

## Validation

All configuration values are validated at startup. Invalid or missing
required values cause the application to exit with a descriptive error
message rather than failing silently at runtime.
```
