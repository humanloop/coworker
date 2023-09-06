import json
import os
from pprint import pprint
from datetime import datetime
from typing import Callable

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


tool_list = [
    no_action,
    message_user,
    create_linear_issue,
    list_linear_teams,
]
tools = [parse_function(t) for t in tool_list]


@app.event("team_join")
def team_join(body, say):
    print("team_join")
    pprint(body)


# Listener middleware to fetch tasks from external system using user ID
def fetch_tasks(context, event, next):
    user = event["user"]
    try:
        # Assume get_tasks fetchs list of tasks from DB corresponding to user ID
        user_tasks = ["go outside", "touch grass"]
        tasks = user_tasks
    except Exception:
        # get_tasks() raises exception because no tasks are found
        tasks = []
    finally:
        # Put user's tasks in context
        context["tasks"] = tasks
        next()


# Listener middleware to create a list of section blocks
def create_sections(context, next):
    task_blocks = []
    # Loops through tasks added to context in previous middleware
    for task in context["tasks"]:
        task_blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{task}\n",
                },
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "See task"},
                    "url": "https://sf.com",
                },
            }
        )
    # Put list of blocks in context
    context["blocks"] = task_blocks
    next()


# Listen for user opening app home
# Include fetch_tasks middleware
@app.event(event="app_home_opened", middleware=[fetch_tasks, create_sections])
def show_tasks(event, client, context):
    print("app_home_opened")
    # Publish view to user's home tab
    client.views_publish(
        user_id=event["user"], view={"type": "home", "blocks": context["blocks"]}
    )


# Listener middleware which filters out messages with "bot_message" subtype
def no_bot_messages(message, next):
    subtype = message.get("subtype")
    if subtype != "bot_message":
        next()


def ignore_deletions(message, next):
    subtype = message.get("subtype")
    if subtype != "message_deleted":
        next()


# TODO: these events might have different structures
@app.event("app_mention", middleware=[no_bot_messages])
@app.event("message", middleware=[no_bot_messages, ignore_deletions])
def respond_to_messages(body: dict, say: Callable[[str], None]):
    channel = body["event"]["channel"]
    # Timestamps
    thread_ts = body["event"].get(
        "thread_ts"
    )  # If the message is in a thread, this field will be populated
    message_ts = body["event"]["ts"]  # timestamp of the message

    # Acknowledge first
    response_message = say(
        text="Thinking...",
        thread_ts=thread_ts if thread_ts else message_ts,
    )

    total_limit = 11
    context_messages = []

    # Step 1: Fetch threaded messages if available
    if thread_ts:
        print("thread_ts")
        replies = web_client.conversations_replies(
            channel=channel,
            ts=thread_ts,
            limit=total_limit - 1,
            # This is to ignore any added message that we've put in the thread
            # TODO: maybe it's better to filter out the bot? Just in case we want to
            # include any other messages that have been added.
            latest=message_ts,
            inclusive=True,
        )
        context_messages += reversed(replies["messages"])
        context_messages += [
            {"user": "end-of-thread", "ts": "0", "text": "------------"}
        ]

    # Step 2: Fetch parent-level messages
    if total_limit - len(context_messages) > 0:
        history = web_client.conversations_history(
            channel=channel,
            limit=total_limit - len(context_messages),
            latest=thread_ts if thread_ts else message_ts,
            # Avoiding having the parent message in the list if we've got that from the thread
            inclusive=False if thread_ts else True,
        )
        context_messages += history["messages"]

    formatted_messages = []
    for msg in context_messages:
        user = msg["user"]  # User is like 'U0124SFJGAD'
        timestamp = msg["ts"]  # Slack uses 'ts' for timestamps
        content = msg["text"]

        # Convert timestamp to human-readable format
        # Slack's 'ts' is a string like '1623431161.000200' which you can split at the
        # dot and use the left part
        readable_timestamp = datetime.utcfromtimestamp(
            float(timestamp.split(".")[0])
        ).strftime("%Y-%m-%d %H:%M:%S UTC")

        formatted_messages.append(f"{content} [{user} @ {readable_timestamp}]")

    print("\n\n\n")
    pprint([msg[:40] for msg in formatted_messages])
    print("\n\n\n")
    # The current message is the top one in the list
    current_message = formatted_messages[0]

    # Join the messages to form the history string
    # Excluding the current message and go from oldest to newest
    history = "\n".join(formatted_messages[1:][::-1])
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

""",
                },
                {"role": "user", "name": user, "content": current_message},
            ],
        },
        inputs={"history": history},
        messages=[],
    )

    chat_response = response.body["data"][0]

    # Update the initial message
    if chat_response["finish_reason"] == "tool_call":
        tool_name = chat_response["tool_call"]["name"]
        args = json.loads(chat_response["tool_call"]["arguments"])
        if tool_name == "message_user":
            new_message_text = args["message"]
        elif tool_name == "no_action":
            new_message_text = "no_action"
            pprint("No action.")
            pass
        else:
            # TODO: make the say function add to the thread.
            tool_response = call_tool(tool_name, args, tool_list, say)
            print(f"Tool Response: {tool_response}")
            new_message_text = tool_response

    else:
        print("TOOL NOT CALLED")
        new_message_text = chat_response["output"]

    if new_message_text == "no_action":
        # Delete the message
        web_client.chat_delete(
            channel=channel,
            ts=response_message["ts"],
        )
    else:
        web_client.chat_update(
            channel=channel,
            ts=response_message["ts"],
            text=new_message_text,
            # thread_ts=thread_ts,  # Keep the thread # Not sure what this does
        )


if __name__ == "__main__":
    handler = SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN"))
    handler.start()
