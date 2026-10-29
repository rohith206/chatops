"""Entry point: Jenkins webhook -> Slack, plus /build slash command."""
import hashlib
import hmac
import time

from flask import Flask, jsonify, request

import config
import jenkins_client
from formatter import build_message, normalize
from slack_notifier import notify

app = Flask(__name__)


# -Jenkins Webhook
@app.post("/webhook/jenkins")
def jenkins_webhook():
    if not hmac.compare_digest(request.headers.get("X-Webhook-Token", ""), config.WEBHOOK_TOKEN):
        return jsonify(error="unauthorized"), 401
    event = normalize(request.get_json(force=True, silent=True) or {})
    ok = notify(event)
    return jsonify(sent=ok), 200 if ok else 502


# ---- ChatOps: /build status <job> | /build run <job> --------------------
def _valid_slack_request() -> bool:
    ts = request.headers.get("X-Slack-Request-Timestamp", "0")
    if abs(time.time() - int(ts)) > 300:
        return False
    base = f"v0:{ts}:{request.get_data(as_text=True)}"
    expected = "v0=" + hmac.new(config.SLACK_SIGNING_SECRET.encode(), base.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, request.headers.get("X-Slack-Signature", ""))


@app.post("/slack/command")
def slash_command():
    if not _valid_slack_request():
        return "invalid signature", 401
    parts = request.form.get("text", "").split()
    if len(parts) != 2 or parts[0] not in ("status", "run"):
        return "Usage: `/build status <job>` or `/build run <job>`"
    action, job = parts
    try:
        if action == "run":
            jenkins_client.trigger_build(job)
            return f"🚀 Triggered `{job}`"
        return jsonify(response_type="in_channel", **build_message(jenkins_client.last_build(job)))
    except Exception as e:
        return f"Jenkins error: {e}"


@app.get("/health")
def health():
    return "ok"


if __name__ == "__main__":
    app.run(port=5000)
