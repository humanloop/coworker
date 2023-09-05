"""Functions for interacting with Linear"""
import os
from typing import List
from dotenv import load_dotenv
import requests
import json
from pprint import pprint

load_dotenv()
LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")


def create_linear_issue(
    title: str,
    description: str,
    team_id: str,
    priority: str,
):
    """Create an issue in Linear.

    Args:
        title (str): The title of the issue
        description (str): The description of the issue
        team_id (str): The 36 char ID of the team to create the issue in
        priority (str): The priority of the issue
        labels (List[str]): The labels to apply to the issue

    """
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


def list_linear_teams():
    """List the IDs of the teams in Linear"""
    url = "https://api.linear.app/graphql"
    headers = {"Authorization": LINEAR_API_KEY, "Content-Type": "application/json"}

    query = """
    query {
      teams {
        nodes {
          id
          name
        }
      }
    }
    """

    response = requests.post(url, headers=headers, json={"query": query})

    if response.status_code == 200:
        teams_data = (
            json.loads(response.text).get("data", {}).get("teams", {}).get("nodes", [])
        )
        return teams_data
    else:
        raise Exception(f"Failed to list teams: {response.text}")


if __name__ == "__main__":
    teams = list_linear_teams()
    for team in teams:
        print(f"ID: {team['id']}, Name: {team['name']}")

    create_linear_issue(
        title="Test issue",
        description="This is a test issue",
        team_id="a71e2092-2815-4546-8254-00f7ed3f4068",
        priority="HIGH",
        labels=["label1", "label2"],
        assignee="assignee",
    )
