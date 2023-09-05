import os
from pprint import pprint
from datetime import datetime

from dotenv import load_dotenv
from humanloop import Humanloop
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from pprint import pprint

from tools.linear import create_linear_issue, list_linear_teams
from tools.slack import message_user, no_action
from tools.utils import call_tool, parse_function

load_dotenv()

HUMANLOOP_API_KEY = os.getenv("HUMANLOOP_API_KEY")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

app = App(token=os.getenv("SLACK_BOT_TOKEN"))
web_client = WebClient(token=SLACK_BOT_TOKEN)
humanloop = Humanloop(api_key=HUMANLOOP_API_KEY)


tool_list = [create_linear_issue, list_linear_teams, no_action, message_user]
tools = [parse_function(t) for t in tool_list]


@app.event("app_home_opened")
def handle_app_home_opened_events(body, logger):
    logger.info(body)


@app.event("team_join")
def team_join(body, say):
    print("team_join")
    pprint(body)


@app.event("app_home_opened")
def app_home_opened():
    print("app home opened")


@app.event("app_mention")
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
        user = msg["user"]  # User is like 'U0124SFJGAD'
        timestamp = msg["ts"]  # Slack uses 'ts' for timestamps
        content = msg["text"]

        # Convert timestamp to human-readable format
        # Slack's 'ts' is a string like '1623431161.000200' which you can split at the
        # dot and use the left part
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
    pprint(tools)
    response = humanloop.chat(
        project="coworker/Brain",
        model_config={
            "tools": tools,
            "model": "gpt-4",
            "max_tokens": -1,
            "temperature": 0.7,
            "chat_template": [
                {
                    "role": "system",
                    "content": """
You are an AI agent that orchestrates other AI agents and organises tasks in Slack.

You read every message that flows through Slack. If you think you can do something useful, you initiate that action. 
The only way for you to interact with the user is by using the functions provided.

Before taking any action you should always send a message to the user with your 
suggested next step and only do the actual task execution if you get their confirmation.

The majority of messages should use the "no_action" function. Only use a different 
function if you're very sure it will be useful as wse want to avoid bothering users. 

ONLY CALL A FUNCTION, DO NOT RESPOND WITH TEXT.

recent_chat_history:
###
{{history}}
###

current_message_to_analyse:
###
{{message}}
###""",
                }
            ],
        },
        inputs={"history": history, "message": current_message},
        messages=[],
    )

    chat_response = response.body["data"][0]

    pprint(chat_response)

    if chat_response["finish_reason"] == "tool_call":
        tool_name = chat_response["tool_call"]["name"]
        if tool_name == "message_user":
            slack_bot_response = chat_response["tool_call"]
            say(text=slack_bot_response)
        elif tool_name == "no_action":
            pprint("No action.")
            pass
        else:
            args = chat_response["tool_call"]["arguments"]
            call_tool(tool_name, args, tool_list)
            say(text=args)
    else:
        # We want to force it to use a tool
        # for now we'll just say the response.
        print("TOOL NOT CALLED")
        say(text=chat_response["output"])


if __name__ == "__main__":
    handler = SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN"))
    handler.start()
