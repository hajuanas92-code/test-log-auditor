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
    Uses sensible defaults (PostgreSQL default port 5432) and raises a
    clear error if the connection cannot be made.
    """
    db_host = os.getenv("DB_HOST", "localhost")
    # Use the standard PostgreSQL port as the safe default
    db_port = int(os.getenv("DB_PORT", "5432"))

    print(f"Connecting to database at {db_host}:{db_port} ...")
    try:
        sock = socket.create_connection((db_host, db_port), timeout=3)
    except Exception as conn_err:
        # Re‑raise with a more descriptive message while preserving the original traceback
        raise ConnectionError(
            f"Failed to connect to database at {db_host}:{db_port}. "
            f"Ensure the service is reachable and the host/port are correct."
        ) from conn_err

    return sock


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