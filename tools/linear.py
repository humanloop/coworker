"""Functions for interacting with Linear"""
import json
import os
from pprint import pprint

import requests
from dotenv import load_dotenv

load_dotenv()
LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
LINEAR_TEAM_ID = "a71e2092-2815-4546-8254-00f7ed3f4068"


def create_linear_issue(
    title: str,
    description: str,
    confirmed: bool,
    priority: int = 0,
) -> str:
    """Create an issue in Linear.

    Args:
        title (str): The title of the issue
        description (str): The description of the issue
        priority (int): The priority of the issue either None (0), High (1), Medium (2), or Low (3)
        labels (List[str]): The labels to apply to the issue 
        confirmed (bool): Whether the user has confirmed the details of the issue \
          as in they have seen the full json arguments and accepted (default False)
    """
    url = "https://api.linear.app/graphql"
    headers = {"Authorization": LINEAR_API_KEY, "Content-Type": "application/json"}

    query = """
mutation CreateIssue(
    $title: String!, 
    $description: String, 
    $teamId: String!, 
    $priority: Int 
) {
    issueCreate(input: {
    title: $title,
    description: $description,
    teamId: $teamId,
    priority: $priority,
    }) {
    success
    issue {
        id
        title
        description
        priority
        url
    }
    }
}
    """

    variables = {
        "title": title,
        "description": description,
        "teamId": LINEAR_TEAM_ID,
        "priority": int(priority),
    }
    pprint(variables)
    if not confirmed:
        return f"""Create issue with the following details?\n
*Title:* {title}\n*Description:* {description}\n*Priority:* {priority}"""

    response = requests.post(
        url, headers=headers, json={"query": query, "variables": variables}
    )

    if response.status_code == 200:
        response_data = json.loads(response.text)
        issue_data = (
            response_data.get("data", {}).get("issueCreate", {}).get("issue", {})
        )
        if issue_data:
            issue_title = issue_data.get("title")
            issue_description = issue_data.get("description")
            issue_url = issue_data.get("url")
            return f"Issue Created: *<{issue_url}|{issue_title}>*\nDescription: {issue_description}"
    return f"Failed to create issue: {response.text}"


def list_linear_teams() -> str:
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
        return json.dumps(teams_data, indent=2)
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
