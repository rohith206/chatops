"""Turns a build event into a Slack message (Block Kit)."""

STATUS_STYLE = {
    "SUCCESS": ("✅", "#2eb886"),
    "FAILURE": ("❌", "#e01e5a"),
    "UNSTABLE": ("⚠️", "#ecb22e"),
    "ABORTED": ("⛔", "#999999"),
    "STARTED": ("🚀", "#439fe0"),
}


def normalize(payload: dict) -> dict:
    """Accept Jenkins Notification-plugin JSON or a simple custom payload."""
    build = payload.get("build", {})
    phase = build.get("phase", "")
    status = build.get("status") or payload.get("status") or ""
    if phase == "STARTED":
        status = "STARTED"
    return {
        "job": payload.get("name") or payload.get("job", "unknown-job"),
        "number": build.get("number") or payload.get("number", "?"),
        "status": status.upper() or "UNKNOWN",
        "url": build.get("full_url") or payload.get("url", ""),
        "branch": payload.get("branch") or build.get("scm", {}).get("branch", ""),
        "env": payload.get("env", ""),
    }


def build_message(event: dict) -> dict:
    icon, color = STATUS_STYLE.get(event["status"], ("ℹ️", "#cccccc"))
    title = f"{icon} *{event['job']}* #{event['number']} — {event['status']}"
    details = [f"*Branch:* {event['branch']}" if event["branch"] else "",
               f"*Env:* {event['env']}" if event["env"] else ""]
    text = "\n".join([title, "  ".join(d for d in details if d)]).strip()
    if event["url"]:
        text += f"\n<{event['url']}|View build>"
    return {
        "text": title,  # fallback for notifications
        "attachments": [{"color": color, "text": text}],
    }
