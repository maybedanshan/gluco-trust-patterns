# Local frontend and backend prototype

Run `python webapp_server.py` from the repository and open http://127.0.0.1:8766.
Python 3.10+ and the standard library are sufficient. The frontend lives in
`frontend/index.html`; `webapp_server.py` provides the API and serves only this
explicit page. Existing offline reports remain separate.

- `GET /api/health`: server readiness.
- `GET /api/research`: existing aggregate model/history/label results, excluding `per_person` records.
- `POST /api/simulate`: JSON `{ "mode": "block", "ratio": 0.2, "seed": 0 }`.
  Reuses the verified time weighting, missingness and metric functions on one
  synthetic day. Returns the reference, observed metrics, biases, removed indices
  and synthetic readings. Invalid or infeasible settings return HTTP 400.

This first local vertical slice separates rendering from computation. It does
not yet accept participant uploads, train models on request, provide accounts,
or implement background job storage. The standard-library HTTP server is a local
development entry point, bound to loopback, not a production deployment server.

Next: a versioned data-import schema with unit/time/participant validation,
then queued experiment jobs and persisted provenance. Agree the input contract
before accepting real clinical files. Keep scientific pipelines independently
reproducible from the CLI.

## API behavior and scope

The local server has no telemetry or persistent request/result storage. Research summaries are cached in memory and refreshed when any source file modification time (nanoseconds) or size changes; this is not a transaction across independently generated studies.

Demo seeds from 0 to 1,000,000 support free exploration. The endpoint uses an independent RNG convention: even a seed from 0–9 is not a reproduction of the reports, which derive random streams from participant/configuration keys. Use the CLI and fixed study protocols for report replication.

GET and POST routing both ignore query strings. Unsupported content types return 415, invalid inputs return 400, unknown routes return 404, and unexpected simulation failures return a generic 500 without exception details. CSP permits inline scripts/styles and same-origin API connections while denying other resource origins. Loopback binding limits network listening; it is not authentication or a complete privacy guarantee for other local software.
