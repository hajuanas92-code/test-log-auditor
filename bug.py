import socket
import traceback
import os
import sys
from dotenv import load_dotenv
import google.cloud.logging

load_dotenv()

client = google.cloud.logging.Client()
logger = client.logger("buggy-app")

def connect_to_database():
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", "5999"))
    print(f"Connecting to database at {db_host}:{db_port} ...")
    sock = socket.create_connection((db_host, db_port), timeout=3)
    return sock


def load_api_config():
    api_key = os.environ["EXTERNAL_API_KEY"]  # deliberately not set
    return api_key


def log_error(e: Exception):
    stack_trace = traceback.format_exc()
    print("ERROR OCCURRED:")
    print(stack_trace)

    logger.log_struct(
        {
            "message": str(e),
            "stack_trace": stack_trace,
        },
        severity="ERROR",
    )
    print("Error logged to Cloud Logging.")


def main():
    bug_type = sys.argv[1] if len(sys.argv) > 1 else "db"

    if bug_type == "db":
        try:
            connect_to_database()
            print("Connected successfully!")
        except Exception as e:
            log_error(e)

    elif bug_type == "api":
        try:
            load_api_config()
            print("API config loaded successfully!")
        except Exception as e:
            log_error(e)

    else:
        print(f"Unknown bug type: {bug_type}. Use 'db' or 'api'.")


if __name__ == "__main__":
    main()