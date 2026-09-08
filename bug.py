import socket
import traceback
import os
from dotenv import load_dotenv
import google.cloud.logging
from google.cloud.logging_v2.resource import Resource

# Load variables from a .env file (if present)
load_dotenv()

# Set up Cloud Logging client (uses GOOGLE_APPLICATION_CREDENTIALS from .env)
client = google.cloud.logging.Client()
logger = client.logger("buggy-app")


def connect_to_database():
    """
    Attempt to open a TCP connection to the configured database.
    The host and port are read from environment variables with sensible defaults.
    """
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", "5432"))  # default PostgreSQL port; adjust as needed

    print(f"Connecting to database at {db_host}:{db_port} ...")
    try:
        sock = socket.create_connection((db_host, db_port), timeout=3)
        return sock
    except Exception as conn_err:
        # Log the connection problem and re‑raise so the caller can handle it
        logger.log_struct(
            {
                "message": f"Database connection failed: {conn_err}",
                "file": __file__,
            },
            severity="ERROR",
        )
        raise


def load_api_config():
    """
    Retrieve the external API key from the environment.
    Returns None if the variable is missing and logs a warning,
    allowing the application to continue or handle the missing key gracefully.
    """
    api_key = os.getenv("EXTERNAL_API_KEY")
    if api_key is None:
        warning_msg = "EXTERNAL_API_KEY is not set; proceeding without an API key."
        print(warning_msg)
        logger.log_struct(
            {
                "message": warning_msg,
                "file": __file__,
            },
            severity="WARNING",
        )
    return api_key


def main():
    try:
        #connect_to_database()
        load_api_config()
        print("Application started successfully!")
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