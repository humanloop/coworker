import os
from datetime import datetime

from dotenv import load_dotenv
from humanloop import Humanloop
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from pprint import pprint

load_dotenv()

app = App(token=os.getenv("SLACK_BOT_TOKEN"))
web_client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
HUMANLOOP_API_KEY = os.getenv("HUMANLOOP_API_KEY")

humanloop = Humanloop(api_key=HUMANLOOP_API_KEY)


@app.event("message")
def respond_to_messages(body, say):
    text = body["event"]["text"]
    channel = body["event"]["channel"]

    # Fetch the most recent 10 messages including the current one
    history_response = web_client.conversations_history(
        channel=channel, limit=11  # 10 previous messages + the current one
    )

    formatted_messages = []
    for msg in history_response["messages"]:
        user = msg["user"]
        timestamp = msg["ts"]  # Slack uses 'ts' for timestamps
        content = msg["text"]

        # Convert timestamp to human-readable format
        # Slack's 'ts' is a string like '1623431161.000200' which you can split at the dot and use the left part
        readable_timestamp = datetime.utcfromtimestamp(
            float(timestamp.split(".")[0])
        ).strftime("%Y-%m-%d %H:%M:%S UTC")

        formatted_message = f"{readable_timestamp} - {user}: {content}"
        formatted_messages.append(formatted_message)

    formatted_messages.reverse()  # Reverse to maintain chronological order

    # The current message is the last one in the list
    current_message = formatted_messages[-1]

    # Join the messages to form the history string
    history = "\n".join(formatted_messages[:-1])  # Excluding the current message

    response = humanloop.chat_deployed(
        project="coworker/Brain",
        model_config={
            "model": "gpt-4",
            "chat_template": """You are an AI agent that orchestrates other AI agents and organises tasks in slack.

You read every message that flows through slack. If you think you can  do something useful, you initiate that action. The only way for you to interact with the user is by using the functions:

1.  message_user
2. linear_ticket
3. store_user_feedback
3. no_task

Before taking any action you should always send a message to the user with your suggested next step and only do the actual task execution if you get their confirmation. 

The majority of messages should use the "no_task" function. Only use a different function if you're very sure it will be useful. We want to avoid bothering users.

recent_chat_history
###
{{history}}
###

current_message_to_analyse:
###
{{message}}
###""",
        },
        inputs={"history": history, "message": current_message},
        messages=[{"role": "user", "content": current_message}],
    )
    pprint(response.body)

    humanloop_response = response.body["data"][0]["output"]
    say(text=humanloop_response)


if __name__ == "__main__":
    handler = SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN"))
    handler.start()
