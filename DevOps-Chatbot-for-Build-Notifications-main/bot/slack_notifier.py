from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

import config
from formatter import build_message

client = WebClient(token=config.SLACK_BOT_TOKEN)


def channel_for(job: str) -> str:
    return config.CHANNEL_MAP.get(job, config.SLACK_DEFAULT_CHANNEL)


def notify(event: dict) -> bool:
    msg = build_message(event)
    try:
        client.chat_postMessage(channel=channel_for(event["job"]), **msg)
        return True
    except SlackApiError as e:
        print(f"Slack error: {e.response['error']}")
        return False
