import json
import os
from datetime import datetime
from pprint import pprint
from typing import Callable

from dotenv import load_dotenv
from humanloop import Humanloop
from slack_bolt.adapter.socket_mode import SocketModeHandler

from tools.feedback import log_user_feedback
from tools.linear import create_linear_issue, list_linear_teams
from tools.slack import message_user, no_action, slack, web_client
from tools.utils import call_tool, parse_function

load_dotenv()

HUMANLOOP_API_KEY = os.getenv("HUMANLOOP_API_KEY")
humanloop = Humanloop(api_key=HUMANLOOP_API_KEY)

ENABLED_TOOLS = [
    no_action,
    message_user,
    create_linear_issue,
    list_linear_teams,
    log_user_feedback,
]
ENABLED_CHANNELS = ["C05H2KT4LP5", "C05RKHTR0LQ"]  # bugs  # coworker-testing


tool_schemas = [parse_function(t) for t in ENABLED_TOOLS]


@slack.event("team_join")
def team_join(body, say):
    print("team_join")
    pprint(body)


# TODO: these events might have different structures
@slack.event("app_mention")
@slack.event("message")
def respond_to_messages(body: dict, say: Callable[[str], None]):
    print(f"EVENT TYPE: {body['event']['type']}")

    # Ignore bot messages and deletions
    if "subtype" in body["event"] and body["event"]["subtype"] in [
        "bot_message",
        "message_deleted",
    ]:
        return

    channel = body["event"]["channel"]
    if channel not in ENABLED_CHANNELS:
        return

    message_ts = body["event"]["ts"]  # timestamp of the message
    # If the message is in a thread, this field will be populated
    thread_ts = body["event"].get("thread_ts")

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

    print("\n\n")
    pprint([msg[:40] for msg in formatted_messages])
    print("\n\n")
    # The current message is the top one in the list
    current_message = formatted_messages[0]

    # Join the messages to form the history string
    # Excluding the current message and go from oldest to newest
    history = "\n".join(formatted_messages[1:][::-1])
    response = humanloop.chat(
        project="coworker/Brain",
        model_config={
            "tools": tool_schemas,
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

    helpers = {
        "web_client": web_client,
        "channel": channel,
        "thread_ts": thread_ts,
        "response_message": response_message,
    }

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
            tool_response = call_tool(tool_name, args, ENABLED_TOOLS, helpers)
            print(f"Tool Response: {tool_response}")
            new_message_text = tool_response

    else:
        print("TOOL NOT CALLED")
        new_message_text = chat_response["output"]

    if new_message_text == "no_action":
        web_client.chat_delete(
            channel=channel,
            ts=response_message["ts"],
        )
    else:
        web_client.chat_update(
            channel=channel,
            ts=response_message["ts"],
            text=new_message_text,
            thread_ts=thread_ts,
        )


if __name__ == "__main__":
    handler = SocketModeHandler(slack, os.getenv("SLACK_APP_TOKEN"))
    handler.start()
