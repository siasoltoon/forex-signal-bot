# PC Worker Connection Runbook

## Architecture

The PC Worker uses outbound pull mode for the home-PC deployment.

- Railway runs the Telegram/control plane and the durable SQLite-backed worker queue.
- Railway exposes an authenticated worker gateway on its existing HTTPS service.
- The Windows PC Worker makes outbound HTTPS requests to Railway.
- The PC Worker claims a queued job, executes it locally, renews its claim lease, and posts the result back.
- The Worker itself remains bound to 127.0.0.1:8765 for local diagnostics.
- No port forwarding, Tailscale Funnel, Cloudflare Tunnel, or public PC endpoint is required.
- PC_WORKER_TOKEN is the shared secret for the Railway worker gateway and local worker.

## Railway variables

Configure on the Railway application:

~~~text
PC_WORKER_MODE=pull
PC_WORKER_TOKEN=<strong-secret>
WORKER_QUEUE_DATABASE_PATH=worker_queue.sqlite3
~~~

Do not configure PC_WORKER_URL for pull mode.

The Railway service must have a Railway-provided public HTTPS domain.

## Windows PC setup

From the PC Worker repository root:

~~~powershell
$env:WORKER_QUEUE_API_URL = "https://<your-railway-domain>"
$env:PC_WORKER_TOKEN = "<same-secret>"
$env:WORKER_QUEUE_POLL_INTERVAL = "3"
$env:WORKER_QUEUE_REQUEST_TIMEOUT = "30"
python -m worker.main
~~~

Prefer storing these values in the local .env file because the project already loads dotenv automatically. Never commit .env.

The worker starts two local capabilities:

1. 127.0.0.1:8765 for local worker health/jobs.
2. Outbound HTTPS pull transport to Railway.

## Pull lifecycle

~~~text
Railway queue
    |
    | POST /worker/claim
    v
PC Worker
    |
    | execute locally
    |
    +-- POST /worker/renew   (while running)
    |
    +-- POST /worker/result
             |
             v
      Railway queue COMPLETED
~~~

The claim token is a fenced lease. A stale worker cannot overwrite a newer worker's result.

If the PC is offline, queued jobs remain PENDING. When the PC returns, the next polling cycle claims pending work.

## Security

- /worker/claim, /worker/renew, /worker/result, and /worker/health require Authorization: Bearer <PC_WORKER_TOKEN>.
- /health remains the unauthenticated Railway health endpoint.
- Never put the token in Git, logs, Telegram messages, screenshots, or issue comments.
- Never expose the PC Worker port through the router.
- If the token is exposed, rotate it on Railway and the PC immediately.

## Verification

1. Deploy Railway with PC_WORKER_MODE=pull and the token.
2. Generate or confirm the Railway public HTTPS domain.
3. Set WORKER_QUEUE_API_URL and the same token on the PC.
4. Start the PC Worker.
5. Worker logs must show pull transport enabled.
6. Submit a heavy job from the application.
7. Worker claims it and executes it locally.
8. The claim lease is renewed while execution continues.
9. Railway queue record becomes COMPLETED, FAILED, TIMEOUT, or CANCELLED.
