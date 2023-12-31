"""Slack API helper functions"""
import json
import os
from pprint import pprint
from typing import Dict

from dotenv import load_dotenv
from slack_bolt import App
from slack_sdk import WebClient

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
web_client = WebClient(token=SLACK_BOT_TOKEN)


def no_action() -> str:
    """No action needs to be taken"""
    return ""


def message_user(message: str) -> str:
    """Sends a message to the user offering to help them or confirming any detals."""
    # This doesn't actually do anything here, because we still do this in main. It's
    # just for signature and docstring here.
    return message


def list_channels() -> str:
    """List the channels in the workspace"""
    cursor = None
    channels = {}
    while True:
        response = web_client.conversations_list(
            cursor=cursor, limit=100, exclude_archived=True, types="public_channel"
        )
        if response["ok"]:
            for channel in response["channels"]:
                channels[channel["name"]] = channel
            cursor = response["response_metadata"]["next_cursor"]
            print(cursor)
            if not cursor:
                break
        else:
            print(f'Error: {response["error"]}')
            break
    return json.dumps([f"{k} {v['id']}" for k, v in channels.items()])


def _list_users() -> Dict[str, Dict]:
    cursor = None
    users = {}
    while True:
        response = web_client.users_list(cursor=cursor, limit=200)
        if response["ok"]:
            for user in response.get("members", []):
                # Filter out bots and deleted users
                if not user.get("is_bot") and not user.get("deleted"):
                    users[user["id"]] = user
            cursor = response["response_metadata"]["next_cursor"]
            if not cursor:
                break
        else:
            print(f'Error: {response["error"]}')
            break
    return users


def list_users() -> str:
    """List the users in the workspace"""
    return json.dumps([f"{k} {v['name']}" for k, v in _list_users().items()])


if __name__ == "__main__":
    # pprint(list_channels())
    pprint(list_users())
