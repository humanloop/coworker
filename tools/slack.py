"""Slack API helper functions"""
import os
from pprint import pprint
from dotenv import load_dotenv

from slack_bolt import App
from slack_sdk import WebClient


load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

slack = App(token=os.getenv("SLACK_BOT_TOKEN"))
web_client = WebClient(token=SLACK_BOT_TOKEN)


def no_action():
    """No action needs to be taken"""
    pass


def message_user(message: str):
    """Sends a message to the user offering to help them or confirming any detals."""
    # This doesn't actually do anything here, because we still do this in main. It's
    # just for signature and docstring here.
    pass


def list_channels():
    """List the channels in the workspace"""
    cursor = None
    channels = {}
    while True:
        response = web_client.conversations_list(cursor=cursor)
        if response["ok"]:
            for channel in response["channels"]:
                channels[channel["name"]] = channel
            cursor = response["response_metadata"]["next_cursor"]
            if not cursor:
                break
        else:
            print(f'Error: {response["error"]}')
            break
    return channels


if __name__ == "__main__":
    pprint([f"{k} {v['id']}" for k, v in list_channels().items()])
