import socket
import traceback
import os
from dotenv import load_dotenv
import google.cloud.logging
from google.cloud.logging_v2.resource import Resource

load_dotenv()

# Set up Cloud Logging client (uses GOOGLE_APPLICATION_CREDENTIALS from .env)
client = google.cloud.logging.Client()
logger = client.logger("buggy-app")


def connect_to_database():
    """
    Establish a TCP connection to the configured database.
    The default values now point to a typical PostgreSQL instance (port 5432).
    If the connection cannot be made, a clear exception is raised and logged.
    """
    db_host = os.getenv("DB_HOST", "localhost")
    # Use a realistic default port; override via DB_PORT env var if needed.
    db_port = int(os.getenv("DB_PORT", "5432"))

    print(f"Connecting to database at {db_host}:{db_port} ...")
    try:
        # Attempt the connection with a short timeout.
        sock = socket.create_connection((db_host, db_port), timeout=5)
        return sock
    except Exception as conn_err:
        # Wrap the original exception with a more helpful message.
        raise ConnectionError(
            f"Unable to connect to database at {db_host}:{db_port}. "
            f"Ensure the service is running and the host/port are correct."
        ) from conn_err


def main():
    try:
        connect_to_database()
        print("Connected successfully!")
    except Exception as e:
        error_message = str(e)
        stack_trace = traceback.format_exc()

        print("ERROR OCCURRED:")
        print(stack_trace)

        # Send the error to Cloud Logging
        logger.log_struct(
            {
                "message": error_message,
                "stack_trace": stack_trace,
                "file": __file__,
            },
            severity="ERROR",
        )
        print("Error logged to Cloud Logging.")


if __name__ == "__main__":
    main()