import os
import socket
import traceback

from dotenv import load_dotenv
import google.cloud.logging
from google.cloud.logging_v2.resource import Resource

load_dotenv()

# Set up Cloud Logging client (uses GOOGLE_APPLICATION_CREDENTIALS from .env)
client = google.cloud.logging.Client()
logger = client.logger("buggy-app")


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


def _get_db_config():
    """
    Retrieve DB connection parameters from the environment.
    Raises ConfigError if mandatory variables are missing.
    """
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")

    if not db_host:
        raise ConfigError("Environment variable DB_HOST is not set.")
    if not db_port:
        raise ConfigError("Environment variable DB_PORT is not set.")

    try:
        db_port = int(db_port)
    except ValueError as exc:
        raise ConfigError(f"DB_PORT must be an integer, got '{db_port}'.") from exc

    return db_host, db_port


def connect_to_database():
    """
    Establish a TCP connection to the configured database.
    If the connection cannot be made, a clear exception is raised and logged.
    """
    db_host, db_port = _get_db_config()

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

def load_api_config():
    api_key = os.environ["EXTERNAL_API_KEY"]  # deliberately not set anywhere
    return api_key

def main():
    try:
        #connect_to_database()
        load_api_config()
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