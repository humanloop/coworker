Coworker
===========

Your AI Coworker that lives in Slack.

Coworker is an open source framework for practical, helpful AI assistants. It lives in Slack, will have access to your docs (as you allow) and can take actions in your various tools.


Principles
----------

1. **Context Aware** - Unlike other AI chatbots, it should have knowledge of your context. The conversation your having, the background goals at your company etc.

2. **Extensible** - It should be extremely easy for a developer to add a new capability to the coworker that's relevant for their company.
3. **Human in the loop** - We want to give Coworker really powerful capabilities. To do that in a way that maintains trust, it should be transparent to a user what the AI is doing and always get approval for its actions.

Setup
------

To get this working, you need to setup a new Slack App, get API keys for any tools you want to use e.g. Linear, Notion etc, and get Humanloop/OpenAI keys for the AI.



**Slack App Setup**

1. Create a New App:
    1. Go to https://api.slack.com/apps and click on “Create New App”.
    2. Give it a name and select the workspace you want to install it to.
    3. Click “Create App”.
2. Permissions:
    1. In the sidebar, navigate to “OAuth & Permissions”.
    2. Under “Scopes”, add the following bot token scopes: `app_mentions:read`, `channels:history`, `chat:write`, `im:history`
    3. Install the app to your workspace by clicking “Install App”.
    4. Find the “Bot User OAuth Token”. This is your `SLACK_BOT_TOKEN` which starts with `xoxb-`.
3. Enable Socket Mode:
    1. In the sidebar, navigate to “Socket Mode”.
    2. Turn on “Enable Socket Mode”.
    3. Generate a new token under “App-Level Tokens”. This is your `SLACK_APP_TOKEN` which starts with `xapp-`.


**Set up a Humanloop / OpenAI account for the AI**

1. Go to https://humanloop.com/signup, and start a free trial
2. Get your `HUMANLOOP_API_TOKEN` from `https://app.humanloop.com/account/api-keys`
3. Get your `OPENAI_API_TOKEN` from https://platform.openai.com/account/api-keys 


**Choose channels the AI should be in, and what tools it has access to**

1. 

Running locally
---------------
1. Clone this repo
2. Copy `.env.example`` to `.env` and fill in the values
3. `poetry install`
4. `poetry run python coworker.py`



Deployment
----------

You can run this locally indefintely, but if you want to deploy, we recommend using Railway.app.

Just fork this repo, and create a new deployment in Railway linked to that repo.

You will need to set up your Environment variables only. 



Privacy
-------
You set this up yourself, with your own Humanloop account and your own OpenAI (or other LLM provider) keys. The data is private to you
and as this will be using the OpenAI API, this is actually a more privacy preserving approach than using ChatGPT directly as
you data will not be used in future training runs of OpenAI's models.



Road Map
--------


- [x] GPT-4 bot that can read all messages in slack and responds when appropriate
- [x] Ability to recognise conversation about a bug and offer to write a Linear ticket then do it
- [x] Ability to recognise conversation about user feedback and save it to a central place
- [] Make the AI responses be in threads so as to avoid cluttering the main feed
- [] Ask for permission to do things
- [] Add more knowledge sources like Notion, Drive or Email (could use something like SID to handle access permissions)
- [] Daily/Weekly summaries of the most important conversations had for engineering, product and sales
- [] Inegrations with meeting note-takes like Fathom or Otter so that the AI can answer questions
- [] Integration with a vector database or similar that the model can read and write from to maintain long term memory











