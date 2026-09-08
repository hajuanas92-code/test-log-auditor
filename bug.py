import socket
import traceback
import os
import sys
from dotenv import load_dotenv
import google.cloud.logging

load_dotenv()

# Initialise Cloud Logging client lazily – it may fail in environments without GCP credentials.
try:
    client = google.cloud.logging.Client()
    logger = client.logger("buggy-app")
except Exception:  # pragma: no cover
    logger = None  # Fallback to a no‑op logger if Cloud Logging cannot be initialised.


def _log_struct(message: str, stack_trace: str):
    """Helper that logs to Cloud Logging if the logger is available."""
    if logger:
        logger.log_struct(
            {"message": message, "stack_trace": stack_trace},
            severity="ERROR",
        )
    else:
        # In non‑GCP environments just print the log entry.
        print("[CloudLogging disabled] ERROR:", message)


def connect_to_database() -> socket.socket | None:
    """Attempt to open a TCP connection to the configured DB.

    Returns:
        socket.socket | None: The connected socket, or ``None`` if the
        connection could not be established.

    The function no longer raises an exception; it logs the problem and
    returns ``None`` so callers can decide how to proceed without the
    program crashing.
    """
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", "5999"))
    print(f"Connecting to database at {db_host}:{db_port} ...")

    try:
        sock = socket.create_connection((db_host, db_port), timeout=3)
        return sock
    except (socket.timeout, ConnectionRefusedError, OSError) as exc:
        # Log the low‑level error and return None instead of raising.
        _log_struct(
            f"Unable to connect to database at {db_host}:{db_port}. "
            "Ensure the service is running and reachable.",
            traceback.format_exc(),
        )
        return None


def load_api_config() -> str:
    """Load the external API key from the environment.

    Returns:
        str: The API key.

    Raises:
        EnvironmentError: If the key is missing.
    """
    # Use getenv to avoid a KeyError if the variable is absent.
    api_key = os.getenv("EXTERNAL_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "EXTERNAL_API_KEY environment variable is not set. "
            "Set it before running the application."
        )
    return api_key


def log_error(e: Exception):
    """Log the full traceback to stdout and Cloud Logging (if configured)."""
    stack_trace = traceback.format_exc()
    print("ERROR OCCURRED:")
    print(stack_trace)

    _log_struct(str(e), stack_trace)
    print("Error logged to Cloud Logging (if enabled).")


def main():
    bug_type = sys.argv[1] if len(sys.argv) > 1 else "db"

    if bug_type == "db":
        sock = connect_to_database()
        if sock:
            print("Connected successfully!")
            sock.close()
        else:
            print("Failed to connect to the database; proceeding without a DB connection.")
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