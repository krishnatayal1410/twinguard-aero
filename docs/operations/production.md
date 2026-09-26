# TwinGuard deployment and verification

## Current boundary

This is a single-engine engineering prototype. Synthetic tests are software checks, not measured fault accuracy, RUL calibration, or flight-release approval. NASA C-MAPSS is simulated turbofan data and cannot validate this reciprocating-engine model by relabeling its channels. Real validation requires engine-specific recordings, maintenance ground truth, held-out engines/runs, fault onset labels, RUL error and interval coverage, and observed mission outcomes. Preserve raw files and calibration/units metadata.

## Cloud deployment

`deploy/cloud/render.yaml` defines a single API instance and private PostgreSQL. The specified plans are paid: review current Render pricing before applying. Set TRUSTED_HOSTS to the assigned API hostname plus localhost and 127.0.0.1. Keep one worker/instance: rolling twin history, fault configuration and active recording are process-local. Rolling restarts interrupt active recordings; end recordings before maintenance. PostgreSQL retains completed records and accounts.

Render needs an authenticated account. The backend must use PostgreSQL, a generated ingest key, explicit origins and hosts, and closed public signup. The container excludes local runtime databases, runs as a non-root user, and suppresses URL access logs to avoid logging websocket session tokens. Provision operators through a private server terminal with `PYTHONPATH=backend python scripts/provision_operator.py`; the password prompt is hidden.

Configure Vercel `VITE_TWINGUARD_API_ORIGIN=https://YOUR-API-HOST` and `VITE_TWINGUARD_DEMO_MODE=0`, then rebuild. Do not put ingest keys or database credentials in VITE variables. Test signup rejection, provisioned-account login, authenticated websocket traffic, stale data holds and saved replay recovery before switching the public application. Existing browser-demo identities do not become server accounts.

Auth has a bounded single-process limiter by network peer. Configure trusted proxy handling and edge rate limits for a real hosting environment; do not blindly trust forwarded headers. All accounts currently share one engine workspace, not tenant-isolated data. `/ready` checks database connectivity; `/health` checks process liveness. Authenticated `/api/v1/system/status` checks telemetry freshness. Provider monitoring must be configured to alert on repeated failures and stale telemetry; it is not enabled merely by this file.

## Backup and recovery

Run `DATABASE_URL=... python scripts/backup_database.py /private/backups/unique-name.dump`. The tool refuses overwrites; SQLite uses the online backup API and integrity_check. PostgreSQL uses pg_dump custom format and validates the archive list; pg_dump and pg_restore must be installed. Export secrets through the host's secret manager, not shell history. Backups contain account and operational data and must remain private. Configure provider-managed automatic backups and retention after provisioning. Test PostgreSQL restoration into a separate empty database with pg_restore and compare accounts, mission counts and samples before trusting recovery. An archive-list check alone is not a restore drill. Never restore over the active database as a test.

## Engine data and hardware

For CSV recordings: `PYTHONPATH=backend python scripts/evaluate_recording.py recording.csv --source 'rig, date, calibration and provenance' --output report.json`. Use canonical Telemetry fields/units; oil pressure is bar. Each row needs a timezone-aware increasing timestamp. Optional fault_label and rul_hours_label supply ground truth. The evaluator isolates its database, preserves source hash, and reports accuracy/confusion and RUL MAE/RMSE only when labels exist. It does not publish recordings as a live feed or train on evaluation data.

CAN: supply vendor DBC, adapter interface/channel, and a JSON mapping of canonical fields to `{ "signal": "vendor_name", "scale": 1, "offset": 0 }`. No manufacturer signal definitions are invented. Use `PYTHONPATH=backend python scripts/run_can_gateway.py --dbc vendor.dbc --mapping mapping.json --channel can0`. All mapped signals must be fresh within two seconds; invalid/incomplete samples are withheld. Stop the synthetic simulator before connecting a physical source to the same engine. Configure the adapter in listen-only mode where supported before attachment.

MQTT: configure MQTT_HOST/PORT/TOPIC, MQTT_USERNAME/PASSWORD, MQTT_TLS=1 and optional MQTT_CA_FILE. The broker must restrict publishing to the authorized engine topic; use separate publisher/subscriber credentials. Payloads must include the configured engine_id and canonical telemetry. TLS verifies the broker certificate. Neither configured flags nor virtual mapping tests prove a physical device is connected.

Sources: https://render.com/docs/blueprint-spec ; https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/
