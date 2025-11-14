from google.genai import Client as GoogleClient

from .agent import run_agent
from .utils import load_env_file, print_pucky_header

load_env_file()


def main():
    print_pucky_header()

    # Remember to set GOOGLE_API_KEY in your .env file as explained in the README
    google_client = GoogleClient()
    run_agent(google_client)


if __name__ == "__main__":
    main()
