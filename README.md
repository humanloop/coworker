Coworker
===========

Your AI Coworker that lives in Slack.

Coworker is an open source framework for practical, helpful AI assistants. It lives in Slack, will have access to your docs (as you allow) and can take actions in your various tools.


Principles
----------

1. **Simple** - The base framework here is simple. Message comes in, AI decides what action to take.
2. **Extensible** - Coworker should be transparent about what it is doing and why. It should be easy to see what it is doing and why.
3. **Human in the loop** - Coworker should be able to ask for help from a human when it is unsure of what to do. 

Setup
------

1. Create a Slack app and install it in your workspace

Go to api.slack.com


Running locally
---------------



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


[x] GPT-4 bot that can read all messages in slack and responds when appropriate
[x] Ability to recognise conversation about a bug and offer to write a Linear ticket then do it
[x] Ability to recognise conversation about user feedback and save it to a central place
[] Make the AI responses be in threads so as to avoid cluttering the main feed
[] Ask for permission to do things
[] Add more knowledge sources like Notion, Drive or Email (could use something like SID to handle access permissions)
[] Daily/Weekly summaries of the most important conversations had for engineering, product and sales
[] Inegrations with meeting note-takes like Fathom or Otter so that the AI can answer questions
[] Integration with a vector database or similar that the model can read and write from to maintain long term memory











