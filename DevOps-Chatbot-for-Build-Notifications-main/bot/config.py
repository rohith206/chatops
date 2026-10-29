import os

from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET", "")
SLACK_DEFAULT_CHANNEL = os.getenv("SLACK_DEFAULT_CHANNEL", "#builds")

JENKINS_URL = os.getenv("JENKINS_URL", "").rstrip("/")
JENKINS_USER = os.getenv("JENKINS_USER", "")
JENKINS_API_TOKEN = os.getenv("JENKINS_API_TOKEN", "")

# Shared secret Jenkins must send in the X-Webhook-Token header
WEBHOOK_TOKEN = os.getenv("WEBHOOK_TOKEN", "")

# Optional per-job channel routing, e.g. "api-deploy=#api-team,web-build=#web-team"
CHANNEL_MAP = dict(
    pair.split("=", 1)
    for pair in os.getenv("CHANNEL_MAP", "").split(",")
    if "=" in pair
)
