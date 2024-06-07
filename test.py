# """Test that the connections are OK."""

import json
import os
from datetime import datetime
from pprint import pprint

from dotenv import load_dotenv
from humanloop import Humanloop
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient

from tools.slack import list_channels

load_dotenv()
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
slack_client = WebClient(token=SLACK_BOT_TOKEN)
app = App(token=SLACK_BOT_TOKEN)


load_dotenv()

HUMANLOOP_API_KEY = os.getenv("HUMANLOOP_API_KEY")
humanloop = Humanloop(api_key=HUMANLOOP_API_KEY, host="https://neostaging.humanloop.ml/v4")


if __name__ == "__main__":
    pprint(humanloop.projects.list())
    pprint(list_channels())

