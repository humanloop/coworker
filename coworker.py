import json
import os
from datetime import datetime
from pprint import pprint
from typing import Callable, Optional

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


class Message:
    role: str
    name: Optional[str]
    content: str


tool_schemas = [parse_function(t) for t in ENABLED_TOOLS]


@slack.event("team_join")
def team_join(body, say):
    print("team_join")
    pprint(body)


@slack.event("app_home_opened")
def handle_app_home_opened_events(body, logger):
    print(f"EVENT TYPE: {body['event']['type']}")


@slack.event("message")
def handle_message(body: dict, say: Callable[[str], None]):
    """A message was sent to a channel"""
    print(
        f"EVENT TYPE: {body['event']['type']}  {body['event']['subtype'] if 'subtype' in body['event'] else ''}"  # noqa: E501
    )
    # Ignore bot messages and deletions
    if "subtype" in body["event"] and body["event"]["subtype"] in [
        "bot_message",
        "message_deleted",
        "message_changed",
    ]:
        return

    # If in public channels (not a DM) check if the channel is enabled
    if body["event"]["channel_type"] == "channel":
        if body["event"]["channel"] not in ENABLED_CHANNELS:
            return

    return respond(body, say)


@slack.event("app_mention")
def handle_app_mentions(body: dict, say: Callable[[str], None]):
    print(f"EVENT TYPE: {body['event']['type']}")

    # Ignore bot messages and deletions
    if "subtype" in body["event"] and body["event"]["subtype"] in [
        "bot_message",
        "message_deleted",
    ]:
        return "OK"
    return respond(body, say)


def respond(body: dict, say: Callable[[str], None]):
    message_ts = body["event"]["ts"]  # timestamp of the message
    # If the message is in a thread, this field will be populated
    thread_ts = body["event"].get("thread_ts")
    channel = body["event"]["channel"]

    # # Acknowledge first
    # response_message = say(
    #     text="Thinking...",
    #     thread_ts=thread_ts if thread_ts else message_ts,
    # )

    total_limit = 11
    context_messages = []

    # Step 1: Fetch threaded messages if we're in a thread
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

The majority of messages should use the "no_action" function. Only use a different 
function if you're very sure it will be useful as wse want to avoid bothering users. 

ONLY CALL A FUNCTION, DO NOT RESPOND WITH TEXT. DEFAULT TO CALLING `no_action`.

recent_chat_history:
###
{{history}}
###

""",
                },
            ],
        },
        inputs={"history": history},
        messages=[
            {"role": "user", "name": user, "content": formatted_messages[0]},
        ],
    )

    chat_response = response.body["data"][0]

    print(chat_response)
    if chat_response["finish_reason"] == "tool_call":
        tool_name = chat_response["tool_call"]["name"]
        args = json.loads(chat_response["tool_call"]["arguments"])
        new_message_text = call_tool(tool_name, args, ENABLED_TOOLS)
    else:
        # This shouldn't happen if it respects the prompt
        print("TOOL NOT CALLED")
        new_message_text = chat_response["output"]

    print("→ ", new_message_text)
    if new_message_text:
        # web_client.chat_update(
        #     channel=channel,
        #     ts=response_message["ts"],
        #     text=new_message_text,
        #     thread_ts=thread_ts,
        # )
        web_client.chat_postMessage(
            channel=channel,
            text=new_message_text,
            thread_ts=thread_ts if thread_ts else message_ts,
        )

    # else:
    # web_client.chat_delete(channel=channel, ts=response_message["ts"])
    return "OK"


if __name__ == "__main__":
    handler = SocketModeHandler(slack, os.getenv("SLACK_APP_TOKEN"))
    handler.start()
