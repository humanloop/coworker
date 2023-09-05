"""Functions for interacting with Linear"""
import os
from dotenv import load_dotenv
import requests
import json
from pprint import pprint

load_dotenv()
LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")


def create_linear_issue(title, description, team_id, priority, labels, assignee):
    """Create an issue in Linear"""
    url = "https://api.linear.app/graphql"
    headers = {"Authorization": LINEAR_API_KEY, "Content-Type": "application/json"}

    query = """
    mutation CreateIssue($title: String!, $description: String, $teamId: String!) {
      issueCreate(input: {
        title: $title,
        description: $description,
        teamId: $teamId
      }) {
        success
        issue {
          id
          title
          description
        }
      }
    }
    """

    variables = {"title": title, "description": description, "teamId": team_id}

    response = requests.post(
        url, headers=headers, json={"query": query, "variables": variables}
    )

    if response.status_code == 200:
        pprint(response.text)

        return json.loads(response.text)
    else:
        raise Exception(f"Failed to create issue: {response.text}")


if __name__ == "__main__":
    create_linear_issue(
        title="Test issue",
        description="This is a test issue",
        team_id="HUM",
        priority="HIGH",
        labels=["label1", "label2"],
        assignee="assignee",
    )
