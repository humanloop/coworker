FEEDBACK_FILE_PATH: str = "tools/feedback.csv"


def log_user_feedback(
    company_name: str,
    description: str,
    urgency: str,
    category: str,
    date: str,
):
    """Records user feedback from customers so that it can be later used
    to inform product roadmaps.

      Args
        company_name (str): Name of the company that provided the feedback if known.

        description (str): Description of the user feedback.

        urgency (str): Urgency level of the feedback.

        category (str): Category of the feedback.

        date(str): Date of feedback

      Returns:
        None"""

    with open(FEEDBACK_FILE_PATH, "a") as file:
        file.write(f"{company_name},{description},{urgency},{category},{date}\n")

    return f"Logged feedback.\n *Company Name:* {company_name}\n *Description:* {description}\n *Urgency:* {urgency}\n *Category:* {category}\n *Date:* {date}"

def read_feedback(
):
    """Read existing feedback

      Returns:
        str: Feedback"""

    with open(FEEDBACK_FILE_PATH, "r") as file:
        feedback = file.read()

    return feedback
