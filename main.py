import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

# Initialize OpenAI and Slack bot
app = App(token=os.getenv("SLACK_BOT_TOKEN"))


@app.event("app_mention")
def respond_to_messages(body, say):
    # Get the message content
    text = body["event"]["text"]
    channel = body["event"]["channel"]
    say(text="hello")


@app.event("message")
def respond_to_messages(body, say):
    # Get the message content
    text = body["event"]["text"]
    channel = body["event"]["channel"]
    say(text="hello")


if __name__ == "__main__":
    handler = SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN"))
    handler.start()
