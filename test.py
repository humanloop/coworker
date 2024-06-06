# """Test that the connection to Humanloop is OK."""

import json
import os
from datetime import datetime
from pprint import pprint

from dotenv import load_dotenv
from humanloop import Humanloop

load_dotenv()

HUMANLOOP_API_KEY = os.getenv("HUMANLOOP_API_KEY")
humanloop = Humanloop(api_key=HUMANLOOP_API_KEY, host="https://neostaging.humanloop.ml/v4")


if __name__ == "__main__":
    print(humanloop.projects.list())