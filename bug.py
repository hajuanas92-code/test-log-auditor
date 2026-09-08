import os
import sys
import socket
import traceback
from dotenv import load_dotenv
import google.cloud.logging

# ----------------------------------------------------------------------
# Load environment variables
# ----------------------------------------------------------------------
load_dotenv()

# ----------------------------------------------------------------------
# Initialise Cloud Logging client
# ----------------------------------------------------------------------
client = google.cloud.logging.Client()
logger = client.logger("buggy-app")


def connect_to_database():
    """
    Attempt to open a TCP connection to the configured database.
    Returns the socket object on success, otherwise raises a RuntimeError
    with a clear, user‑friendly message.
    """
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", "5999"))
    print(f"Connecting to database at {db_host}:{db_port} ...")

    try:
        sock = socket.create_connection((db_host, db_port), timeout=3)
        return sock
    except (ConnectionRefusedError, socket.timeout) as exc:
        # Wrap the low‑level socket error in a higher‑level exception
        raise RuntimeError(
            f"Unable to connect to database at {db_host}:{db_port}. "
            "Verify that the service is running and the host/port are correct."
        ) from exc


def load_api_config():
    """
    Retrieve the external API key from the environment.
    Raises a RuntimeError with a helpful message if the variable is missing.
    """
    api_key = os.getenv("EXTERNAL_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Environment variable 'EXTERNAL_API_KEY' is not set. "
            "Set it before running the application."
        )
    return api_key


def log_error(e: Exception):
    """
    Log the exception stack trace locally and to Cloud Logging.
    """
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