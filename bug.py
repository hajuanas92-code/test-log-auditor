import os
import socket
import traceback

from dotenv import load_dotenv
import google.cloud.logging
from google.cloud.logging_v2.resource import Resource

load_dotenv()

# ----------------------------------------------------------------------
# Cloud Logging client (uses GOOGLE_APPLICATION_CREDENTIALS from .env)
# ----------------------------------------------------------------------
client = google.cloud.logging.Client()
logger = client.logger("buggy-app")


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


def _get_db_config():
    """
    Retrieve DB connection parameters from the environment.
    Provides sensible defaults for local development and raises
    ConfigError only when the values are present but malformed.
    """
    # Default to a typical local PostgreSQL instance – adjust as needed.
    default_host = "127.0.0.1"
    default_port = 5432

    db_host = os.getenv("DB_HOST", default_host)
    db_port = os.getenv("DB_PORT", str(default_port))

    if not db_host:
        raise ConfigError("Environment variable DB_HOST is not set and no default is defined.")
    if not db_port:
        raise ConfigError("Environment variable DB_PORT is not set and no default is defined.")

    try:
        db_port = int(db_port)
    except ValueError as exc:
        raise ConfigError(f"DB_PORT must be an integer, got '{db_port}'.") from exc

    return db_host, db_port


def connect_to_database():
    """
    Establish a TCP connection to the configured database.
    Returns the connected socket or raises a detailed ConnectionError.
    """
    db_host, db_port = _get_db_config()

    print(f"Connecting to database at {db_host}:{db_port} ...")
    try:
        # Attempt the connection with a short timeout.
        sock = socket.create_connection((db_host, db_port), timeout=5)
        return sock
    except socket.timeout as exc:
        raise ConnectionError(
            f"Timed out while trying to connect to {db_host}:{db_port}. "
            "Check network connectivity and firewall rules."
        ) from exc
    except ConnectionRefusedError as exc:
        raise ConnectionError(
            f"Connection refused by {db_host}:{db_port}. "
            "Ensure the database service is running and listening on the specified port."
        ) from exc
    except OSError as exc:
        # Catch any other low‑level socket errors.
        raise ConnectionError(
            f"Failed to connect to {db_host}:{db_port} due to an OS error: {exc}."
        ) from exc


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