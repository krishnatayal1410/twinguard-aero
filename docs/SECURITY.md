# Security posture

TwinGuard Aero is a local/synthetic engineering demonstrator, not a certified flight-control application.

## Implemented hardening

- Explicit CORS allowlist; no wildcard CORS.
- Trusted-host validation.
- Telemetry ingest-key support.
- Strict Pydantic telemetry ranges and engine-ID format.
- POST/PATCH/PUT request-size cap.
- Browser security headers and Nginx CSP.
- Local development startup defaults.
- Production mode can disable FastAPI Swagger docs.
- Production mode disables new account signup by default unless `ALLOW_SIGNUP=1` is deliberately configured.
- Passwords use PBKDF2-SHA256 with per-password random salts.
- Server-side sessions use random tokens stored as SHA-256 token hashes with expiration.
- Mission analysis fails closed when telemetry is stale or below the configured data-quality threshold.
- No real CAN IDs, credentials, DRDO data, or private keys are included.

## Account creation policy

Development/local SIH use:

```text
TWINGUARD_ENV=development
ALLOW_SIGNUP=1
```

Production default:

```text
TWINGUARD_ENV=production
```

With production mode, signup defaults to disabled. If account provisioning requires temporary signup, enable it only in a controlled environment and disable it again after provisioning.

The current local MVP assigns the first created account the `admin` label and later accounts the `operator` label. This is not a complete enterprise RBAC/provisioning system. Before internet-facing deployment, replace this bootstrap behavior with organizational identity, explicit role assignment and audited account lifecycle management.

## Telemetry/decision safety boundary

Transport connectivity is not considered sufficient for decision support. TwinGuard separately tracks:

- telemetry age,
- data-quality score,
- Sensor Trust,
- decision eligibility.

If the latest state exceeds `TELEMETRY_STALE_SECONDS` or data quality falls below `MISSION_MIN_DATA_QUALITY`, the runtime enters `DATA HOLD` and blocks new Mission Reliability Twin analysis.

This does not make the software flight-safe; it prevents one obvious class of stale-data misuse in the demonstrator.

## Run checks

```bash
bash scripts/security_check.sh
```

CI additionally compiles/tests the backend, builds the frontend, verifies the packaged synthetic native model artifacts and executes a live backend + simulator integration path.

## Before any internet-facing or physical-engine deployment

Add or validate at minimum:

- organizational authentication/authorization and account provisioning,
- TLS/mTLS as appropriate,
- managed secret storage and rotation,
- network segmentation,
- audit logging,
- dependency/SBOM/CVE scanning,
- SAST and DAST,
- penetration testing,
- signed releases/updates,
- secure logging/telemetry retention policy,
- rate limits and abuse controls,
- backup/recovery procedures,
- formal threat modeling,
- applicable aerospace cybersecurity and safety review.

No software can truthfully guarantee that no security vulnerability exists, and none of these controls substitute for the validation/certification pathway required for a flight-critical system.
