# Security posture

TwinGuard Aero is a local/synthetic engineering MVP, not a certified flight-control application.

Implemented hardening:
- Explicit CORS allowlist; no wildcard CORS.
- Trusted-host validation.
- Telemetry ingest key support.
- Strict Pydantic telemetry ranges and engine ID format.
- POST/PATCH/PUT request-size cap.
- Browser security headers and Nginx CSP.
- Local startup and Docker ports bind to loopback.
- Production mode can disable FastAPI Swagger docs.
- No real CAN IDs, credentials, DRDO data, or private keys are included.

Run `bash scripts/security_check.sh`.

No software can truthfully guarantee that no security vulnerability exists. Before any internet-facing or physical-engine deployment, add organizational authentication/authorization, TLS/mTLS, managed secret storage, network segmentation, dependency CVE scanning, SAST/DAST, penetration testing, signed updates, audit logging and an aerospace cybersecurity review.
